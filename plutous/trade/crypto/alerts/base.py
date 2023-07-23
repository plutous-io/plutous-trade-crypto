import json
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Type

import pandas as pd
import requests
import telegram
from pydantic import BaseModel, Field, validator
from sqlalchemy import text

from plutous import database as db
from plutous.enums import Exchange
from plutous.trade.crypto.models import (
    OHLCV,
    Base,
    FundingRate,
    LongShortRatio,
    OpenInterest,
)

TIMEOUT = 60


class BaseAlertConfig(BaseModel):
    frequency: str
    lookback: int
    exchange: Exchange
    whitelist_symbols: list[str] = Field(default_factory=list)
    blacklist_symbols: list[str] = Field(default_factory=list)
    discord_webhooks: dict[str, str] = Field(default_factory=dict)
    discord_mentions: dict[str, list[str]] = Field(default_factory=dict)
    telegram_config: dict[str, dict[str, str]] = Field(default_factory=dict)
    filters: list[str] = Field(default_factory=list)

    @validator(
        "whitelist_symbols",
        "blacklist_symbols",
        "discord_webhooks",
        "discord_mentions",
        "telegram_config",
        "filters",
        pre=True,
    )
    def parse_json(cls, value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return {}
        return value


class BaseAlert(ABC):
    __tables__: list[Type[Base]] = [FundingRate, LongShortRatio, OpenInterest, OHLCV]

    def __init__(self, config: BaseAlertConfig):
        self.config = config
        mins = 60 if config.frequency == "1h" else int(config.frequency[:-1])
        multiplier = mins * 60 * 1000
        since = (
            (int(datetime.utcnow().timestamp() * 1000) // multiplier) - config.lookback
        ) * multiplier
        self.data: dict[str, pd.DataFrame] = {}

        with db.engine.connect() as conn:
            kwargs = {
                "exchange": config.exchange,
                "since": since,
                "frequency": config.frequency,
                "symbols": config.whitelist_symbols,
                "conn": conn,
            }
            blacklists = "'" + "', '".join(config.blacklist_symbols) + "'"
            filters = [text(sql) for sql in config.filters] + [
                text(f"symbol not in ({blacklists})")
            ]
            for table in self.__tables__:
                records = pd.DataFrame()
                start = time.time()
                while len(records) < config.lookback:
                    records = table.query(**kwargs, filters=filters)
                    time.sleep(1)
                    if time.time() - start > 60:
                        raise TimeoutError(
                            f"Querying {table.__tablename__} took longer than {TIMEOUT} seconds."
                        )

                self.data[table.__tablename__] = records

    @abstractmethod
    def run(self):
        pass

    def send_discord_message(self, message: str):
        for tag, webhook in self.config.discord_webhooks.items():
            mention_list = self.config.discord_mentions.get(tag, [])
            mentions = ""
            if mention_list:
                mentions = " ".join(mention_list) + "\n"
            msg = message.replace("{{ mentions }}\n", mentions)
            requests.post(webhook, json={"content": msg})

    def send_telegram_message(self, message: str):
        msg = message.replace("{{ mentions }}\n", "")
        for telegram_config in self.config.telegram_config.values():
            bot = telegram.Bot(token=telegram_config["token"])
            bot.sendMessage(chat_id=telegram_config["chat_id"], text=msg)
