from ccxt.pro import bybit


class Bybit(bybit):
    funding_rates = None

    def describe(self):
        return self.deep_extend(
            super(Bybit, self).describe(),
            {
                "has": {
                    "fetchFundingHistory": True,
                },
                "plutous_funcs": [],
            },
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

    async def fetch_funding_history(
        self, symbol=None, since=None, limit=None, params={}
    ):
        await self.load_markets()
        market = self.market(symbol)
        request = {"symbol": market["id"], "exec_type": "Funding"}
        if since is not None:
            request["start_time"] = since
        if limit is not None:
            request["limit"] = limit
        response = await self.privateGetContractV3PrivateExecutionList(
            self.extend(request, params)
        )
        # contract v3
        #
        #     {
        #         "retCode": 0,
        #         "retMsg": "OK",
        #         "result": {
        #             "list": [
        #                 {
        #                     "symbol": "BITUSDT",
        #                     "execFee": "0.001356",
        #                     "execId": "499e1a2a-c664-55db-bbf0-78ad31b7b033",
        #                     "execPrice": "0.452",
        #                     "execQty": "5.0",
        #                     "execType": "Trade",
        #                     "execValue": "2.26",
        #                     "feeRate": "0.0006",
        #                     "lastLiquidityInd": "RemovedLiquidity",
        #                     "leavesQty": "0.0",
        #                     "orderId": "1d40db82-b1f6-4340-9190-650eeddd440b",
        #                     "orderLinkId": "",
        #                     "orderPrice": "0.430",
        #                     "orderQty": "5.0",
        #                     "orderType": "Market",
        #                     "stopOrderType": "UNKNOWN",
        #                     "side": "Sell",
        #                     "execTime": "1657269236943",
        #                     "closedSize": "5.0"
        #                 },
        #                 {
        #                     "symbol": "BITUSDT",
        #                     "execFee": "0.004068",
        #                     "execId": "ed090e6a-afc0-5cb5-b51d-039592a44ec5",
        #                     "execPrice": "0.452",
        #                     "execQty": "15.0",
        #                     "execType": "Trade",
        #                     "execValue": "6.78",
        #                     "feeRate": "0.0006",
        #                     "lastLiquidityInd": "RemovedLiquidity",
        #                     "leavesQty": "0.0",
        #                     "orderId": "d34d40a1-2475-4552-9e54-347a27282ec0",
        #                     "orderLinkId": "",
        #                     "orderPrice": "0.429",
        #                     "orderQty": "15.0",
        #                     "orderType": "Market",
        #                     "stopOrderType": "UNKNOWN",
        #                     "side": "Sell",
        #                     "execTime": "1657268340170",
        #                     "closedSize": "15.0"
        #                 }
        #             ],
        #             "nextPageCursor": ""
        #         },
        #         "retExtInfo": null,
        #         "time": 1658911518442
        #     }
        #
        result = self.safe_value(response, "result", {})
        funding_histories = self.safe_value(result, "list", [])
        return self.parse_funding_histories(funding_histories, market, since, limit)

    def parse_funding_history(self, funding_history, market=None):
        #
        #     {
        #         "symbol": "BITUSDT",
        #         "execFee": "0.001356",
        #         "execId": "499e1a2a-c664-55db-bbf0-78ad31b7b033",
        #         "execPrice": "0.452",
        #         "execQty": "5.0",
        #         "execType": "Trade",
        #         "execValue": "2.26",
        #         "feeRate": "0.0006",
        #         "lastLiquidityInd": "RemovedLiquidity",
        #         "leavesQty": "0.0",
        #         "orderId": "1d40db82-b1f6-4340-9190-650eeddd440b",
        #         "orderLinkId": "",
        #         "orderPrice": "0.430",
        #         "orderQty": "5.0",
        #         "orderType": "Market",
        #         "stopOrderType": "UNKNOWN",
        #         "side": "Sell",
        #         "execTime": "1657269236943",
        #         "closedSize": "5.0"
        #     }
        #
        timestamp = self.safe_integer(funding_history, "execTime")
        symbol = self.safe_string(funding_history, "symbol")
        market = self.safe_market(symbol, market, None, "swap")
        amount = self.safe_number(funding_history, "execFee")
        currencyId = market["quote"]
        code = self.safe_currency_code(currencyId)
        return {
            "info": funding_history,
            "symbol": symbol,
            "timestamp": timestamp,
            "datetime": self.iso8601(timestamp),
            "amount": amount,
            "code": code,
        }

    def parse_funding_histories(
        self, funding_histories, market=None, since=None, limit=None
    ):
        result = []
        for i in range(0, len(funding_histories)):
            result.append(self.parse_funding_history(funding_histories[i]))
        sorted = self.sort_by(result, "timestamp")
        return self.filter_by_since_limit(sorted, since, limit)
