from .base import Base
from .bid_ask_sum import BidAskSum
from .funding_rate import FundingRate
from .funding_settlement import FundingSettlement
from .long_short_ratio import LongShortRatio
from .ohlcv import OHLCV, OHLCV1h
from .open_interest import OpenInterest
from .orderbook import Orderbook
from .taker_buy_sell import TakerBuySell

Table = (
    Base
    | BidAskSum
    | FundingRate
    | FundingSettlement
    | LongShortRatio
    | OHLCV
    | OHLCV1h
    | OpenInterest
    | Orderbook
    | TakerBuySell
)
