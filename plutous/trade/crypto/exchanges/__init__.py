from typing import Union

from .binance import Binance, BinanceCoinm, BinanceUsdm
from .bitget import Bitget
from .bitmex import Bitmex
from .bybit import Bybit
from .coinbase import Coinbase
from .coinex import CoinEx
from .deribit import Deribit
from .gateio import GateIO
from .gemini import Gemini
from .huobi import Huobi
from .hyperliquid import Hyperliquid
from .kraken import Kraken
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
    Bitmex,
    Bybit,
    Coinbase,
    CoinEx,
    Deribit,
    GateIO,
    Gemini,
    Huobi,
    Hyperliquid,
    Kraken,
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
