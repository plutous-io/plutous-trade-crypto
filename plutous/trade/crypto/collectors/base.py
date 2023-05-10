from abc import ABC, abstractmethod
from typing import Union, Type

from plutous.trade.crypto.exchanges import BinanceUsdm, BinanceCoinm

Exchange = Union[
    BinanceUsdm,
    BinanceCoinm,
]

EXCHANGE_CLS: dict[str, Type[Exchange]] = {
    "binance_usdm": BinanceUsdm,
    "binance_coinm": BinanceCoinm,
}


class BaseCollector(ABC):
    def __init__(self, exchange: str, **kwargs):
        self.exchange = EXCHANGE_CLS[exchange](**kwargs)

    @abstractmethod
    async def collect(self) -> None:
        pass
