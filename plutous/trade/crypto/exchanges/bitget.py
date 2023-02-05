import asyncio

from ccxt.pro import bitget
from ccxt.base.errors import BadSymbol


class Bitget(bitget):
    funding_rates = None

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

    # patch
    async def fetch_funding_rate(self, symbol, params={}):
        """
        fetch the current funding rate
        :param str symbol: unified market symbol
        :param dict params: extra parameters specific to the bitget api endpoint
        :returns dict: a `funding rate structure <https://docs.ccxt.com/en/latest/manual.html#funding-rate-structure>`
        """
        await self.load_markets()
        market = self.market(symbol)
        if not market["swap"]:
            raise BadSymbol(
                self.id + " fetchFundingRate() supports swap contracts only"
            )
        request = {
            "symbol": market["id"],
        }
        fundingRate, fundingTime = await asyncio.gather(
            self.publicMixGetMarketCurrentFundRate(self.extend(request, params)),
            self.publicMixGetMarketFundingTime(self.extend(request, params)),
        )
        # Current Fund Rate
        #     {
        #         "code": "00000",
        #         "msg": "success",
        #         "requestTime": 1652401684275,
        #         "data": {
        #             "symbol": "BTCUSDT_UMCBL",
        #             "fundingRate": "-0.000182"
        #         }
        #     }
        #
        # Funding Time
        #     {
        #         "code":"00000",
        #         "data":{
        #             "symbol":"BTCUSDT_UMCBL",
        #             "fundingTime":"1627311600000"
        #         },
        #         "msg":"success",
        #         "requestTime":1627291915767
        #     }
        fundingRateData = self.safe_value(fundingRate, "data", {})
        fundingTimeData = self.safe_value(fundingTime, "data", {})
        data = self.extend(fundingRateData, fundingTimeData)
        return self.parse_funding_rate(data, market)

    # patch
    def parse_funding_rate(self, contract, market=None):
        #
        #     {
        #         "symbol": "BTCUSDT_UMCBL",
        #         "fundingRate": "-0.000182",
        #         "fundingTime": "1627311600000"
        #     }
        #
        marketId = self.safe_string(contract, "symbol")
        symbol = self.safe_symbol(marketId, market)
        fundingTime = self.safe_integer(contract, "fundingTime")
        return {
            "info": contract,
            "symbol": symbol,
            "markPrice": None,
            "indexPrice": None,
            "interestRate": None,
            "estimatedSettlePrice": None,
            "timestamp": None,
            "datetime": None,
            "fundingRate": self.safe_number(contract, "fundingRate"),
            "fundingTimestamp": fundingTime,
            "fundingDatetime": self.iso8601(fundingTime),
            "nextFundingRate": None,
            "nextFundingTimestamp": None,
            "nextFundingDatetime": None,
            "previousFundingRate": None,
            "previousFundingTimestamp": None,
            "previousFundingDatetime": None,
        }

    async def fetch_funding_history(self, symbol, since=None, limit=None, params={}):
        """
        fetch funding history
        :param str symbol: unified market symbol
        :param int since: unix timestamp in milliseconds
        :param int limit: max number of records to return
        :param dict params: extra parameters specific to the bitget api endpoint
        :returns list: a list of funding rate structures
        """
        await self.load_markets()
        market = self.market(symbol)
        if not market["swap"]:
            raise BadSymbol(
                self.id + " fetchFundingHistory() supports swap contracts only"
            )
        if since is None:
            since = self.milliseconds() - 31556952000  # 1yr
        request = {
            "symbol": market["id"],
            "marginCoin": market["quoteId"],
            "startTime": since,
            "endTime": self.milliseconds(),
        }
        if limit is not None:
            request['pageSize'] = limit
        response = await self.privateMixGetAccountAccountBill(
            self.extend(request, params)
        )
        # {
        # "code": "00000",
        # "msg": "success",
        # "data": {
        #     "result": [
        #     {
        #         "id": "892962903462432768",
        #         "symbol": "ETHUSDT_UMCBL",
        #         "marginCoin": "USDT",
        #         "amount": "0",
        #         "fee": "-0.1765104",
        #         "feeByCoupon": "",
        #         "feeCoin": "USDT",
        #         "business": "contract_settle_fee",
        #         "ctime": "1648624867354"
        #     }
        #     ],
        #     "endId": "885353495773458432",
        #     "nextFlag": false,
        #     "preFlag": false
        # }
        
        data = self.safe_value(response, "data", {})
        result = self.safe_value(data, "result", [])
        return self.parse_funding_histories(result, market, since, limit)

    def parse_funding_history(self, funding_history, market=None):
        #     {
        #         "id": "892962903462432768",
        #         "symbol": "ETHUSDT_UMCBL",
        #         "marginCoin": "USDT",
        #         "amount": "0",
        #         "fee": "-0.1765104",
        #         "feeByCoupon": "",
        #         "feeCoin": "USDT",
        #         "business": "contract_settle_fee",
        #         "ctime": "1648624867354"
        #     }
        marketId = self.safe_string(funding_history, 'symbol')
        symbol = self.safe_symbol(marketId, market, None, 'swap')
        timestamp = self.safe_integer(funding_history, "cTime")
        amount = self.safe_number(funding_history, "amount")
        currencyId = self.safe_string(funding_history, 'marginCoin')
        code = self.safe_currency_code(currencyId)
        id = self.safe_string(funding_history, 'id')
        return {
            'info': funding_history,
            'symbol': symbol,
            'code': code,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'id': id,
            'amount': amount,
        }

    def parse_funding_histories(self, funding_histories, market=None, since=None, limit=None):
        result = []
        for i in range(0, len(funding_histories)):
            entry = funding_histories[i]
            if entry['business'] == 'contract_settle_fee':
                parsed = self.parse_funding_history(entry, market)
                result.append(parsed)
        sorted = self.sort_by(result, 'timestamp')
        return self.filter_by_since_limit(sorted, since, limit)
