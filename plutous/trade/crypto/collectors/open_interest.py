import asyncio

from plutous.trade.crypto.enums import CollectorType
from plutous.trade.crypto.models import OpenInterest

from .base import BaseCollector


class OpenInterestCollector(BaseCollector):
    COLLECTOR_TYPE = CollectorType.OPEN_INTEREST
    TABLE = OpenInterest

    async def fetch_data(self):
        active_symbols = await self.fetch_active_symbols()
        coroutines = [
            self.exchange.fetch_open_interest(symbol) for symbol in active_symbols
        ]
        open_interests = await asyncio.gather(*coroutines)
        return [
            OpenInterest(
                symbol=open_interest["symbol"],
                exchange=self._exchange,
                timestamp=self.round_milliseconds(
                    open_interest["timestamp"], offset=-1
                ),
                open_interest=open_interest["openInterestAmount"],
                datetime=self.exchange.iso8601(
                    self.round_milliseconds(open_interest["timestamp"], offset=-1)
                ),
            )
            for open_interest in open_interests
        ]
