import asyncio
import time
from datetime import datetime
from typing import Type

from loguru import logger

from plutous import database as db
from plutous.trade.crypto.models import ohlcv as m

from .base import BaseCollector, BaseCollectorConfig


class OHLCVCollectorConfig(BaseCollectorConfig):
    symbols: list[str] = [
        "ETH/USDT:USDT",
        "BTC/USDT:USDT",
    ]
    symbol_type: str = "swap"
    frequency: str = "1h"
    cold_start_duration: int = 5  # minutes


class OHLCVCollector(BaseCollector):
    TABLE = m.OHLCV

    config: OHLCVCollectorConfig

    async def _collect(self):
        while minute_countdown := (60 - datetime.now().minute) < (
            self.config.cold_start_duration
        ):
            logger.info("Cold starting, waiting for the next hour")
            if minute_countdown > 1:
                time.sleep(30)
            time.sleep(1)

        Table: Type[m.Base] = getattr(m, f"OHLCV{self.config.frequency}")
        round_milliseconds = self.exchange.parse_timeframe(self.config.frequency) * 1000
        last_timestamp = self.round_milliseconds(
            self.exchange.milliseconds(),
            round_milliseconds,
            offset=-1,
        )
        active_symbols = await self.fetch_active_symbols()
        coroutines = [
            self.exchange.fetch_ohlcv(
                symbol,
                timeframe=self.config.frequency,
                since=last_timestamp,
                params={},
            )
            for symbol in active_symbols
        ]
        ohlcvs = await asyncio.gather(*coroutines)
        ohlcvs = [ohlcvs[0] for ohlcvs in ohlcvs]
        ohlcv = [
            Table(
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
        if ohlcv[0].timestamp != last_timestamp:
            raise RuntimeError(f"Data is stale, last updated at {ohlcv[0].timestamp}")

        with db.Session() as session:
            self._insert(ohlcv, session, Table)
            session.commit()

        await self.exchange.close()
