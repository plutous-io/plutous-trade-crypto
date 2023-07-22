import asyncio

from plutous.trade.crypto.enums import CollectorType
from plutous.trade.crypto.models import OHLCV

from .base import BaseCollector


class OHLCVCollector(BaseCollector):
    COLLECTOR_TYPE = CollectorType.OHLCV
    TABLE = OHLCV

    async def fetch_data(self):
        last_timestamp = self.round_milliseconds(
            self.exchange.milliseconds(), offset=-1
        )
        active_symbols = await self.fetch_active_symbols()
        coroutines = [
            self.exchange.fetch_ohlcv(
                symbol,
                timeframe="5m",
                limit=1,
                params={"endTime": last_timestamp},
            )
            for symbol in active_symbols
        ]
        ohlcvs = await asyncio.gather(*coroutines)
        ohlcvs = [ohlcvs[0] for ohlcvs in ohlcvs]
        return [
            OHLCV(
                symbol=symbol,
                exchange=self._exchange,
                timestamp=ohlcv[0],
                open=ohlcv[1],
                high=ohlcv[2],
                low=ohlcv[3],
                close=ohlcv[4],
                volume=ohlcv[5],
                datetime=self.exchange.iso8601(ohlcv[0]),
            )
            for symbol, ohlcv in list(zip(active_symbols, ohlcvs))
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
            self.exchange.fetch_ohlcv(
                symbol,
                timeframe="5m",
                since=self.round_milliseconds(start_time),
                limit=limit,
                params=params,
            )
            for symbol in active_symbols
        ]
        ohlcvs = await asyncio.gather(*coroutines)

        data: list[OHLCV] = []
        for symbol, ohlcvs in list(zip(active_symbols, ohlcvs)):
            for ohlcv in ohlcvs:
                data.append(
                    OHLCV(
                        symbol=symbol,
                        exchange=self._exchange,
                        timestamp=ohlcv[0],
                        open=ohlcv[1],
                        high=ohlcv[2],
                        low=ohlcv[3],
                        close=ohlcv[4],
                        volume=ohlcv[5],
                        datetime=self.exchange.iso8601(ohlcv[0]),
                    )
                )
        return data
