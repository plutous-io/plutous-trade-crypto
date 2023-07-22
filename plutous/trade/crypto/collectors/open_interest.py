import asyncio
from datetime import datetime, timedelta

from plutous.trade.crypto.enums import CollectorType
from plutous.trade.crypto.models import OpenInterest

from .base import BaseCollector


class OpenInterestCollector(BaseCollector):
    COLLECTOR_TYPE = CollectorType.OPEN_INTEREST
    TABLE = OpenInterest

    async def backfill(
        self,
        since: datetime,
        duration: timedelta | None = None,
        limit: int = 100,
        missing_only: bool = False,
    ):
        since += timedelta(minutes=5)
        await super().backfill(
            since=since,
            duration=duration,
            limit=limit,
            missing_only=missing_only,
        )

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

    async def backfill_data(
        self,
        start_time: int,
        end_time: int | None = None,
        limit: int = 100,
        missing_only: bool = False,
    ):
        params = {
            "endTime": self.round_milliseconds(
                self.exchange.milliseconds(),
                offset=-1,
            )
        }
        if end_time:
            params["endTime"] = min(params["endTime"], end_time)

        active_symbols = await self.fetch_active_symbols()
        coroutines = [
            self.exchange.fetch_open_interest_history(
                symbol,
                timeframe="5m",
                since=self.round_milliseconds(start_time),
                limit=limit,
                params=params,
            )
            for symbol in active_symbols
        ]
        open_interest_list = await asyncio.gather(*coroutines)

        data: list[OpenInterest] = []
        for open_interests in open_interest_list:
            for open_interest in open_interests:
                data.append(
                    OpenInterest(
                        symbol=open_interest["symbol"],
                        exchange=self._exchange,
                        timestamp=self.round_milliseconds(
                            open_interest["timestamp"], offset=-1
                        ),
                        open_interest=open_interest["openInterestAmount"],
                        datetime=self.exchange.iso8601(
                            self.round_milliseconds(
                                open_interest["timestamp"], offset=-1
                            )
                        ),
                    )
                )
        return data
