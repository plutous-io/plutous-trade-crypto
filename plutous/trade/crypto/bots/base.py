import asyncio
import time
from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal, Type

import requests
import sentry_sdk
from ccxt.base.errors import InvalidOrder
from loguru import logger
from pydantic import BaseModel
from sqlalchemy.orm import joinedload

from plutous import database as db
from plutous.trade.crypto import exchanges as ex
from plutous.trade.crypto.enums import OrderType
from plutous.trade.crypto.exchanges.base.errors import OrderNotCancellable
from plutous.trade.enums import Action, PositionSide, StrategyDirection
from plutous.trade.models import Bot, Position, Trade


class BaseBotConfig(BaseModel):
    bot_id: int
    dry_run: bool = False
    order_timeout: int = 60
    http_proxy: str | None = None
    open_position_msg: str | None = None
    close_position_msg: str | None = None
    order_type: OrderType = OrderType.MARKET


class BaseBot(ABC):
    __config_cls__: Type[BaseBotConfig] = BaseBotConfig

    def __init__(self, config: BaseBotConfig):
        logger.info(f"Initializing {self.__class__.__name__}")
        self.session = session = db.Session()
        self.bot = bot = (
            session.query(Bot)
            .options(joinedload(Bot.api_key))
            .options(joinedload(Bot.strategy))
            .filter(Bot.id == config.bot_id)
            .one()
        )
        if bot.sentry_dsn:
            sentry_sdk.init(bot.sentry_dsn)

        positions = (
            session.query(Position)
            .filter(
                Position.bot_id == bot.id,
                Position.closed_at == None,
            )
            .all()
        )
        self.positions = {(p.symbol, p.side): p for p in positions}

        bot_config = bot.config or {}
        bot_config.update(
            {key: val for key, val in config.__dict__.items() if key not in bot_config}
        )
        self.config = self.__config_cls__(**bot_config)
        logger.info(f"Bot config: {self.config}")

        kwargs = {}
        if not self.config.dry_run:
            kwargs.update({"apiKey": bot.api_key.key, "secret": bot.api_key.secret})
            if bot.api_key.passphrase:
                kwargs["passphrase"] = bot.api_key.passphrase
            if bot.api_key.user_token:
                kwargs["userToken"] = bot.api_key.user_token
        if self.config.http_proxy:
            kwargs["http_proxy"] = self.config.http_proxy
        self.exchange: ex.Exchange = getattr(ex, bot.exchange.value)(kwargs)

    def run(self, **kwargs):
        logger.info(f"Running {self.__class__.__name__}")
        asyncio.run(self._run(**kwargs))
        self.session.close()

    @abstractmethod
    async def _run(self, **kwargs):
        pass

    def send_discord_message(self, message: str):
        for webhook in self.bot.discord_webhooks:
            requests.post(webhook, json={"content": message})

    async def open_position(
        self,
        symbol: str,
        side: PositionSide,
        quantity: Decimal | None = None,
        order_type: OrderType | None = None,
        params: dict[str, Any] | None = None,
    ):
        if order_type is None:
            order_type = self.config.order_type
        if params is None:
            params = {}
        if self.bot.max_position == len(self.positions):
            return

        action = Action.BUY if side == PositionSide.LONG else Action.SELL
        ticker = await self.exchange.fetch_ticker(symbol)
        price: Decimal = Decimal(str(ticker["last"]))

        if quantity is None:
            position_size = sum(
                [
                    p.price * p.quantity * (1 if k[1] == PositionSide.LONG else -1)
                    for k, p in self.positions.items()
                ]
            ) * (1 if side == PositionSide.LONG else -1)
            amount = abs(
                self.bot.allocated_capital
                * (-1 if self.bot.strategy.direction == StrategyDirection.SHORT else 1)
                - position_size
            ) / (self.bot.max_position - len(self.positions))
            quantity = amount / price

        if not self.config.dry_run:
            create_order = getattr(self, f"create_{order_type.value}_order")
            trades: list[dict[str, Any]] = await create_order(
                symbol=symbol,
                side=action.value,
                amount=float(quantity),
                params=params,
            )
        else:
            trades = [
                {
                    "datetime": datetime.utcnow(),
                    "price": float(price),
                    "amount": float(quantity),
                    "id": "dry_run",
                }
            ]

        if not trades:
            logger.info("No trades executed, position not opened")
            return

        side = PositionSide.LONG if action == Action.BUY else PositionSide.SHORT
        position = self.positions.get((symbol, side))
        if position is None:
            position = Position(
                bot_id=self.bot.id,
                asset_type=self.bot.strategy.asset_type,
                exchange=self.bot.exchange,
                symbol=symbol,
                side=side,
                price=Decimal("0"),
                quantity=Decimal("0"),
                realized_pnl=Decimal("0"),
                opened_at=trades[0]["datetime"],
            )
            self.positions[(symbol, side)] = position

        _trades = []
        for t in trades:
            trade = Trade(
                exchange=self.bot.exchange,
                asset_type=self.bot.strategy.asset_type,
                symbol=symbol,
                action=action,
                side=side,
                quantity=Decimal(str(t["amount"])),
                price=Decimal(str(t["price"])),
                identifier=t["id"],
                realized_pnl=Decimal("0"),
                datetime=t["datetime"],
                position=position,
            )
            _trades.append(trade)
            position.price = (
                (position.price * position.quantity) + (trade.price * trade.quantity)
            ) / (position.quantity + trade.quantity)
            position.quantity += trade.quantity

        self.session.add_all(_trades)
        self.session.commit()

        circle = ":red_circle:" if side == PositionSide.SHORT else ":green_circle:"

        msg = [
            self.bot.name,
            f"{circle} Opened {side.value} on **{symbol}**",
            f"`price: {position.price}`",
            f"`quantity: {position.quantity}`",
        ]
        if self.config.open_position_msg:
            msg.append(self.config.open_position_msg)

        self.send_discord_message("\n".join(msg))
        logger.info("\n".join(msg))

    async def close_position(
        self,
        symbol: str,
        side: PositionSide,
        quantity: Decimal | None = None,
        order_type: OrderType | None = None,
        params: dict[str, Any] | None = None,
    ):
        if order_type is None:
            order_type = self.config.order_type
        if params is None:
            params = {}
        position = self.positions.get((symbol, side))
        if position is None:
            return

        action = Action.SELL if position.side == PositionSide.LONG else Action.BUY
        quantity = min(quantity or position.quantity, position.quantity)

        if not self.config.dry_run:
            create_order = getattr(self, f"create_{order_type.value}_order")
            trades = await create_order(
                symbol=symbol,
                side=action.value,
                amount=float(quantity),
                params=params,
            )
        else:
            ticker: dict[str, Any] = await self.exchange.fetch_ticker(symbol)  # type: ignore
            price = Decimal(str(ticker["last"]))
            realized_pnl = (price * quantity - position.price * quantity) * (
                1 if position.side == PositionSide.LONG else -1
            )
            trades = [
                {
                    "datetime": datetime.utcnow(),
                    "price": float(price),
                    "amount": float(quantity),
                    "id": "dry_run",
                }
            ]

        if not trades:
            logger.info("No trades executed, position not closed")
            return

        total_realized_pnl = 0
        pre_allocated_capital = self.bot.allocated_capital
        for t in trades:
            price = Decimal(str(t["price"]))
            quantity = Decimal(str(t["amount"]))
            realized_pnl = (
                (price - position.price)
                * quantity
                * (1 if position.side == PositionSide.LONG else -1)
            )
            total_realized_pnl += realized_pnl
            trade = Trade(
                exchange=self.bot.exchange,
                asset_type=self.bot.strategy.asset_type,
                position=position,
                side=position.side,
                symbol=symbol,
                action=action,
                quantity=quantity,
                price=price,
                identifier=t["id"],
                realized_pnl=realized_pnl,
                datetime=t["datetime"],
            )
            self.session.add(trade)

            position.quantity -= quantity
            position.realized_pnl += realized_pnl

            if position.quantity == 0:
                position.closed_at = trade.datetime

            if self.bot.accumulate:
                self.bot.allocated_capital += realized_pnl

        if position.closed_at is not None:
            del self.positions[(symbol, side)]

        self.session.commit()

        q = sum([t["amount"] for t in trades])
        p = sum([t["amount"] * t["price"] for t in trades]) / q
        icon = ":white_check_mark:" if total_realized_pnl > 0 else ":x:"

        accumulated_realized_pnl = sum(
            [b.realized_pnl for b in self.bot.positions if b.realized_pnl is not None]
        )

        msg = [
            self.bot.name,
            f"{icon} Closed {side.value} on **{symbol}**",
            f"`price: {p}`",
            f"`quantity: {q}`",
            f"`realized_pnl: {total_realized_pnl}`",
            f"`realized_pnl(%): {total_realized_pnl / pre_allocated_capital * 100}`",
            f"`accumulated_realized_pnl: {accumulated_realized_pnl}`",
            f"`accumulated_realized_pnl(%): {accumulated_realized_pnl / self.bot.initial_capital * 100}`",
        ]
        if self.config.close_position_msg:
            msg.append(self.config.close_position_msg)
        self.send_discord_message("\n".join(msg))
        logger.info("\n".join(msg))

    async def create_market_order(
        self,
        symbol: str,
        side: Literal["buy", "sell"],
        amount: float,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        if params is None:
            params = {}
        await self.exchange.load_markets()
        order = await self.exchange.create_order(
            symbol=symbol,
            type="market",
            side=side,
            amount=amount,
            params=params,
        )
        await asyncio.sleep(0.5)
        trades: list[dict[str, Any]] = await self.exchange.fetch_order_trades(
            order["id"], symbol=symbol
        )
        traded_amount = sum([t["amount"] for t in trades])
        price = sum([t["price"] * t["amount"] for t in trades]) / traded_amount
        logger.info(
            f"""
            Market Order created sucessfully
            Symbol: {symbol}
            Traded amount: {traded_amount}
            Traded price: {price}
            """
        )
        return trades

    async def create_limit_chasing_order(
        self,
        symbol: str,
        side: Literal["buy", "sell"],
        amount: float,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        if params is None:
            params = {}
        price_offset: int = params.pop("price_offset", 3)
        order_lifetime: int = params.pop("order_lifetime", 2)

        logger.info(f"Creating limit chasing order for {symbol}")
        await self.exchange.load_markets()
        market = self.exchange.market(symbol)
        amount = float(self.exchange.amount_to_precision(symbol, amount))
        filled_amount = 0
        filled_trades = []
        start = time.time()
        while filled_amount < amount:
            if time.time() - start > self.config.order_timeout:
                logger.info("Order timed out, creating market order")
                filled_trades.extend(
                    (
                        await self.create_market_order(
                            symbol,
                            side,
                            amount - filled_amount,
                            params,
                        )
                    )
                )
                break

            ob = await self.exchange.watch_order_book(symbol)
            price_precision = market["precision"]["price"]
            price = (
                ob["asks"][0][0] - (price_offset * price_precision)
                if side == "buy"
                else ob["bids"][0][0] + (price_offset * price_precision)
            )
            amount_to_fill = amount - filled_amount
            try:
                self.exchange.amount_to_precision(symbol, amount_to_fill)
            except InvalidOrder:
                logger.info("Amount to precision failed, stopping limit chasing")
                break
            logger.info(
                f"Creating limit chasing order at price: {price}, amount: {amount_to_fill}"
            )
            try:
                order: dict[str, Any] = await self.exchange.create_order(
                    symbol=symbol,
                    type="limit",
                    side=side,
                    amount=amount_to_fill,
                    price=price,
                    params=params,
                )
            except InvalidOrder as e:
                logger.error(f"Invalid order: {e}")
                break
            await asyncio.sleep(order_lifetime)
            try:
                await self.exchange.cancel_order(order["id"], symbol)
                logger.info(f"Limit Chasing Order cancelled: {order['id']}")
            except OrderNotCancellable as e:
                logger.info(f"Order not cancellable: {order['id']}: {e}")

            trades: list[dict[str, Any]] = await self.exchange.fetch_order_trades(
                order["id"], symbol=symbol
            )
            traded_amount = sum([t["amount"] for t in trades])
            filled_trades.extend(trades)
            filled_amount += traded_amount
            if traded_amount:
                logger.info(
                    f"""
                    Limit Chasing Order created sucessfully
                    Symbol: {symbol}
                    Traded amount: {traded_amount}
                    Traded price: {price}
                    Filled amount: {filled_amount}
                    Filled percentage: {filled_amount / amount}
                    """
                )
        return filled_trades
