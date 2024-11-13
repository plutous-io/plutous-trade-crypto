from enum import Enum

from plutous.trade.crypto.exchanges import (
    Binance,
    BinanceCoinm,
    BinanceUsdm,
    Bitget,
    Bybit,
    GateIO,
    Huobi,
    Hyperliquid,
    Kucoin,
    KucoinFutures,
    LBank,
    Mexc,
    Okx,
    Phemex,
    Woo,
)


class Exchange(Enum):
    BINANCE = Binance
    BINANCE_COINM = BinanceCoinm
    BINANCE_USDM = BinanceUsdm
    BITGET = Bitget
    BYBIT = Bybit
    GATEIO = GateIO
    HUOBI = Huobi
    HYPERLIQUID = Hyperliquid
    KUCOIN = Kucoin
    KUCOIN_FUTURES = KucoinFutures
    OKX = Okx
    PHEMEX = Phemex
    WOO = Woo
    MEXC = Mexc
    LBANK = LBank
