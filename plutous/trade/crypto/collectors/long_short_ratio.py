import asyncio

from plutous.trade.crypto.enums import CollectorType
from plutous.trade.crypto.models import LongShortRatio

from .base import BaseCollector


class LongShortRatioCollector(BaseCollector):
    COLLECTOR_TYPE = CollectorType.LONG_SHORT_RATIO
    TABLE = LongShortRatio

    async def fetch_data(self):
        last_timestamp = self.round_milliseconds(
            self.exchange.milliseconds(), offset=-1
        )
        active_symbols = await self.fetch_active_symbols()
        coroutines = [
            self.exchange.fetch_long_short_ratio_history(
                symbol,
                timeframe="5m",
                limit=1,
                params={"endTime": last_timestamp},
            )
            for symbol in active_symbols
        ]
        long_short_ratios = await asyncio.gather(*coroutines)
        long_short_ratios = [ratio[0] for ratio in long_short_ratios]

        return [
            LongShortRatio(
                symbol=symbol,
                exchange=self._exchange,
                timestamp=long_short_ratio["timestamp"],
                long_short_ratio=long_short_ratio["longShortRatio"],
                long_account=long_short_ratio["longAccount"],
                short_account=long_short_ratio["shortAccount"],
                datetime=long_short_ratio["datetime"],
            )
            for symbol, long_short_ratio in list(zip(active_symbols, long_short_ratios))
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
            self.exchange.fetch_long_short_ratio_history(
                symbol,
                timeframe="5m",
                since=self.round_milliseconds(start_time),
                limit=limit,
                params=params,
            )
            for symbol in active_symbols
        ]
        long_short_ratios = await asyncio.gather(*coroutines)

        data: list[LongShortRatio] = []
        for symbol, long_short_ratios in list(zip(active_symbols, long_short_ratios)):
            for long_short_ratio in long_short_ratios:
                data.append(
                    LongShortRatio(
                        symbol=symbol,
                        exchange=self._exchange,
                        timestamp=long_short_ratio["timestamp"],
                        long_short_ratio=long_short_ratio["longShortRatio"],
                        long_account=long_short_ratio["longAccount"],
                        short_account=long_short_ratio["shortAccount"],
                        datetime=long_short_ratio["datetime"],
                    )
                )
        return data
