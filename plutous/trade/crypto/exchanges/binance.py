from datetime import datetime, timedelta, timezone

from ccxt.base.errors import BadSymbol, NotSupported
from ccxt.pro import binance, binancecoinm, binanceusdm

from ..utils import paginate


class BinanceBase(binance):
    def describe(self):
        return self.deep_extend(
            super(BinanceBase, self).describe(),
            {
                "options": {
                    "watchFundingRate": {
                        "name": "markPrice",
                    },
                    # get updates every 1000ms or 3000ms
                    "watchFundingRateRate": 1000
                },
                "plutous_funcs": [
                    "parse_c2c_trade",
                    "parse_c2c_trades",
                    "fetch_incomes",
                    "fetch_c2c_trades",
                    "fetch_commissions",
                    "fetch_wallet_balance",
                ],
            },
        )

    def parse_c2c_trade(self, trade):
        # {'orderNumber': '20300690644555571200',
        # 'advNo': '11300308153087909888',
        # 'tradeType': 'BUY',
        # 'asset': 'USDT',
        # 'fiat': 'RON',
        # 'fiatSymbol': 'lei',
        # 'amount': '455.89000000',
        # 'totalPrice': '2000.00000000',
        # 'unitPrice': '4.387',
        # 'orderStatus': 'COMPLETED',
        # 'createTime': '1638684240000',
        # 'commission': '0',
        # 'counterPartNickName': 'X***',
        # 'advertisementRole': 'TAKER'}

        timestamp = self.safe_integer(trade, "createTime")
        id = self.safe_string(trade, "orderNumber")
        advNo = self.safe_string(trade, "advNo")
        tradeType = self.safe_string(trade, "tradeType")
        asset = self.safe_string(trade, "asset")
        fiat = self.safe_string(trade, "fiat")
        fiatSymbol = self.safe_string(trade, "fiatSymbol")
        amount = self.safe_string(trade, "amount")
        totalPrice = self.safe_string(trade, "totalPrice")
        unitPrice = self.safe_string(trade, "unitPrice")
        orderStatus = self.safe_string(trade, "orderStatus")
        commission = self.safe_string(trade, "commission")
        counterPartNickName = self.safe_string(trade, "counterPartNickName")
        advertisementRole = self.safe_string(trade, "advertisementRole")

        return {
            "id": id,
            "advNo": advNo,
            "tradeType": tradeType,
            "asset": asset,
            "fiat": fiat,
            "fiatSymbol": fiatSymbol,
            "amount": amount,
            "totalPrice": totalPrice,
            "unitPrice": unitPrice,
            "orderStatus": orderStatus,
            "timestamp": timestamp,
            "commission": commission,
            "counterPartNickName": counterPartNickName,
            "advertisementRole": advertisementRole,
        }

    def parse_convert_history(self, trade):
        # {'quoteId': 'aea3a3a53f5e4667b8df7241f04b7b9b',
        # 'orderId': '1085789920229951883',
        # 'orderStatus': 'SUCCESS',
        # 'fromAsset': 'BUSD',
        # 'fromAmount': '20',
        # 'toAsset': 'USDT',
        # 'toAmount': '19.98304',
        # 'ratio': '0.999152',
        # 'inverseRatio': '1.0008487',
        # 'createTime': '1641138583193'}

        fromAsset = self.safe_string(trade, "fromAsset")
        toAsset = self.safe_string(trade, "toAsset")
        timestamp = self.safe_string(trade, "createTime")
        id = self.safe_string(trade, "quoteId")
        order_id = self.safe_string(trade, "orderId")
        to_amount = self.safe_string(trade, "toAmount")
        from_amount = self.safe_string(trade, "fromAmount")
        try:
            symbol = f"{fromAsset}/{toAsset}"
            self.market(symbol)
            price = self.safe_string(trade, "ratio")
            side = "sell"
            amount = from_amount
            cost = to_amount

        except BadSymbol:
            symbol = f"{toAsset}/{fromAsset}"
            price = self.safe_string(trade, "inverseRatio")
            side = "buy"
            amount = to_amount
            cost = from_amount

        return {
            "info": trade,
            "symbol": symbol,
            "timestamp": timestamp,
            "datetime": self.iso8601(timestamp),
            "id": id,
            "order": order_id,
            "price": price,
            "amount": amount,
            "cost": cost,
            "side": side,
        }

    def parse_c2c_trades(self, trades):
        # {'code': '000000',
        #  'message': 'success',
        #  'data': [{'orderNumber': '20300690644555571200',
        #    'advNo': '11300308153087909888',
        #    'tradeType': 'BUY',
        #    'asset': 'USDT',
        #    'fiat': 'RON',
        #    'fiatSymbol': 'lei',
        #    'amount': '455.89000000',
        #    'totalPrice': '2000.00000000',
        #    'unitPrice': '4.387',
        #    'orderStatus': 'COMPLETED',
        #    'createTime': '1638684240000',
        #    'commission': '0',
        #    'counterPartNickName': 'X***',
        #    'advertisementRole': 'TAKER'},
        #   {'orderNumber': '20300479660467953664',
        #    'advNo': '11299858648265822208',
        #    'tradeType': 'BUY',
        #    'asset': 'USDT',
        #    'fiat': 'RON',
        #    'fiatSymbol': 'lei',
        #    'amount': '434.97000000',
        #    'totalPrice': '2000.00000000',
        #    'unitPrice': '4.598',
        #    'orderStatus': 'COMPLETED',
        #    'createTime': '1638633938000',
        #    'commission': '0',
        #    'counterPartNickName': 'Usd***',
        #    'advertisementRole': 'TAKER'}],
        #  'total': '2',
        #  'success': True}
        trades = trades["data"]
        result = []
        for trade in trades:
            result.append(self.parse_c2c_trade(trade))

        return result

    def parse_convert_histories(self, trades):
        # {'list': [{'quoteId': 'ba797fac76cc43f28f135a5456e5c246',
        #    'orderId': '1085789190085435434',
        #    'orderStatus': 'SUCCESS',
        #    'fromAsset': 'BUSD',
        #    'fromAmount': '100.4338',
        #    'toAsset': 'USDT',
        #    'toAmount': '100.34863214',
        #    'ratio': '0.999152',
        #    'inverseRatio': '1.00084872',
        #    'createTime': '1641138498751'},
        #   {'quoteId': 'aea3a3a53f5e4667b8df7241f04b7b9b',
        #    'orderId': '1085789920229951883',
        #    'orderStatus': 'SUCCESS',
        #    'fromAsset': 'BUSD',
        #    'fromAmount': '20',
        #    'toAsset': 'USDT',
        #    'toAmount': '19.98304',
        #    'ratio': '0.999152',
        #    'inverseRatio': '1.00084872',
        #    'createTime': '1641138583193'},
        #  'startTime': '1640995200000',
        #  'endTime': '1643587200000',
        #  'limit': '100',
        #  'moreData': False}
        trades = trades["list"]
        result = []
        for trade in trades:
            result.append(self.parse_convert_history(trade))
        return result

    async def fetch_wallet_balance(self, params={}):
        defaultType = self.safe_string_2(
            self.options, "fetchWalletBalance", "defaultType", "spot"
        )
        type = self.safe_string(params, "type", defaultType)

        query = params.copy()
        query["type"] = type
        balance = await self.fetch_balance(query)
        if type in ("future", "delivery"):
            # Futures balance took marginBalance as the total,
            # we are looking for wallet balance
            balance = balance["info"]["assets"]
            return {
                item["asset"]: self.parse_number(item["walletBalance"])
                for item in balance
                if float(item["walletBalance"]) != 0.0
            }
        else:
            balance = balance["total"]
            return {key: val for key, val in balance.items() if val != 0.0}

    async def fetch_incomes(
        self,
        income_type=None,
        symbol=None,
        since=None,
        limit=None,
        params={},
    ):
        defaultType = "future"
        market = None
        request = {}
        if since is not None:
            request["startTime"] = since
        if limit is not None:
            request["limit"] = limit
        if income_type is not None:
            request[
                "incomeType"
            ] = income_type  # "TRANSFER"，"WELCOME_BONUS", "REALIZED_PNL"，"FUNDING_FEE", "COMMISSION" and "INSURANCE_CLEAR"

        await self.load_markets()
        if symbol is not None:
            market = self.market(symbol)
            request["symbol"] = market["id"]
        defaultType = self.safe_string(self.options, "defaultType", defaultType)
        type = self.safe_string(params, "type", defaultType)
        params = self.omit(params, "type")
        if (type == "future") or (type == "linear"):
            method = "fapiPrivateGetIncome"
        elif (type == "delivery") or (type == "inverse"):
            method = "dapiPrivateGetIncome"
        else:
            raise NotSupported(
                self.id + " fetchIncomes() supports linear and inverse contracts only"
            )
        response = await getattr(self, method)(self.extend(request, params))
        return self.parse_incomes(response, market, since, limit)

    async def fetch_commissions(self, symbol=None, since=None, limit=None, params={}):
        return await self.fetch_incomes("COMMISSION", symbol, since, limit, params)

    async def fetch_funding_history(
        self, symbol=None, since=None, limit=None, params={}
    ):
        return await self.fetch_incomes("FUNDING_FEE", symbol, since, limit, params)

    @paginate(
        max_limit=100,
        max_interval=timedelta(days=30),
        start_time_arg="startTimestamp",
        end_time_arg="endTimestamp",
    )
    async def fetch_c2c_trades(self, since=None, limit=None, params={}):
        query = params.copy()
        if since is not None:
            query["startTimestamp"] = since

        if limit is not None:
            query["row"] = limit

        trades = await self.sapi_get_c2c_ordermatch_listuserorderhistory(query)
        return self.parse_c2c_trades(trades)

    @paginate(
        max_limit=1000,
        max_interval=timedelta(days=30),
    )
    async def fetch_convert_history(
        self,
        since=None,
        limit=None,
        params={},
    ):
        await self.load_markets()
        if since is None:
            since = int(
                (datetime.now(timezone.utc) - timedelta(days=30)).timestamp() * 1000
            )

        end = params.get("endTime", datetime.now(timezone.utc))
        query = params.copy()

        if limit is not None:
            query["limit"] = limit

        query["startTime"] = since
        query["endTime"] = end

        trades = await self.sapi_get_convert_tradeflow(params=query)
        return self.parse_convert_histories(trades)

    async def watch_funding_rate(self, symbol, params={}):
        await self.load_markets()
        market = self.market(symbol)
        options = self.safe_value(self.options, 'watchTrades', {})
        name = self.safe_string(options, 'name', 'markPrice')
        messageHash = market["lowercaseId"] + "@" + name
        type, params = self.handle_market_type_and_params("watchFundingRate", market, params)
        url = self.urls['api']['ws'][type] + '/' + self.stream(type, messageHash)
        requestId = self.request_id(url)
        request = {
            'method': 'SUBSCRIBE',
            'params': [
                messageHash,
            ],
            'id': requestId,
        }
        subscribe = {
            'id': requestId,
        }
        return await self.watch(url, messageHash, self.extend(request, params), messageHash, subscribe)

    def handle_funding_rate(self, client, message):
        # mark price update
        #     {
        #         "e": "markPriceUpdate",     # Event type
        #         "E": 1562305380000,         # Event time
        #         "s": "BTCUSDT",             # Symbol
        #         "p": "11794.15000000",      # Mark price
        #         "i": "11784.62659091",      # Index price
        #         "P": "11784.25641265",      # Estimated Settle Price, only useful in the last hour before the settlement starts
        #         "r": "0.00038167",          # Funding rate
        #         "T": 1562306400000          # Next funding time
        #     }

        
        return


