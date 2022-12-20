from ccxt.pro import bitget


class Bitget(bitget):
    funding_rates = None

    def describe(self):
        return self.deep_extend(
            super(Bitget, self).describe(),
            {"plutous_funcs": []},
        )

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
