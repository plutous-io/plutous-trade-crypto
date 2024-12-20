import asyncio
import json
from abc import ABC, abstractmethod
from typing import Any, Type

import sentry_sdk
from loguru import logger
from pydantic import BaseModel, field_validator
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from plutous.enums import Exchange
from plutous.trade.crypto import exchanges as ex
from plutous.trade.crypto.config import CONFIG
from plutous.trade.crypto.models import Base, Table


class BaseCollectorConfig(BaseModel):
    exchange: Exchange
    symbols: list[str] | None = None
    symbol_type: str = "spot"
    rate_limit: int | None = None
    sentry_dsn: str | None = CONFIG.collector.sentry_dsn

    @field_validator("symbols", mode="before")
    def parse_json(cls, value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return {}
        return value


class BaseCollector(ABC):
    TABLE: Type[Base]

    def __init__(self, config: BaseCollectorConfig):
        self._exchange = config.exchange
        params = {}
        if config.rate_limit:
            params["rateLimit"] = config.rate_limit
        self.exchange: ex.Exchange = getattr(ex, config.exchange.value)(params)
        self.symbols = config.symbols
        self.config = config

        if config.sentry_dsn:
            sentry_sdk.init(config.sentry_dsn)

    def collect(self):
        logger.info(f"Starting {self.__class__.__name__}")
        asyncio.run(self._collect())

    @abstractmethod
    async def _collect(self): ...

    async def fetch_active_symbols(self) -> list[str]:
        if self.symbols:
            return self.symbols
        markets: dict[str, dict[str, Any]] = await self.exchange.load_markets(
            reload=True
        )
        return [
            symbol
            for symbol, market in markets.items()
            if market["active"] and (market["type"] == self.config.symbol_type)
        ]

    def _insert(
        self,
        data: list[Table],
        session: Session,
        table: Type[Table] | None = None,
    ):
        if not data:
            return
        if table is None:
            table = self.TABLE
        logger.info(f"Inserting {len(data)} records into {table.__name__}")
        stmt = insert(table).values([d.dict() for d in data])
        stmt = stmt.on_conflict_do_nothing(
            index_elements=[
                "exchange",
                "symbol",
                "timestamp",
            ],
        )
        session.execute(stmt)

    def _upsert(
        self,
        data: list[Table],
        session: Session,
        table: Type[Table] | None = None,
        update_fields: list[str] | None = None,
    ):
        if not data:
            return
        if table is None:
            table = self.TABLE
        logger.info(f"Upserting {len(data)} records into {table.__name__}")
        stmt = insert(table).values([d.dict() for d in data])
        index_elements = ["exchange", "symbol", "timestamp"]
        to_update = set(update_fields or list(data[0].dict().keys())) - set(
            index_elements
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=index_elements,
            set_={k: getattr(stmt.excluded, k) for k in to_update},
        )
        session.execute(stmt)

    def round_milliseconds(
        self,
        timestamp: int,
        multiplier: int = 60 * 1000,
        offset: int = 0,
    ) -> int:
        return ((timestamp // multiplier) + offset) * multiplier
