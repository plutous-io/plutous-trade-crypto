from typing import Union

from .binance import Binance, BinanceCoinm, BinanceUsdm
from .bitget import Bitget
from .bybit import Bybit
from .coinex import CoinEx
from .gateio import GateIO
from .huobi import Huobi
from .kucoin import Kucoin, KucoinFutures
from .mexc import Mexc
from .okx import Okx
from .phemex import Phemex
from .upbit import Upbit
from .woo import Woo

Exchange = Union[
    Binance,
    BinanceCoinm,
    BinanceUsdm,
    Bitget,
    Bybit,
    CoinEx,
    GateIO,
    Huobi,
    Kucoin,
    KucoinFutures,
    Mexc,
    Okx,
    Phemex,
    Upbit,
    Woo,
]
