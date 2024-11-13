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
        # {
        #     "symbol": "BTCUSDT",
        #     "highestPrice": "69495.5",
        #     "underlyingPrice": "68455.904",
        #     "lowestPrice": "68182.1",
        #     "openPrice": "68762.4",
        #     "positionFeeRate": "0.0001",
        #     "volume": "33534.2858",
        #     "markedPrice": "68434.1",
        #     "turnover": "1200636218.210558",
        #     "positionFeeTime": "28800",
        #     "lastPrice": "68427.3",
        #     "nextFeeTime": "1730736000000",
        #     "fundingRate": "0.0001",
        # }
        marketId = self.safe_string(ticker, "symbol")
        symbol = self.safe_symbol(marketId, market)
        markPrice = self.safe_number(ticker, "markedPrice")
        indexPrice = self.safe_number(ticker, "underlyingPrice")
        fundingRate = self.safe_number(ticker, "fundingRate")
        fundingTime = self.safe_integer(ticker, "nextFeeTime")
        positionFeeTime = self.safe_integer(ticker, "positionFeeTime")
        intervalString = None
        if positionFeeTime is not None:
            interval = self.parse_to_int(positionFeeTime / 60 / 60)
            intervalString = str(interval) + "h"
        return {
            "info": ticker,
            "symbol": symbol,
            "markPrice": markPrice,
            "indexPrice": indexPrice,
            "fundingRate": fundingRate,
            "fundingTimestamp": fundingTime,
            "fundingDatetime": self.iso8601(fundingTime),
            "timestamp": None,
            "datetime": None,
            "nextFundingRate": None,
            "nextFundingTimestamp": None,
            "nextFundingDatetime": None,
            "previousFundingRate": None,
            "previousFundingTimestamp": None,
            "previousFundingDatetime": None,
            "interval": intervalString,
        }
