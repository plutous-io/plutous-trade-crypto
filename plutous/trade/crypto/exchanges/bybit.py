from ccxt.pro import bybit
from ccxt.base.errors import BadSymbol


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

    # async def fetch_funding_rates(self, symbols=None, params={}):
    #     results: dict = await self.fetch_tickers(symbols, params)
    #     for key, value in results.items():
    #         results[key] = self.parse_funding_rate_from_ticker(value)
    #     return results

    # def parse_funding_rate_from_ticker(self, ticker):
    #     info = self.safe_value(ticker, "info", {})
    #     markPrice = self.safe_number(info, "markPrice")
    #     indexPrice = self.safe_number(info, "indexPrice")
    #     fundingRate = self.safe_number(info, "fundingRate")
    #     fundingTimestamp = self.safe_integer(info, "nextFundingTime")
    #     fundingDatetime = self.iso8601(fundingTimestamp)
    #     return {
    #         "info": info,
    #         "symbol": ticker["symbol"],
    #         "markPrice": markPrice,
    #         "indexPrice": indexPrice,
    #         "interestRate": None,
    #         "estimatedSettlePrice": None,
    #         "timestamp": ticker["timestamp"],
    #         "datetime": ticker["datetime"],
    #         "fundingRate": fundingRate,
    #         "fundingTimestamp": fundingTimestamp,
    #         "fundingDatetime": fundingDatetime,
    #         "nextFundingRate": None,
    #         "nextFundingTimestamp": None,
    #         "nextFundingDatetime": None,
    #         "previousFundingRate": None,
    #         "previousFundingTimestamp": None,
    #         "previousFundingDatetime": None,
    #     }

    def parse_funding_rate(self, ticker, market=None, timestamp=None):
        #
        #     {
        #         "symbol": "BTCUSDT",
        #         "bidPrice": "19255",
        #         "askPrice": "19255.5",
        #         "lastPrice": "19255.50",
        #         "lastTickDirection": "ZeroPlusTick",
        #         "prevPrice24h": "18634.50",
        #         "price24hPcnt": "0.033325",
        #         "highPrice24h": "19675.00",
        #         "lowPrice24h": "18610.00",
        #         "prevPrice1h": "19278.00",
        #         "markPrice": "19255.00",
        #         "indexPrice": "19260.68",
        #         "openInterest": "48069.549",
        #         "turnover24h": "4686694853.047006",
        #         "volume24h": "243730.252",
        #         "fundingRate": "0.0001",
        #         "nextFundingTime": "1663689600000",
        #         "predictedDeliveryPrice": "",
        #         "basisRate": "",
        #         "deliveryFeeRate": "",
        #         "deliveryTime": "0"
        #     }
        #
        marketId = self.safe_string(ticker, "symbol")
        symbol = self.safe_symbol(marketId, market, None, "contract")
        fundingRate = self.safe_number(ticker, "fundingRate")
        fundingTimestamp = self.safe_integer(ticker, "nextFundingTime")
        markPrice = self.safe_number(ticker, "markPrice")
        indexPrice = self.safe_number(ticker, "indexPrice")
        return {
            "info": ticker,
            "symbol": symbol,
            "markPrice": markPrice,
            "indexPrice": indexPrice,
            "interestRate": None,
            "estimatedSettlePrice": None,
            "timestamp": timestamp,
            "datetime": self.iso8601(timestamp),
            "fundingRate": fundingRate,
            "fundingTimestamp": fundingTimestamp,
            "fundingDatetime": self.iso8601(fundingTimestamp),
            "nextFundingRate": None,
            "nextFundingTimestamp": None,
            "nextFundingDatetime": None,
            "previousFundingRate": None,
            "previousFundingTimestamp": None,
            "previousFundingDatetime": None,
        }

    async def fetch_funding_rate(self, symbol, params={}):
        """
        fetch the current funding rate
        :param str symbol: unified market symbol
        :param dict params: extra parameters specific to the bybit api endpoint
        :returns dict: a `funding rate structure <https://docs.ccxt.com/en/latest/manual.html#funding-rate-structure>`
        """
        await self.load_markets()
        market = self.market(symbol)
        request = {
            "symbol": market["id"],
        }
        method = None
        method = "publicGetDerivativesV3PublicTickers"
        if market["linear"]:
            request["category"] = "linear"
        elif market["inverse"]:
            request["category"] = "inverse"
        else:
            raise BadSymbol(self.id + " fetchFundingRate() does not support " + symbol)
        response = await getattr(self, method)(self.extend(request, params))
        #
        # {
        #     "retCode": 0,
        #     "retMsg": "OK",
        #     "result": {
        #         "category": "linear",
        #         "list": [
        #             {
        #                 "symbol": "BTCUSDT",
        #                 "bidPrice": "19255",
        #                 "askPrice": "19255.5",
        #                 "lastPrice": "19255.50",
        #                 "lastTickDirection": "ZeroPlusTick",
        #                 "prevPrice24h": "18634.50",
        #                 "price24hPcnt": "0.033325",
        #                 "highPrice24h": "19675.00",
        #                 "lowPrice24h": "18610.00",
        #                 "prevPrice1h": "19278.00",
        #                 "markPrice": "19255.00",
        #                 "indexPrice": "19260.68",
        #                 "openInterest": "48069.549",
        #                 "turnover24h": "4686694853.047006",
        #                 "volume24h": "243730.252",
        #                 "fundingRate": "0.0001",
        #                 "nextFundingTime": "1663689600000",
        #                 "predictedDeliveryPrice": "",
        #                 "basisRate": "",
        #                 "deliveryFeeRate": "",
        #                 "deliveryTime": "0"
        #             }
        #         ]
        #     },
        #     "retExtInfo": null,
        #     "time": 1663670053454
        # }
        #
        result = self.safe_value(response, "result", {})
        tickers = self.safe_value(result, "list")
        ticker = self.safe_value(tickers, 0)
        timestamp = self.safe_integer(response, "time")
        return self.parse_funding_rate(ticker, market, timestamp)

    async def fetch_funding_rates(self, symbols=None, params={}):
        """
        fetches funding rates for multiple markets
        :param [str]|None symbols: unified symbols of the markets to fetch the funding rates for, all market funding rates are returned if not assigned
        :param dict params: extra parameters specific to the bybit api endpoint
        :returns dict: an array of `funding rate structures <https://docs.ccxt.com/en/latest/manual.html#funding-rate-structure>`
        """
        await self.load_markets()
        symbols = self.market_symbols(symbols)
        request = {}
        subType, query = self.handle_sub_type_and_params(
            "fetchFundingRates", None, params, "linear"
        )
        if subType == "option":
            # bybit requires a symbol when query tockers for options markets
            raise NotSupported(
                self.id + " fetchTickers() is not supported for option markets"
            )
        else:
            request["category"] = subType
        response = await self.publicGetDerivativesV3PublicTickers(
            self.extend(request, query)
        )
        #
        #     {
        #         "retCode": 0,
        #         "retMsg": "OK",
        #         "result": {
        #             "category": "linear",
        #             "list": [
        #                 {
        #                     "symbol": "BTCUSDT",
        #                     "bidPrice": "19255",
        #                     "askPrice": "19255.5",
        #                     "lastPrice": "19255.50",
        #                     "lastTickDirection": "ZeroPlusTick",
        #                     "prevPrice24h": "18634.50",
        #                     "price24hPcnt": "0.033325",
        #                     "highPrice24h": "19675.00",
        #                     "lowPrice24h": "18610.00",
        #                     "prevPrice1h": "19278.00",
        #                     "markPrice": "19255.00",
        #                     "indexPrice": "19260.68",
        #                     "openInterest": "48069.549",
        #                     "turnover24h": "4686694853.047006",
        #                     "volume24h": "243730.252",
        #                     "fundingRate": "0.0001",
        #                     "nextFundingTime": "1663689600000",
        #                     "predictedDeliveryPrice": "",
        #                     "basisRate": "",
        #                     "deliveryFeeRate": "",
        #                     "deliveryTime": "0"
        #                 }
        #             ]
        #         },
        #         "retExtInfo": null,
        #         "time": 1663670053454
        #     }
        #
        tickerList = self.safe_value(response, "result", [])
        timestamp = self.safe_integer(response, "time")
        if not isinstance(tickerList, list):
            tickerList = self.safe_value(tickerList, "list")
        fundingRates = {}
        for i in range(0, len(tickerList)):
            ticker = self.parse_funding_rate(tickerList[i], None, timestamp)
            symbol = ticker["symbol"]
            fundingRates[symbol] = ticker
        return self.filter_by_array(fundingRates, "symbol", symbols)
