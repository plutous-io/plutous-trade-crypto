from ccxt.pro import bybit


class Bybit(bybit):
    funding_rates = None

    def describe(self):
        return self.deep_extend(
            super(Bybit, self).describe(),
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
        #     "timestamp": 1671522606730,
        #     "datetime": "2022-12-20T07:50:06.730Z",
        #     "high": 16990.0,
        #     "low": 16203.0,
        #     "bid": None,
        #     "bidVolume": None,
        #     "ask": None,
        #     "askVolume": None,
        #     "vwap": 16623.52702485755,
        #     "open": 16702.5,
        #     "close": 16785.0,
        #     "last": 16785.0,
        #     "previousClose": None,
        #     "change": 82.5,
        #     "percentage": 0.4939,
        #     "average": 16743.75,
        #     "baseVolume": 141761.47499999,
        #     "quoteVolume": 2356575710.746002,
        #     "info": {
        #         "symbol": "BTCUSDT",
        #         "tickDirection": "MinusTick",
        #         "price24hPcnt": "0.004939",
        #         "lastPrice": "16785.00",
        #         "prevPrice24h": "16702.50",
        #         "highPrice24h": "16990.00",
        #         "lowPrice24h": "16203.00",
        #         "prevPrice1h": "16809.00",
        #         "markPrice": "16787.41",
        #         "indexPrice": "16796.37",
        #         "openInterest": "63385.361",
        #         "turnover24h": "2356575710.746002",
        #         "volume24h": "141761.47499999",
        #         "nextFundingTime": "2022-12-20T08:00:00Z",
        #         "fundingRate": "0.0001",
        #         "predictedFundingRate": "",
        #         "bid1Price": "16785.00",
        #         "bid1Size": "61.205",
        #         "ask1Price": "16785.50",
        #         "ask1Size": "0.139",
        #         "deliveryFeeRate":"",
        #         "deliveryTime": ""
        #     },
        # }
        symbol = self.safe_string(message, "symbol")
        timestamp = self.safe_integer(message, "timestamp")
        info = self.safe_value(message, "info", {})
        markPrice = self.safe_number(info, "markPrice")
        indexPrice = self.safe_number(info, "indexPrice")
        fundingRate = self.safe_number(info, "fundingRate")
        fundingTime = self.safe_string(info, "fundingTime")
        fundingTimestamp = self.parse_date(fundingTime)
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

    async def fetch_funding_rates(self, symbols=None, params={}):
        results: dict = await self.fetch_tickers(symbols, params)
        for key, value in results.items():
            results[key] = self.parse_funding_rate_from_ticker(value)
        return results

    def parse_funding_rate_from_ticker(self, ticker):
        info = self.safe_value(ticker, "info", {})
        markPrice = self.safe_number(info, "markPrice")
        indexPrice = self.safe_number(info, "indexPrice")
        fundingRate = self.safe_number(info, "fundingRate")
        fundingTimestamp = self.safe_integer(info, "nextFundingTime")
        fundingDatetime = self.iso8601(fundingTimestamp)
        return {
            "info": info,
            "symbol": ticker["symbol"],
            "markPrice": markPrice,
            "indexPrice": indexPrice,
            "interestRate": None,
            "estimatedSettlePrice": None,
            "timestamp": ticker["timestamp"],
            "datetime": ticker["datetime"],
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