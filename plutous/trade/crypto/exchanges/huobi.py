from ccxt.pro import huobi


class Huobi(huobi):
    funding_rates = None

    def describe(self):
        return self.deep_extend(
            super(Huobi, self).describe(),
            {
                "urls": {
                    "api": {
                        "ws": {
                            "api": {
                                "index": "wss://api.hbdm.com/ws_index",
                            },
                            # these settings work faster for clients hosted on AWS
                            "api-aws": {
                                "index": "wss://api.hbdm.vn/ws_index",
                            },
                        },
                    },
                },
                "options": {
                    "watchFundRateRate": "1min",  # 1min, 5min, 15min, 30min, 60min,4hour,1day, 1week, 1mon
                },
                "plutous_funcs": [],
            },
        )

    async def watch_funding_rate(self, symbol, params={}):
        """
        watches funding rate for a symbol
        :param str symbol: unified symbol of the market to fetch the ticker for
        :param dict params: extra parameters specific to the huobi api endpoint
        :returns dict: a `funding_rate structure <https://docs.ccxt.com/en/latest/manual.html#funding-rate-structure>`
        """
        await self.load_markets()
        market = self.market(symbol)
        symbol = market["symbol"]
        wfr_rate = self.safe_string(self.options, "watchFundRateRate", "1min")
        messageHash = "market." + market["id"] + ".estimated_rate" + "." + wfr_rate
        return await self.subscribe_index(symbol, messageHash, None, params)

    def handle_funding_rate(self, client, message):
        #
        #     {
        #         "ch":"market.BTC-USDT.estimated_rate.1min",
        #         "ts":1603708560233,
        #         "tick":{
        #             "id":1603708560,
        #             "open":"0.0001",
        #             "close":"0.0001",
        #             "high":"0.0001",
        #             "low":"0.0001",
        #             "amount":"0",
        #             "vol":"0",
        #             "count":"0",
        #             "trade_turnover":"0"
        #         }
        #     }
        #
        if not self.funding_rates:
            self.funding_rates = {}

        tick = self.safe_value(message, "tick", {})
        ch = self.safe_string(message, "ch")
        parts = ch.split(".")
        marketId = self.safe_string(parts, 1)
        market = self.safe_market(marketId)
        funding_rate = self.parse_ws_funding_rate(tick, market)
        timestamp = self.safe_integer(message, "ts")
        funding_rate["timestamp"] = timestamp
        funding_rate["datetime"] = self.iso8601(timestamp)
        symbol = market["symbol"]
        self.funding_rates[symbol] = funding_rate
        client.resolve(funding_rate, ch)
        return message

    def parse_ws_funding_rate(self, funding_rate, market=None):
        #
        #     {
        #         "id":1603708560,
        #         "open":"0.0001",
        #         "close":"0.0001",
        #         "high":"0.0001",
        #         "low":"0.0001",
        #         "amount":"0",
        #         "vol":"0",
        #         "count":"0",
        #         "trade_turnover":"0"
        #     }
        #
        marketId = self.safe_string_2(funding_rate, "symbol", "contract_code")
        symbol = self.safe_symbol(marketId, market)
        rate = self.safe_float(funding_rate, "close")
        return {
            "info": funding_rate,
            "symbol": symbol,
            "markPrice": None,
            "indexPrice": None,
            "interestRate": None,
            "estimatedSettlePrice": None,
            "timestamp": None,
            "datetime": None,
            "fundingRate": rate,
            "fundingTimestamp": None,
            "fundingDatetime": None,
            "nextFundingRate": None,
            "nextFundingTimestamp": None,
            "nextFundingDatetime": None,
            "previousFundingRate": None,
            "previousFundingTimestamp": None,
            "previousFundingDatetime": None,
        }

    def handle_subject(self, client, message):
        ch = self.safe_value(message, "ch", "")
        parts = ch.split(".")
        type = self.safe_string(parts, 0)
        if type == "market":
            methodName = self.safe_string(parts, 2)
            methods = {
                "estimated_rate": self.handle_funding_rate,
            }
            method = self.safe_value(methods, methodName)
            if method is None:
                return message
            else:
                return method(client, message)
        return super(Huobi, self).handle_subject(client, message)

    async def subscribe_index(self, symbol, messageHash, method=None, params={}):
        api = self.safe_string(self.options, "api", "api")
        url = self.urls["api"]["ws"][api]["index"]
        requestId = self.request_id()
        request = {
            "sub": messageHash,
            "id": requestId,
        }
        subscription = {
            "id": requestId,
            "messageHash": messageHash,
            "symbol": symbol,
            "params": params,
        }
        if method is not None:
            subscription["method"] = method
        return await self.watch(
            url, messageHash, self.extend(request, params), messageHash, subscription
        )
