from ccxt.base.types import FundingRates, Market, Strings
from ccxt.pro import lbank


class LBank(lbank):
    async def fetch_funding_rates(
        self, symbols: Strings = None, params={}
    ) -> FundingRates:
        """
        fetch the funding rate for multiple markets
        :see: https://www.lbank.com/en-US/docs/contract.html#query-contract-market-list
        :param str[]|None symbols: list of unified market symbols
        :param dict [params]: extra parameters specific to the exchange API endpoint
        :returns dict: a dictionary of `funding rates structures <https://docs.ccxt.com/#/?id=funding-rates-structure>`, indexed by market symbols
        """
        await self.load_markets()
        symbols = self.market_symbols(symbols)
        request: dict = {"productGroup": "SwapU"}
        response = await self.contractPublicGetCfdOpenApiV1PubMarketData(
            self.extend(request, params)
        )
        time = await self.fetch_time({"type": "swap"})
        # {
        #     "data": [
        #         {
        #             "symbol": "BTCUSDT",
        #             "highestPrice": "69495.5",
        #             "underlyingPrice": "68455.904",
        #             "lowestPrice": "68182.1",
        #             "openPrice": "68762.4",
        #             "positionFeeRate": "0.0001",
        #             "volume": "33534.2858",
        #             "markedPrice": "68434.1",
        #             "turnover": "1200636218.210558",
        #             "positionFeeTime": "28800",
        #             "lastPrice": "68427.3",
        #             "nextFeeTime": "1730736000000",
        #             "fundingRate": "0.0001",
        #         }
        #     ],
        #     "error_code": "0",
        #     "msg": "Success",
        #     "result": "true",
        #     "success": True,
        # }
        tickerList = self.safe_list(response, "data", [])
        for ticker in tickerList:
            ticker["timestamp"] = time
        result = self.parse_funding_rates(tickerList)
        return self.filter_by_array(result, "symbol", symbols)

    def parse_funding_rate(self, ticker, market: Market = None):
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
        symbol = self.safe_symbol(marketId, market, None, "contract")
        markPrice = self.safe_number(ticker, "markedPrice")
        indexPrice = self.safe_number(ticker, "underlyingPrice")
        fundingRate = self.safe_number(ticker, "fundingRate")
        nextFundTimestamp = self.safe_integer(ticker, "nextFeeTime")
        timestamp = self.safe_integer(ticker, "timestamp")
        return {
            "info": ticker,
            "symbol": symbol,
            "markPrice": markPrice,
            "indexPrice": indexPrice,
            "fundingRate": fundingRate,
            "fundingTimestamp": nextFundTimestamp,
            "fundingDatetime": self.iso8601(nextFundTimestamp),
            "interestRate": None,
            "estimatedSettlePrice": None,
            "timestamp": timestamp,
            "datetime": self.iso8601(timestamp),
            "nextFundingRate": None,
            "nextFundingTimestamp": None,
            "nextFundingDatetime": None,
            "previousFundingRate": None,
            "previousFundingTimestamp": None,
            "previousFundingDatetime": None,
        }
