from typing import Any

from plutous import database as db
from plutous.trade.crypto.enums import CollectorType
from plutous.trade.crypto.models import FundingRate, FundingSettlement

from .base import BaseCollector


class FundingRateCollector(BaseCollector):
    COLLECTOR_TYPE = CollectorType.FUNDING_RATE
    TABLE = FundingRate

    async def collect(self):
        fr, fs = await self.fetch_data()
        with db.Session() as session:
            self._insert(fr, session, FundingRate)
            self._insert(fs, session, FundingSettlement)
            session.commit()
        await self.exchange.close()

    async def fetch_data(self):
        active_symbols = await self.fetch_active_symbols()
        funding_rates: dict[str, dict[str, Any]] = await self.exchange.fetch_funding_rates()  # type: ignore
        fr = [
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

        fs = [
            FundingSettlement(
                symbol=funding_rate["symbol"],
                exchange=self._exchange,
                funding_rate=funding_rate["fundingRate"] * 100,
                timestamp=funding_rate["fundingTimestamp"],
                datetime=funding_rate["fundingDatetime"],
            )
            for funding_rate in funding_rates.values()
            if (funding_rate["symbol"] in active_symbols)
            & (
                funding_rate["fundingTimestamp"] - funding_rate["timestamp"]
                < 5 * 60 * 1000
            )
        ]
        return fr, fs

    async def backfill_data(self, start_time: int, end_time: int | None = None):
        if not end_time:
            end_time = self.round_milliseconds(self.exchange.milliseconds(), offset=-1)

        data: list[FundingRate] = []

        active_symbols = await self.fetch_active_symbols()
        for symbol in active_symbols:
            with db.Session() as session:
                last_funding_rate: FundingRate = (
                    session.query(FundingRate).filter(
                        FundingRate.exchange == self._exchange,
                        FundingRate.symbol == symbol,
                        FundingRate.timestamp == start_time,
                    )
                ).one()

            for time in range(start_time, end_time + 300000, 300000):
                data.append(
                    FundingRate(
                        symbol=symbol,
                        exchange=last_funding_rate.exchange,
                        timestamp=time,
                        funding_rate=last_funding_rate.funding_rate,
                        datetime=self.exchange.iso8601(time),
                    )
                )
        return data
