from plutous.trade.enums import Action, PositionSide, StrategyDirection

from .base import BaseBot, BaseBotConfig


class WebhookBotConfig(BaseBotConfig):
    symbol: str


class WebhookBot(BaseBot):
    config: WebhookBotConfig

    async def _run(
        self,
        action: Action,
        quantity: float | None = None,
    ):
        await self.exchange.load_markets()
        if self.config.symbol in self.positions:
            position = self.positions[self.config.symbol]
            if (
                (position.side == PositionSide.LONG)
                & (action == Action.BUY)
            ) | (
                (position.side == PositionSide.SHORT)
                & (action == Action.SELL)
            ):
                await self.exchange.close()
                return

            await super().close_position(
                symbol=self.config.symbol,
                quantity=quantity,
            )

            if self.bot.strategy.direction != StrategyDirection.BOTH:
                await self.exchange.close()
                return

        await self.open_position(
            symbol=self.config.symbol,
            side=PositionSide.LONG
            if action == Action.BUY
            else PositionSide.SHORT,
            quantity=quantity,
        )
        await self.exchange.close()

    async def close_position(self, quantity: float | None = None):
        await self.exchange.load_markets()
        if self.config.symbol in self.positions:
            await super().close_position(
                symbol=self.config.symbol,
                quantity=quantity,
            )
            await self.exchange.close()
            