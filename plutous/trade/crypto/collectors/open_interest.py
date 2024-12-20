import asyncio
from datetime import datetime, timedelta

from plutous import database as db
from plutous.trade.crypto.models import OpenInterest

from .base import BaseCollector, BaseCollectorConfig

TIMEOUT = timedelta(minutes=2)


class OpenInterestCollectorConfig(BaseCollectorConfig):
    symbol_type: str = "swap"


class OpenInterestCollector(BaseCollector):
    TABLE = OpenInterest

    config: OpenInterestCollectorConfig

    async def _collect(self):
        while True:
            active_symbols = await self.fetch_active_symbols()
            coroutines = [
                self.exchange.fetch_open_interest(symbol) for symbol in active_symbols
            ]
            open_interests: list[dict] = await asyncio.gather(*coroutines)

            if open_interests[0]["timestamp"] < int(
                (datetime.now() - TIMEOUT).timestamp() * 1000
            ):
                raise RuntimeError(
                    f"Data is stale, last updated at {open_interests[0]['timestamp']}"
                )
            with db.Session() as session:
                self._insert(
                    [
                        OpenInterest(
                            symbol=open_interest["symbol"],
                            exchange=self._exchange,
                            timestamp=self.round_milliseconds(
                                open_interest["timestamp"]
                            ),
                            open_interest=open_interest["openInterestAmount"],
                            datetime=self.exchange.iso8601(
                                self.round_milliseconds(open_interest["timestamp"])
                            ),
                        )
                        for open_interest in open_interests
                    ],
                    session,
                )
                session.commit()
            await asyncio.sleep(30)
