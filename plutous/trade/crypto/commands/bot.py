from datetime import datetime
from typing import Any

from pydantic import BaseModel
from sqlalchemy.orm import Session

from plutous.trade.crypto import exchanges as ex
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
            if ((position.side == PositionSide.LONG) & (self.action == Action.BUY)) | (
                (position.side == PositionSide.SHORT) & (self.action == Action.SELL)
            ):
                await exchange.close()
                return

            quantity = self.quantity or position.quantity

            order: dict[str, Any] = await exchange.create_order(
                symbol=self.symbol,
                type="market",
                side=self.action.value,
                amount=quantity,
                params={"positionSide": position.side.value},
            )  # type: ignore
            t: dict[str, Any] = (
                await exchange.fetch_my_trades(
                    symbol=self.symbol,
                    params={"orderId": order["id"]},
                )
            )[0]
            realized_pnl = float(t["info"]["realizedPnl"])

            trade = Trade(
                exchange=bot.exchange,
                asset_type=bot.strategy.asset_type,
                position_id=position.id,
                side=position.side,
                symbol=self.symbol,
                action=self.action,
                quantity=t["amount"],
                price=t["price"],
                identifier=t["id"],
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
                await exchange.close()
                return

        side = PositionSide.LONG if self.action == Action.BUY else PositionSide.SHORT
        ticker = await exchange.fetch_ticker(self.symbol)
        quantity = self.quantity or bot.allocated_capital / ticker["last"]
        order: dict[str, Any] = await exchange.create_order(
            symbol=self.symbol,
            type="market",
            side=self.action.value,
            amount=quantity,
            params={"positionSide": side.value},
        )  # type: ignore
        t: dict[str, Any] = (
            await exchange.fetch_my_trades(
                symbol=self.symbol,
                params={"orderId": order["id"]},
            )  # type: ignore
        )[0]

        position = Position(
            bot_id=self.bot_id,
            asset_type=bot.strategy.asset_type,
            exchange=bot.exchange,
            symbol=self.symbol,
            side=side,
            quantity=t["amount"],
            opened_at=t["datetime"],
            trades=[
                Trade(
                    exchange=bot.exchange,
                    asset_type=bot.strategy.asset_type,
                    symbol=self.symbol,
                    action=self.action,
                    side=side,
                    quantity=t["amount"],
                    price=t["price"],
                    identifier=t["id"],
                    realized_pnl=0,
                    datetime=t["datetime"],
                )
            ],
        )

        session.add(position)
        session.commit()
        await exchange.close()
