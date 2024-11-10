import asyncio

from ccxt.base.types import FundingRate, FundingRates, Market, Strings
from ccxt.pro import bitget


class Bitget(bitget):

    def describe(self):
        return self.deep_extend(
            super(Bitget, self).describe(),
            {
                "has": {
                    "fetchFundingHistory": True,
                },
                "plutous_funcs": [],
            },
        )

    async def fetch_funding_rates(
        self, symbols: Strings = None, params={}
    ) -> FundingRates:
        await self.load_markets()
        market = None
        if symbols is not None:
            symbol = self.safe_value(symbols, 0)
            sandboxMode = self.safe_bool(self.options, "sandboxMode", False)
            if sandboxMode:
                sandboxSymbol = self.convert_symbol_for_sandbox(symbol)
                market = self.market(sandboxSymbol)
            else:
                market = self.market(symbol)
        _, params = self.handle_market_type_and_params(
            "fetchFundingRates", market, params
        )
        response = None
        request: dict = {}
        productType = None
        productType, params = self.handle_product_type_and_params(market, params)
        request["productType"] = productType
        response = await self.publicMixGetV2MixMarketTickers(
            self.extend(request, params)
        )
        # {
        #     "code": "00000",
        #     "msg": "success",
        #     "requestTime": 1700533773477,
        #     "data": [
        #         {
        #             "symbol": "BTCUSD",
        #             "lastPr": "29904.5",
        #             "askPr": "29904.5",
        #             "bidPr": "29903.5",
        #             "bidSz": "0.5091",
        #             "askSz": "2.2694",
        #             "high24h": "0",
        #             "low24h": "0",
        #             "ts": "1695794271400",
        #             "change24h": "0",
        #             "baseVolume": "0",
        #             "quoteVolume": "0",
        #             "usdtVolume": "0",
        #             "openUtc": "0",
        #             "changeUtc24h": "0",
        #             "indexPrice": "29132.353333",
        #             "fundingRate": "-0.0007",
        #             "holdingAmount": "125.6844",
        #             "deliveryStartTime": null,
        #             "deliveryTime": null,
        #             "deliveryStatus": "delivery_normal",
        #             "open24h": "0",
        #             "markPrice": "12345"
        #         },
        #     ]
        # }
        data = self.safe_list(response, "data", [])
        funding_rates = self.parse_funding_rates(data, market)
        funding_intervals = await asyncio.gather(
            *[self.fetch_funding_interval(symbol) for symbol in funding_rates.keys()]
        )
        to_remove = []
        for funding_rate, funding_interval in zip(
            funding_rates.values(), funding_intervals
        ):
            if self.market(funding_rate["symbol"])["type"] != "swap":
                to_remove.append(funding_rate["symbol"])
                continue
            funding_rate["interval"] = funding_interval["interval"]
            funding_rate["fundingTimestamp"] = funding_interval["fundingTimestamp"]
            funding_rate["fundingDatetime"] = funding_interval["fundingDatetime"]
        for symbol in to_remove:
            del funding_rates[symbol]
        return funding_rates

    def parse_funding_rate(self, contract, market: Market = None) -> FundingRate:
        fr = super().parse_funding_rate(contract, market)
        timestamp = self.safe_integer(contract, "ts")
        markPrice = self.safe_number(contract, "markPrice")
        indexPrice = self.safe_number(contract, "indexPrice")
        fr["timestamp"] = timestamp
        fr["datetime"] = self.iso8601(timestamp)
        fr["markPrice"] = markPrice
        fr["indexPrice"] = indexPrice
        return fr

    async def watch_funding_rate(self, symbol, params={}):
        message = await self.watch_ticker(symbol, params)
        return self.handle_funding_rate(message)

    def handle_funding_rate(self, message):
        if self.funding_rates is None:
            self.funding_rates = dict()

        funding_rate = self.parse_ws_funding_rate(message)
        self.funding_rates[funding_rate["symbol"]] = funding_rate
        return funding_rate

    def parse_ws_funding_rate(self, message, market=None):
        # linear usdt/ inverse swap and future
        # {
        #     "symbol": "BTC/USDT:USDT",
        #     "timestamp": 1671530087344,
        #     "datetime": "2022-12-20T09:54:47.344Z",
        #     "high": 16865.0,
        #     "low": 16246.0,
        #     "bid": 16794.5,
        #     "bidVolume": None,
        #     "ask": 16795.0,
        #     "askVolume": None,
        #     "vwap": 16629.686571813283,
        #     "open": None,
        #     "close": 16795.0,
        #     "last": 16795.0,
        #     "previousClose": None,
        #     "change": None,
        #     "percentage": None,
        #     "average": None,
        #     "baseVolume": 196773.582,
        #     "quoteVolume": 3272282994.273,
        #     "info": {
        #         "instId": "BTCUSDT",
        #         "last": "16795.00",
        #         "bestAsk": "16795",
        #         "bestBid": "16794.5",
        #         "high24h": "16865.00",
        #         "low24h": "16246.00",
        #         "priceChangePercent": "0.00804",
        #         "capitalRate": "0.000100",
        #         "nextSettleTime": 1671548400000,
        #         "systemTime": 1671530087344,
        #         "markPrice": "16794.69",
        #         "indexPrice": "16803.46",
        #         "holding": "146937.885",
        #         "baseVolume": "196773.582",
        #         "quoteVolume": "3272282994.273",
        #         "openUtc": "16427.5000000000000000",
        #         "chgUTC": "0.02237",
        #         "symbolType": 1,
        #         "symbolId": "BTCUSDT_UMCBL",
        #         "deliveryPrice": "0",
        #         "bidSz": "5.473",
        #         "askSz": "4.005",
        #     },
        # }
        symbol = self.safe_string(message, "symbol")
        timestamp = self.safe_integer(message, "timestamp")
        info = self.safe_value(message, "info", {})
        markPrice = self.safe_number(info, "markPrice")
        indexPrice = self.safe_number(info, "indexPrice")
        fundingRate = self.safe_number(info, "capitalRate")
        fundingTimestamp = self.safe_integer(info, "nextSettleTime")
        fundingDatetime = self.iso8601(fundingTimestamp)
        return {
            "info": info,
            "symbol": symbol,
            "markPrice": markPrice,
            "indexPrice": indexPrice,
            "interestRate": None,
            "estimatedSettlePrice": None,
            "timestamp": timestamp,
            "datetime": self.iso8601(timestamp),
            "fundingRate": fundingRate,
            "fundingTimestamp": fundingTimestamp,
            "fundingDatetime": fundingDatetime,
            "nextFundingRate": None,
            "nextFundingTimestamp": None,
            "nextFundingDatetime": None,
            "previousFundingRate": None,
            "previousFundingTimestamp": None,
            "previousFundingDatetime": None,
        }
