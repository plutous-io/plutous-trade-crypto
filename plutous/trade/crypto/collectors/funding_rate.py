from typing import Any

from plutous.trade.crypto.enums import CollectorType
from plutous.trade.crypto.models import FundingRate

from .base import BaseCollector


class FundingRateCollector(BaseCollector):
    COLLECTOR_TYPE = CollectorType.FUNDING_RATE

    async def fetch_data(self):
        active_symbols = await self.fetch_active_symbols()
        funding_rates: dict[str, dict[str, Any]] = await self.exchange.fetch_funding_rates()  # type: ignore
        return [
            FundingRate(
                symbol=funding_rate["symbol"],
                exchange=self._exchange,
                timestamp=funding_rate["timestamp"] // 60000 * 60000,
                funding_rate=funding_rate["fundingRate"],
                datetime=self.exchange.iso8601(
                    funding_rate["timestamp"] // 60000 * 60000
                ),
            )
            for funding_rate in funding_rates.values()
            if funding_rate["symbol"] in active_symbols
        ]
