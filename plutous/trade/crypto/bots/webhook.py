from plutous.trade.enums import Action, PositionSide

from .base import BaseBot, BaseBotConfig


class WebhookBotConfig(BaseBotConfig):
    symbol: str


class WebhookBot(BaseBot):
    config: WebhookBotConfig

    async def _run(
        self,
        action: Action,
        quantity: float,
        prev_position_side: PositionSide,
        prev_position_size: float,
    ):
        await self.exchange.load_markets()
        if ((prev_position_side == PositionSide.LONG) & (action == Action.SELL)) | (
            (prev_position_side == PositionSide.SHORT) & (action == Action.BUY)
        ):
            close_quantity = quantity
            if quantity >= prev_position_size:
                close_quantity = None
            
            await super().close_position(
                symbol=self.config.symbol,
                side=prev_position_side,
                quantity=close_quantity,
            )

            quantity -= prev_position_size

        if quantity > 0:
            await self.open_position(
                symbol=self.config.symbol,
                side=PositionSide.LONG if action == Action.BUY else PositionSide.SHORT,
                quantity=quantity,
            )
        await self.exchange.close()

    async def close_position(
        self,
        side: PositionSide,
        quantity: float | None = None,
    ):
        await self.exchange.load_markets()
        if (self.config.symbol, side) in self.positions:
            await super().close_position(
                symbol=self.config.symbol,
                side=side,
                quantity=quantity,
            )
        await self.exchange.close()
