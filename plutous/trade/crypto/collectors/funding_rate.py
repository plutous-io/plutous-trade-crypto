from typing import Any

from plutous.trade.crypto.enums import CollectorType
from plutous.trade.crypto.models import FundingRate

from .base import BaseCollector


class FundingRateCollector(BaseCollector):
    COLLECTOR_TYPE = CollectorType.FUNDING_RATE
    TABLE = FundingRate

    async def fetch_data(self):
        active_symbols = await self.fetch_active_symbols()
        funding_rates: dict[str, dict[str, Any]] = await self.exchange.fetch_funding_rates()  # type: ignore
        return [
            FundingRate(
                symbol=funding_rate["symbol"],
                exchange=self._exchange,
                timestamp=self.round_milliseconds(funding_rate["timestamp"], offset=-1),
                funding_rate=funding_rate["fundingRate"] * 100,
                datetime=self.exchange.iso8601(
                    self.round_milliseconds(funding_rate["timestamp"], offset=-1)
                ),
            )
            for funding_rate in funding_rates.values()
            if funding_rate["symbol"] in active_symbols
        ]
