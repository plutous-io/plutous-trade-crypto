from typing import Any
import pandas as pd

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

    async def backfill_data(
        self,
        start_time: int,
        end_time: int | None = None,
        limit: int = 100,
        missing_only: bool = False,
    ):
        """Actually uses forward fill"""
        data: list[FundingRate] = []

        with db.engine.connect() as conn:
            kwargs = {
                "exchange": self._exchange,
                "symbols": await self.fetch_active_symbols(),
                "since": self.round_milliseconds(start_time),
                "frequency": "5m",
                "limit": limit,
                "conn": conn,
            }
            if end_time:
                kwargs["until"] = end_time
            fr_df = FundingRate.query(**kwargs).asfreq("5min")

        if len(fr_df):
            fr_df = fr_df.asfreq("5min")
            is_na_fr_df = fr_df.isna()
            fr_cols = (
                fr_df.columns[is_na_fr_df.any()] if missing_only else fr_df.columns
            )
            fr_df.ffill(inplace=True)

            for symbol in fr_cols.to_list():
                fr = (
                    fr_df[symbol][is_na_fr_df[symbol]]
                    if missing_only
                    else fr_df[symbol]
                )
                for ts, value in fr.items():
                    time = int(ts.timestamp() * 1000)
                    if pd.isnull(value):
                        continue
                    data.append(
                        FundingRate(
                            symbol=symbol,
                            exchange=self._exchange,
                            timestamp=time,
                            funding_rate=value,
                            datetime=self.exchange.iso8601(time),
                        )
                    )
        return data
