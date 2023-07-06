import asyncio
import time
from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

import requests
import sentry_sdk
from ccxt.base.errors import OrderNotFound
from pydantic import BaseModel
from sqlalchemy.orm import joinedload

from plutous import database as db
from plutous.trade.crypto import exchanges as ex
from plutous.trade.crypto.enums import OrderType
from plutous.trade.enums import Action, PositionSide, StrategyDirection
from plutous.trade.models import Bot, Position, Trade


class BaseBotConfig(BaseModel):
    bot_id: int
    dry_run: bool = False
    order_timeout: int = 60
    open_position_msg: str | None = None
    close_position_msg: str | None = None


class BaseBot(ABC):
    def __init__(self, config: BaseBotConfig):
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
        self.exchange: ex.Exchange = getattr(ex, bot.exchange.value)(
            dict(apiKey=bot.api_key.key, secret=bot.api_key.secret)
        )

        bot_config = bot.config or {}
        bot_config.update(
            {key: val for key, val in config.__dict__.items() if key not in bot_config}
        )
        config.__dict__.update(bot_config)
        self.config = config

    def run(self, **kwargs):
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
        order_type: OrderType = OrderType.MARKET,
    ):
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
                params={"positionSide": side.value},
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
            f"`price: {price}`",
            f"`quantity: {quantity}`",
        ]
        if self.config.open_position_msg:
            msg.append(self.config.open_position_msg)

        self.send_discord_message("\n".join(msg))

    async def close_position(
        self,
        symbol: str,
        side: PositionSide,
        quantity: Decimal | None = None,
        order_type: OrderType = OrderType.MARKET,
    ):
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
                params={"positionSide": position.side.value},
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

        total_realized_pnl = 0
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

        self.session.commit()

        q = sum([t["amount"] for t in trades])
        p = sum([t["amount"] * t["price"] for t in trades]) / q
        icon = ":white_check_mark:" if total_realized_pnl > 0 else ":x:"

        msg = [
            self.bot.name,
            f"{icon} Closed {side.value} on **{symbol}**",
            f"`price: {p}`",
            f"`quantity: {q}`",
            f"`realized_pnl: {total_realized_pnl}`",
        ]
        if self.config.close_position_msg:
            msg.append(self.config.close_position_msg)
        self.send_discord_message("\n".join(msg))

    async def create_market_order(
        self,
        symbol: str,
        side: Literal["buy", "sell"],
        amount: float,
        params: dict[str, Any] = {},
    ) -> list[dict[str, Any]]:
        await self.exchange.load_markets()
        amount = float(self.exchange.amount_to_precision(symbol, amount))
        order = await self.exchange.create_order(
            symbol=symbol,
            type="market",
            side=side,
            amount=amount,
            params=params,
        )
        await asyncio.sleep(0.5)
        trades = await self.exchange.fetch_my_trades(
            symbol=symbol,
            params={"orderId": order["id"]},
        )
        return trades

    async def create_limit_chasing_order(
        self,
        symbol: str,
        side: Literal["buy", "sell"],
        amount: float,
        params: dict[str, Any] = {},
    ) -> list[dict[str, Any]]:
        await self.exchange.load_markets()
        amount = float(self.exchange.amount_to_precision(symbol, amount))
        filled_amount = 0
        trades = []
        start = time.time()
        while True:
            if time.time() - start > self.config.order_timeout:
                trades.extend(
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

            orderbook = await self.exchange.watch_order_book(symbol)
            price = (
                orderbook["bids"][5][0] if side == "buy" else orderbook["asks"][5][0]
            )
            order = await self.exchange.create_order(
                symbol=symbol,
                type="limit",
                side=side,
                amount=amount - filled_amount,
                price=price,
                params=params,
            )
            await asyncio.sleep(2)
            try:
                await self.exchange.cancel_order(order["id"], symbol)
            except OrderNotFound:
                break
            finally:
                trades += await self.exchange.fetch_my_trades(
                    symbol=symbol,
                    params={"orderId": order["id"]},
                )
                filled_amount += sum([t["amount"] for t in trades])
        return trades
