import asyncio

from ccxt.base.types import FundingRate, FundingRates, Market, Strings
from ccxt.pro import lbank


class LBank(lbank):
    async def fetch_funding_rates(
        self, symbols: Strings = None, params={}
    ) -> FundingRates:
        time, funding_rates = await asyncio.gather(
            self.fetch_time(),
            super().fetch_funding_rates(symbols, params),
        )
        for funding_rate in funding_rates.values():
            funding_rate["timestamp"], funding_rate["datetime"] = (
                time,
                self.iso8601(time),
            )
        return funding_rates

    def parse_funding_rate(self, ticker, market: Market = None) -> FundingRate:
        position_fee_time = self.safe_integer(ticker, "positionFeeTime")
        interval_string = None
        if position_fee_time is not None:
            interval = self.parse_to_int(position_fee_time / 60 / 60)
            interval_string = str(interval) + "h"
        fr = super().parse_funding_rate(ticker, market)
        fr["interval"] = interval_string
        return fr
