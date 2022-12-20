from ccxt.pro import okx


class Okx(okx):
    funding_rates = None

    def describe(self):
        return self.deep_extend(
            super(Okx, self).describe(),
            {"plutous_funcs": []},
        )

    async def watch_funding_rate(self, symbol, params={}):
        return await self.subscribe("public", "funding-rate", symbol, params)

    def handle_funding_rate(self, client, message):
        #
        #     {
        #         "arg": {
        #             "channel": "funding-rate",
        #             "instId": "BTC-USD-SWAP"
        #         },
        #         "data": [
        #             {
        #             "fundingRate": "0.0001515",
        #             "fundingTime": "1622822400000",
        #             "instId": "BTC-USD-SWAP",
        #             "instType": "SWAP",
        #             "nextFundingRate": "0.00029",
        #             "nextFundingTime": "1622851200000"
        #             }
        #         ]
        #     }
        #
        if not self.funding_rates:
            self.funding_rates = dict()

        arg = self.safe_value(message, "arg", {})
        channel = self.safe_string(arg, "channel")
        data = self.safe_value(message, "data", [])
        for i in range(0, len(data)):
            funding_rate = self.parse_funding_rate(data[i])
            symbol = funding_rate["symbol"]
            marketId = self.safe_string(funding_rate["info"], "instId")
            messageHash = channel + ":" + marketId
            self.funding_rates[symbol] = funding_rate
            client.resolve(funding_rate, messageHash)
        return message

    def handle_message(self, client, message):
        if not self.handle_error_message(client, message):
            return
        #
        #     {event: 'subscribe', arg: {channel: 'tickers', instId: 'BTC-USDT'}}
        #     {event: 'login', msg: '', code: '0'}
        #
        #     {
        #         arg: {channel: 'tickers', instId: 'BTC-USDT'},
        #         data: [
        #             {
        #                 instType: 'SPOT',
        #                 instId: 'BTC-USDT',
        #                 last: '31500.1',
        #                 lastSz: '0.00001754',
        #                 askPx: '31500.1',
        #                 askSz: '0.00998144',
        #                 bidPx: '31500',
        #                 bidSz: '3.05652439',
        #                 open24h: '31697',
        #                 high24h: '32248',
        #                 low24h: '31165.6',
        #                 sodUtc0: '31385.5',
        #                 sodUtc8: '32134.9',
        #                 volCcy24h: '503403597.38138519',
        #                 vol24h: '15937.10781721',
        #                 ts: '1626526618762'
        #             }
        #         ]
        #     }
        #
        #     {event: 'error', msg: 'Illegal request: {"op":"subscribe","args":["spot/ticker:BTC-USDT"]}', code: '60012'}
        #     {event: 'error', msg: "channel:ticker,instId:BTC-USDT doesn't exist", code: '60018'}
        #     {event: 'error', msg: 'Invalid OK_ACCESS_KEY', code: '60005'}
        #     {
        #         event: 'error',
        #         msg: 'Illegal request: {"op":"login","args":["de89b035-b233-44b2-9a13-0ccdd00bda0e","7KUcc8YzQhnxBE3K","1626691289","H57N99mBt5NvW8U19FITrPdOxycAERFMaapQWRqLaSE="]}',
        #         code: '60012'
        #     }
        #
        if message == "pong":
            return self.handle_pong(client, message)
        # table = self.safe_string(message, 'table')
        # if table is None:
        event = self.safe_string(message, "event")
        if event is not None:
            methods = {
                # 'info': self.handleSystemStatus,
                # 'book': 'handleOrderBook',
                "login": self.handle_authenticate,
                "subscribe": self.handle_subscription_status,
            }
            method = self.safe_value(methods, event)
            if method is None:
                return message
            else:
                return method(client, message)
        else:
            arg = self.safe_value(message, "arg", {})
            channel = self.safe_string(arg, "channel")
            methods = {
                "bbo-tbt": self.handle_order_book,  # newly added channel that sends tick-by-tick Level 1 data, all API users can subscribe, public depth channel, verification not required
                "books": self.handle_order_book,  # all API users can subscribe, public depth channel, verification not required
                "books5": self.handle_order_book,  # all API users can subscribe, public depth channel, verification not required, data feeds will be delivered every 100ms(vs. every 200ms now)
                "books50-l2-tbt": self.handle_order_book,  # only users who're VIP4 and above can subscribe, identity verification required before subscription
                "books-l2-tbt": self.handle_order_book,  # only users who're VIP5 and above can subscribe, identity verification required before subscription
                "tickers": self.handle_ticker,
                "trades": self.handle_trades,
                "account": self.handle_balance,
                # 'margin_account': self.handle_balance,
                "orders": self.handle_orders,
                "orders-algo": self.handle_orders,
                "funding-rate": self.handle_funding_rate,
            }
            method = self.safe_value(methods, channel)
            if method is None:
                if channel.find("candle") == 0:
                    self.handle_ohlcv(client, message)
                else:
                    return message
            else:
                return method(client, message)
