from datetime import datetime
from typing import Any

from pydantic import BaseModel
from sqlalchemy.orm import Session

from plutous.trade.crypto import exchanges as ex
from plutous.trade.crypto.enums import OrderType
from plutous.trade.enums import Action, PositionSide, StrategyDirection
from plutous.trade.models import Bot, Position, Trade


class WebhookBotCreateOrder(BaseModel):
    bot_id: int
    symbol: str
    action: Action
    quantity: float | None = None

    async def execute(self, session: Session):
        bot = session.query(Bot).filter_by(id=self.bot_id).one()
        position = (
            session.query(Position)
            .filter(
                Position.bot_id == self.bot_id,
                Position.closed_at == None,
                Position.symbol == self.symbol,
            )
            .one_or_none()
        )

        exchange: ex.Exchange = getattr(ex, bot.exchange.value)(
            {
                "apiKey": bot.api_key.key,
                "secret": bot.api_key.secret,
            }
        )
        if position is not None:
            if (position.side == PositionSide.LONG) & (self.action == Action.BUY):
                return
            if (position.side == PositionSide.SHORT) & (self.action == Action.SELL):
                return

            quantity = self.quantity or position.quantity

            order: dict[str, Any] = await exchange.create_order(
                symbol=self.symbol,
                type="market",
                side=self.action.value,
                amount=quantity,
                params={"positionSide": position.side.value},
            )  # type: ignore
            t: dict[str, Any] = await exchange.fetch_my_trades(
                symbol=self.symbol,
                params={"orderId": order["id"]},
            )
            realized_pnl = float(t["info"]["realizedPnl"])

            trade = Trade(
                bot_id=self.bot_id,
                position_id=position.id,
                symbol=self.symbol,
                action=self.action,
                quantity=t["amount"],
                price=t["price"],
                identifier=t["id"],
                order_type=OrderType.MARKET,
                realized_pnl=realized_pnl,
                datetime=t["datetime"],
            )
            session.add(trade)

            position.quantity -= quantity
            if position.quantity == 0:
                position.closed_at = trade.datetime

            if bot.accumulate:
                bot.allocated_capital += realized_pnl

            session.commit()

            if bot.strategy.direction != StrategyDirection.BOTH:
                return

        side = PositionSide.LONG if self.action == Action.BUY else PositionSide.SHORT
        ticker = await exchange.fetch_ticker(self.symbol)
        quantity = self.quantity or bot.allocated_capital / ticker["last"]
        order: dict[str, Any] = await exchange.create_order(
            symbol=self.symbol,
            type="market",
            side=self.action.value,
            amount=quantity,
            params={"position_side": side.value},
        )  # type: ignore
        t: dict[str, Any] = await exchange.fetch_my_trades(
            symbol=self.symbol,
            params={"orderId": order["id"]},
        )  # type: ignore

        position = Position(
            bot_id=self.bot_id,
            asset_type=bot.strategy.asset_type,
            exchaneg=bot.exchange,
            symbol=self.symbol,
            side=side,
            quantity=t["amount"],
            opened_at=t["datetime"],
            trades=[
                Trade(
                    bot_id=self.bot_id,
                    position=position,
                    symbol=self.symbol,
                    action=self.action,
                    quantity=t["amount"],
                    price=t["price"],
                    identifier=t["id"],
                    order_type=OrderType.MARKET,
                    realized_pnl=0,
                    datetime=t["datetime"],
                )
            ],
        )

        session.add(position)
        session.commit()
