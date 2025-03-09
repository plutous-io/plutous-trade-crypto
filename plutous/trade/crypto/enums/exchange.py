from enum import Enum

from plutous.trade.crypto.exchanges import (
    Binance,
    BinanceCoinm,
    BinanceUsdm,
    Bitget,
    Bitmex,
    Bitunix,
    Bybit,
    Coinbase,
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
    Woo,
)


class Exchange(Enum):
    BINANCE = Binance
    BINANCE_COINM = BinanceCoinm
    BINANCE_USDM = BinanceUsdm
    BITGET = Bitget
    BYBIT = Bybit
    BITMEX = Bitmex
    BITUNIX = Bitunix
    COINBASE = Coinbase
    DERIBIT = Deribit
    GATEIO = GateIO
    GEMINI = Gemini
    HUOBI = Huobi
    HYPERLIQUID = Hyperliquid
    KRAKEN = Kraken
    KUCOIN = Kucoin
    KUCOIN_FUTURES = KucoinFutures
    OKX = Okx
    PHEMEX = Phemex
    WOO = Woo
    MEXC = Mexc
    LBANK = LBank