class Binance(BinanceBase):
    @paginate(max_limit=1000)
    async def fetch_ohlcv(
        self,
        symbol,
        timeframe,
        since=None,
        limit=None,
        params={},
    ):
        return await super().fetch_ohlcv(symbol, timeframe, since, limit, params)

    @paginate(
        max_limit=1000,
        max_interval=timedelta(days=1),
    )
    async def fetch_my_trades(
        self,
        symbol=None,
        since=None,
        limit=None,
        params={},
    ):
        return await super().fetch_my_trades(symbol, since, limit, params)


class BinanceUsdm(BinanceBase, binanceusdm):
    @paginate(
        max_limit=1000,
        max_interval=timedelta(days=7),
    )
    async def fetch_my_trades(
        self,
        symbol=None,
        since=None,
        limit=None,
        params={},
    ):
        return await super().fetch_my_trades(symbol, since, limit, params)

    @paginate(max_limit=1000)
    async def fetch_incomes(
        self,
        income_type=None,
        symbol=None,
        since=None,
        limit=None,
        params={},
    ):
        return await super().fetch_incomes(
            income_type,
            symbol,
            since,
            limit,
            params,
        )


class BinanceCoinm(BinanceBase, binancecoinm):
    @paginate(max_limit=1000)
    async def fetch_my_trades(
        self,
        symbol=None,
        since=None,
        limit=None,
        params={},
    ):
        return await super().fetch_my_trades(symbol, since, limit, params)

    @paginate(
        max_limit=1000,
        max_interval=timedelta(days=200),
    )
    async def fetch_incomes(
        self,
        income_type=None,
        symbol=None,
        since=None,
        limit=None,
        params={},
    ):
        return await super().fetch_incomes(income_type, symbol, since, limit, params)
