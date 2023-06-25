import json
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Type

import pandas as pd
import requests
import telegram
from pydantic import BaseModel
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
    whitelist_symbols: list[str] = []
    blacklist_symbols: list[str] = []
    discord_webhooks: list[str] | str = []
    telegram_config: list[dict[str, str]] | str = []
    filters: list[str] | str = []

    def __init__(self, **data):
        super().__init__(**data)
        if isinstance(self.whitelist_symbols, str):
            self.whitelist_symbols = json.loads(self.whitelist_symbols)
        if isinstance(self.blacklist_symbols, str):
            self.blacklist_symbols = json.loads(self.blacklist_symbols)
        if isinstance(self.discord_webhooks, str):
            self.discord_webhooks = json.loads(self.discord_webhooks)
        if isinstance(self.telegram_config, str):
            self.telegram_config = json.loads(self.telegram_config)
        if isinstance(self.filters, str):
            self.filters = json.loads(self.filters)


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
        for webhook in self.config.discord_webhooks:
            requests.post(webhook, json={"content": message})

    def send_telegram_message(self, message: str):
        for telegram_config in self.config.telegram_config:
            bot = telegram.Bot(token=telegram_config["token"])
            bot.sendMessage(chat_id=telegram_config["chat_id"], text=message)
