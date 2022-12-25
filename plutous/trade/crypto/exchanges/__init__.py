from typing import Union

from .binance import Binance, BinanceCoinm, BinanceUsdm
from .bitget import Bitget
from .bybit import Bybit
from .gateio import GateIO
from .huobi import Huobi
from .kucoin import Kucoin, KucoinFutures
from .mexc import Mexc
from .okx import Okx
from .phemex import Phemex

Exchange = Union[
    Binance,
    BinanceCoinm,
    BinanceUsdm,
    Bitget,
    Bybit,
    GateIO,
    Huobi,
    Kucoin,
    KucoinFutures,
    Mexc,
    Okx,
    Phemex,
]
