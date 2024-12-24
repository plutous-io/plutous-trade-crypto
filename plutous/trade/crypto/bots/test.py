from .base import BaseBot, BaseBotConfig


class TestBotConfig(BaseBotConfig):
    pass


class TestBot(BaseBot):
    config: TestBotConfig

    async def _run(self):
        pass
