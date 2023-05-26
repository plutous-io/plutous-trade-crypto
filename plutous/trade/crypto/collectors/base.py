from abc import ABC, abstractmethod
from typing import Any, Union

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

    def __init__(self, exchange: Exchange, **kwargs):
        self._exchange = exchange
        self.exchange: ExchangeType = EXCHANGE_CLS[exchange](**kwargs)

    async def collect(self):
        data = await self.fetch_data()
        with db.Session() as session:
            session.add_all(data)
            session.commit()
        await self.exchange.close()

    async def fetch_active_symbols(self):
        markets: dict[str, dict[str, Any]] = await self.exchange.load_markets()
        return [symbol for symbol, market in markets.items() if market["active"]]

    @abstractmethod
    async def fetch_data(self) -> list[Base]:
        pass
