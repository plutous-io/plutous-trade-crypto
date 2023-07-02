from abc import ABC, abstractmethod
from typing import Any, Type, Union
from datetime import datetime, timedelta

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from plutous import database as db
from plutous.enums import Exchange
from plutous.trade.crypto.enums import CollectorType
from plutous.trade.crypto.exchanges import BinanceCoinm, BinanceUsdm
from plutous.trade.crypto.models import Base

EXCHANGE_CLS = {
    Exchange.BINANCE_USDM: BinanceUsdm,
    Exchange.BINANCE_COINM: BinanceCoinm,
}

ExchangeType = Union[BinanceUsdm, BinanceCoinm]


class BaseCollector(ABC):
    COLLECTOR_TYPE: CollectorType
    TABLE: Type[Base]

    def __init__(self, exchange: Exchange):
        self._exchange = exchange
        self.exchange: ExchangeType = EXCHANGE_CLS[exchange]({"rateLimit": False})

    async def collect(self):
        data = await self.fetch_data()
        with db.Session() as session:
            self._insert(data, session)
            session.commit()
        await self.exchange.close()

    async def backfill(
        self,
        since: datetime,
        duration: timedelta | None = None,
        missing_only: bool = False,
    ):
        start_time = int(since.timestamp()) * 1000
        end_time = None
        if duration:
            end_time = self.round_milliseconds(
                start_time, offset=int(duration / timedelta(minutes=5))
            )

        data = await self.backfill_data(start_time, end_time, missing_only)
        with db.Session() as session:
            self._insert(data, session)
            session.commit()
        await self.exchange.close()

    async def fetch_active_symbols(self):
        markets: dict[str, dict[str, Any]] = await self.exchange.load_markets()
        return [symbol for symbol, market in markets.items() if market["active"]]

    @abstractmethod
    async def fetch_data(self) -> list[Base]:
        pass

    @abstractmethod
    async def backfill_data(
        self,
        start_time: int,
        end_time: int | None = None,
        missing_only: bool = False,
    ) -> list[Base]:
        pass

    def _insert(
        self,
        data: list[Base],
        session: Session,
        table: Type[Base] | None = None,
    ):
        if not data:
            return
        if table is None:
            table = self.TABLE
        stmt = insert(table).values([d.dict() for d in data])
        stmt = stmt.on_conflict_do_nothing(
            index_elements=[
                "exchange",
                "symbol",
                "timestamp",
            ],
        )
        session.execute(stmt)

    def round_milliseconds(
        self,
        timestamp: int,
        multipler: int = 300000,
        offset: int = 0,
    ) -> int:
        return ((timestamp // multipler) + offset) * multipler
