from pydantic import BaseModel

from plutous.config import BaseConfig


class CollectorConfig(BaseModel):
    sentry_dsn: str | None = None


class AlertConfig(BaseModel):
    sentry_dsn: str | None = None


class Config(BaseConfig):
    __section__ = "trade/crypto"

    collector: CollectorConfig
    alert: AlertConfig


CONFIG = Config.from_file()
