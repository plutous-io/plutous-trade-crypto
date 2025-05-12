import asyncio
from datetime import datetime, timedelta

from plutous import database as db
from plutous.trade.crypto.models import LongShortRatio

from .base import BaseCollector, BaseCollectorConfig

TIMEOUT = timedelta(minutes=10)


class LongShortRatioCollectorConfig(BaseCollectorConfig):
    symbol_type: str = "swap"
    sleep_time: int = 30


class LongShortRatioCollector(BaseCollector):
    TABLE = LongShortRatio

    config: LongShortRatioCollectorConfig

    async def _collect(self):
        while True:
            active_symbols = await self.fetch_active_symbols()
            coroutines = [
                self.exchange.fetch_long_short_ratio_history(
                    symbol,
                    timeframe="5m",
                    limit=1,
                )
                for symbol in active_symbols
            ]
            long_short_ratios: list[dict] = [
                lsr[0] for lsr in await asyncio.gather(*coroutines)
            ]

            if long_short_ratios[0]["timestamp"] < int(
                (datetime.now() - TIMEOUT).timestamp() * 1000
            ):
                raise RuntimeError(
                    f"Data is stale, last updated at {long_short_ratios[0]['timestamp']}"
                )
            with db.Session() as session:
                self._insert(
                    [
                        LongShortRatio(
                            symbol=long_short_ratio["symbol"],
                            exchange=self._exchange,
                            timestamp=self.round_milliseconds(
                                self.exchange.milliseconds()
                            ),
                            long_account=long_short_ratio["longAccount"],
                            short_account=long_short_ratio["shortAccount"],
                            long_short_ratio=long_short_ratio["longShortRatio"],
                            datetime=self.exchange.iso8601(
                                self.round_milliseconds(self.exchange.milliseconds())
                            ),
                        )
                        for long_short_ratio in long_short_ratios
                    ],
                    session,
                )
                session.commit()
            await asyncio.sleep(self.config.sleep_time)
