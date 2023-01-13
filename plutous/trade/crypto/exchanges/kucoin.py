import math

from ccxt.pro import kucoin, kucoinfutures


class Kucoin(kucoin):
    def describe(self):
        return self.deep_extend(
            super(Kucoin, self).describe(),
            {"plutous_funcs": []},
        )


class KucoinFutures(kucoinfutures):
    def describe(self):
        return self.deep_extend(
            super(KucoinFutures, self).describe(),
            {"plutous_funcs": []},
        )

    async def fetch_funding_rates(self, symbols=None, params={}):
        funding_rates = {}
        markets = await self.load_markets(True, params=params)
        current_time: int = int(await self.fetch_time())
        symbols = self.market_symbols(symbols)
        for key, market in markets.items():
            if market["swap"]:
                nextFundingRateTime: int = self.safe_integer(
                    market["info"], "nextFundingRateTime"
                )
                market["info"]["nextFundingRateTime"] = (
                    math.floor((current_time + nextFundingRateTime) / 3600000) * 3600000
                )
                funding_rates[key] = self.parse_funding_rate_from_market(market)

        return self.filter_by_array(funding_rates, "symbol", symbols)

    def parse_funding_rate_from_market(self, market):
        info = self.safe_value(market, "info", {})
        markPrice = self.safe_number(info, "markPrice")
        indexPrice = self.safe_number(info, "indexPrice")
        fundingRate = self.safe_number(info, "fundingFeeRate")
        nextfundingRate = self.safe_number(info, "predictedFundingFeeRate")
        fundingTimestamp = self.safe_integer(info, "nextFundingRateTime")
        fundingDatetime = self.iso8601(fundingTimestamp)
        return {
            "info": info,
            "symbol": market["symbol"],
            "markPrice": markPrice,
            "indexPrice": indexPrice,
            "interestRate": None,
            "estimatedSettlePrice": None,
            "timestamp": None,
            "datetime": None,
            "fundingRate": fundingRate,
            "fundingTimestamp": fundingTimestamp,
            "fundingDatetime": fundingDatetime,
            "nextFundingRate": nextfundingRate,
            "nextFundingTimestamp": None,
            "nextFundingDatetime": None,
            "previousFundingRate": None,
            "previousFundingTimestamp": None,
            "previousFundingDatetime": None,
        }