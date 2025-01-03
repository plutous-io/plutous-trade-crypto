from ccxt.base.errors import BadRequest, BadSymbol
from ccxt.base.types import FundingRate, FundingRates, Market, Strings
from ccxt.pro import phemex


class Phemex(phemex):
    def parse_funding_rate(self, contract, market: Market = None) -> FundingRate:
        fr = super().parse_funding_rate(contract, market)
        try:
            market = self.market(self.safe_string(fr, "symbol"))
            info = self.safe_dict(market, "info", {})
            intervalSecond = self.safe_integer(info, "fundingInterval")
            if intervalSecond is not None:
                fr["interval"] = str(int(intervalSecond / 60 / 60)) + "h"
                multiplier = intervalSecond * 1000
                settlementTimestamp = (
                    (self.milliseconds() // multiplier) + 1
                ) * multiplier
                fr["fundingTimestamp"] = settlementTimestamp
                fr["fundingDatetime"] = self.iso8601(settlementTimestamp)
        except BadSymbol:
            pass
        return fr

    async def fetch_funding_rates(
        self, symbols: Strings = None, params={}
    ) -> FundingRates:
        await self.load_markets()
        market: Market = None
        if symbols is not None:
            first = self.safe_value(symbols, 0)
            market: Market = self.market(first)
            if not market["swap"]:
                raise BadSymbol(
                    self.id + " fetchFundingRates() supports swap contracts only"
                )
        type = None
        type, params = self.handle_market_type_and_params(
            "fetchFundingRates", market, params, "swap"
        )
        subType = None
        subType, params = self.handle_sub_type_and_params(
            "fetchFundingRates", market, params, "linear"
        )
        query = self.omit(params, "type")
        if type != "swap":
            raise BadRequest(
                self.id + " does not support " + type + " markets, only swap"
            )
        response = None
        if subType == "inverse" or self.safe_string(market, "settle") == "USD":
            response = await self.v1GetMdTicker24hrAll(query)
        else:
            response = await self.v2GetMdV2Ticker24hrAll(query)
        result = self.safe_list(response, "result", [])
        funding_rates = self.parse_funding_rates(result)
        return self.filter_by_array(funding_rates, "symbol", symbols)
