from plutous.config import BaseConfig


class Config(BaseConfig):
    __section__ = "trade/crypto"

    sentry_dsn: str | None = None


config = Config.from_file()
