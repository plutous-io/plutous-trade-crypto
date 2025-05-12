import requests
from loguru import logger

from .base import BaseBot, BaseBotConfig


class LiquidationAlertBotConfig(BaseBotConfig):
    webhook: str = "https://test.com"
    type: str = "spot"
    upper: float = 1000
    lower: float = 1000


class LiquidationAlertBot(BaseBot):
    __config_cls__ = LiquidationAlertBotConfig
    config: LiquidationAlertBotConfig

    async def _run(self, **kwargs):
        resp = await self.exchange.fetch_balance(params={"type": self.config.type})
        usdt_balance = [
            data for data in resp["info"]["data"] if data["currency"] == "USDT"
        ][0]
        equity = usdt_balance["equity"]
        logger.info(f"USDT balance: {equity}")
        if usdt_balance["equity"] > self.config.upper:
            logger.info(f"USDT balance is above upper limit {self.config.upper}")
            requests.get(self.config.webhook)

        if usdt_balance["equity"] < self.config.lower:
            logger.info(f"USDT balance is below lower limit {self.config.lower}")
            requests.get(self.config.webhook)

        await self.exchange.close()
