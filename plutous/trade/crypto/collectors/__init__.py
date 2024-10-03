from typing import Type

from plutous.trade.crypto.enums import CollectorType

from .base import BaseCollector, BaseCollectorConfig
from .funding_rate import FundingRateCollector, FundingRateCollectorConfig
from .long_short_ratio import LongShortRatioCollector, LongShortRatioCollectorConfig
from .ohlcv import OHLCVCollector, OHLCVCollectorConfig
from .open_interest import OpenInterestCollector, OpenInterestCollectorConfig
from .orderbook import OrderbookCollector, OrderbookCollectorConfig
from .taker_buy_sell import TakerBuySellCollector, TakerBuySellCollectorConfig

COLLECTORS: dict[CollectorType, Type[BaseCollector]] = {
    CollectorType.FUNDING_RATE: FundingRateCollector,
    CollectorType.LONG_SHORT_RATIO: LongShortRatioCollector,
    CollectorType.OHLCV: OHLCVCollector,
    CollectorType.OPEN_INTEREST: OpenInterestCollector,
    CollectorType.ORDERBOOK: OrderbookCollector,
    CollectorType.TAKER_BUY_SELL: TakerBuySellCollector,
}
