from typing import Type

from plutous.trade.crypto.enums import CollectorType

from .base import BaseCollector
from .funding_rate import FundingRateCollector
from .long_short_ratio import LongShortRatioCollector
from .ohlcv import OHLCVCollector
from .open_interest import OpenInterestCollector

COLLECTORS: dict[CollectorType, Type[BaseCollector]] = {
    CollectorType.FUNDING_RATE: FundingRateCollector,
    CollectorType.LONG_SHORT_RATIO: LongShortRatioCollector,
    CollectorType.OHLCV: OHLCVCollector,
    CollectorType.OPEN_INTEREST: OpenInterestCollector,
}