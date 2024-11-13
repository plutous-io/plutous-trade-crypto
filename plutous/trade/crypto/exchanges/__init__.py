from typing import Union

from .binance import Binance, BinanceCoinm, BinanceUsdm
from .bitget import Bitget
from .bybit import Bybit
from .coinbase import Coinbase
from .coinex import CoinEx
from .gateio import GateIO
from .huobi import Huobi
from .hyperliquid import Hyperliquid
from .kucoin import Kucoin, KucoinFutures
from .lbank import LBank
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
    Coinbase,
    CoinEx,
    GateIO,
    Huobi,
    Hyperliquid,
    Kucoin,
    KucoinFutures,
    LBank,
    Mexc,
    Okx,
    Phemex,
    Upbit,
    Woo,
    Mexc,
]
