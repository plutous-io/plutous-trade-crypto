from ccxt.pro import gateio


class GateIO(gateio):
    funding_rates = None

    def describe(self):
        return self.deep_extend(
            super(GateIO, self).describe(),
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
        #     {
        #         "symbol": "BTC/USDT:USDT",
        #         "timestamp": None,
        #         "datetime": None,
        #         "high": 16868.8,
        #         "low": 16209.3,
        #         "bid": None,
        #         "bidVolume": None,
        #         "ask": None,
        #         "askVolume": None,
        #         "vwap": 16783.41415634818,
        #         "open": None,
        #         "close": 16790.9,
        #         "last": 16790.9,
        #         "previousClose": None,
        #         "change": None,
        #         "percentage": 0.6184,
        #         "average": None,
        #         "baseVolume": 16233.0,
        #         "quoteVolume": 272445162.0,
        #         "info": {
        #             "contract": "BTC_USDT",
        #             "last": "16790.9",
        #             "change_percentage": "0.6184",
        #             "total_size": "132266913",
        #             "volume_24h": "162332327",
        #             "volume_24h_base": "16233",
        #             "volume_24h_quote": "272445162",
        #             "volume_24h_settle": "272445162",
        #             "mark_price": "16797.51",
        #             "funding_rate": "0.000077",
        #             "funding_rate_indicative": "0.000077",
        #             "index_price": "16797.24",
        #             "quanto_base_rate": "",
        #             "low_24h": "16209.3",
        #             "high_24h": "16868.8",
        #         },
        #     }

        symbol = self.safe_string(message, "symbol")
        timestamp = self.safe_integer(message, "timestamp")
        info = self.safe_value(message, "info", {})
        markPrice = self.safe_number(info, "mark_price")
        indexPrice = self.safe_number(info, "index_price")
        fundingRate = self.safe_number(info, "funding_rate")
        funingRateIndicative = self.safe_number(info, "funding_rate_indicative")
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
            "fundingTimestamp": None,
            "fundingDatetime": None,
            "nextFundingRate": funingRateIndicative,
            "nextFundingTimestamp": None,
            "nextFundingDatetime": None,
            "previousFundingRate": None,
            "previousFundingTimestamp": None,
            "previousFundingDatetime": None,
        }
