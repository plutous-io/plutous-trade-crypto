from plutous.trade.enums import Action, PositionSide, StrategyDirection

from .base import BaseBot, BaseBotConfig


class WebhookBotConfig(BaseBotConfig):
    symbol: str
    action: Action
    quantity: float | None = None


class WebhookBot(BaseBot):
    config: WebhookBotConfig
    
    async def _run(self):
        await self.exchange.load_markets()
        if self.config.symbol in self.positions:
            position = self.positions[self.config.symbol]
            if ((position.side == PositionSide.LONG) & (self.config.action == Action.BUY)) | (
                (position.side == PositionSide.SHORT) & (self.config.action == Action.SELL)
            ):
                await self.exchange.close()
                return

            await self.close_position(
                symbol=self.config.symbol,
                quantity=self.config.quantity,
            )

            if self.bot.strategy.direction != StrategyDirection.BOTH:
                await self.exchange.close()
                return

        await self.open_position(
            symbol=self.config.symbol,
            side=PositionSide.LONG
            if self.config.action == Action.BUY
            else PositionSide.SHORT,
            quantity=self.config.quantity,
        )
        await self.exchange.close()
