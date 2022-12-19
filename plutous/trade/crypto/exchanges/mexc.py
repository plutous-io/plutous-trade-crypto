from ccxt.pro import mexc


class Mexc(mexc):
    funding_rates = None

    def describe(self):
        return self.deep_extend(
            super(Mexc, self).describe(),
            {
                "plutous_funcs": [
                    "handle_funding_rate",
                    "watch_funding_rate",
                ],
            },
        )

    async def watch_funding_rate(self, symbol, params={}):
        """
        get the live funing rate for a particular symbol
        :param str symbol: unified symbol of the market to fetch trades for
        :param dict params: extra parameters specific to the mexc api endpoint
        :returns [dict]: a list of `trade structures <https://docs.ccxt.com/en/latest/manual.html?#public-trades>`
        """
        await self.load_markets()
        market = self.market(symbol)
        symbol = market["symbol"]
        channel = "sub.funding.rate"
        messageHash = "funding.rate" + ":" + symbol
        requestParams = {
            "symbol": market["id"],
        }
        return await self.watch_swap_public(messageHash, channel, requestParams, params)

    def handle_funding_rate(self, client, message):
        # funding rates
        #     {
        #         "channel":"push.funding.rate",
        #         "data":{
        #             "rate":0.001,
        #             "symbol":"BTC_USDT"
        #         },
        #         "symbol":"BTC_USDT",
        #         "ts":1587442022003
        #     }
        #
        if self.funding_rates is None:
            self.funding_rates = dict()
        data = self.safe_value(message, "data", {})
        data["fundingRate"] = self.safe_number(data, "rate")
        data["timestamp"] = self.safe_integer(message, "ts")
        marketId = self.safe_string(message, "symbol")
        market = self.safe_market(marketId)
        symbol = market["symbol"]
        funding_rate = self.parse_funding_rate(data, market)
        self.funding_rates[symbol] = funding_rate
        messageHash = "funding.rate:" + symbol
        client.resolve(funding_rate, messageHash)
        return message

    def handle_message(self, client, message):
        #
        # spot pong
        #
        #  "ping"
        #
        # swap pong
        #  {channel: 'pong', data: 1651570941402, ts: 1651570941402}
        #
        # auth spot
        #
        #  {channel: 'sub.personal', msg: 'OK'}
        #
        # auth swap
        #
        #  {channel: 'rs.login', data: 'success', ts: 1651486643082}
        #
        # subscription
        #
        #  {channel: 'rs.sub.depth', data: 'success', ts: 1651239594401}
        #
        # swap ohlcv
        #     {
        #         "channel":"push.kline",
        #         "data":{
        #             "a":233.740269343644737245,
        #             "c":6885,
        #             "h":6910.5,
        #             "interval":"Min60",
        #             "l":6885,
        #             "o":6894.5,
        #             "q":1611754,
        #             "symbol":"BTC_USDT",
        #             "t":1587448800
        #         },
        #         "symbol":"BTC_USDT",
        #         "ts":1587442022003
        #     }
        #
        # swap ticker
        #     {
        #         channel: 'push.ticker',
        #         data: {
        #           amount24: 491939387.90105,
        #           ask1: 39530.5,
        #           bid1: 39530,
        #           contractId: 10,
        #           fairPrice: 39533.4,
        #           fundingRate: 0.00015,
        #           high24Price: 40310.5,
        #           holdVol: 187680157,
        #           indexPrice: 39538.5,
        #           lastPrice: 39530,
        #           lower24Price: 38633,
        #           maxBidPrice: 43492,
        #           minAskPrice: 35584.5,
        #           riseFallRate: 0.0138,
        #           riseFallValue: 539.5,
        #           symbol: 'BTC_USDT',
        #           timestamp: 1651160401009,
        #           volume24: 125171687
        #         },
        #         symbol: 'BTC_USDT',
        #         ts: 1651160401009
        #       }
        #
        # swap trades
        #     {
        #         "channel":"push.deal",
        #         "data":{
        #             "M":1,
        #             "O":1,
        #             "T":1,
        #             "p":6866.5,
        #             "t":1587442049632,
        #             "v":2096
        #         },
        #         "symbol":"BTC_USDT",
        #         "ts":1587442022003
        #     }
        #
        # spot trades
        #
        #    {
        #        "symbol":"BTC_USDT",
        #        "data":{
        #           "deals":[
        #              {
        #                 "t":1651227552839,
        #                 "p":"39190.01",
        #                 "q":"0.001357",
        #                 "T":2
        #              }
        #           ]
        #        },
        #        "channel":"push.deal"
        #     }
        #
        # spot order
        #     {
        #         symbol: 'LTC_USDT',
        #         data: {
        #           price: 100.25,
        #           quantity: 0.0498,
        #           amount: 4.99245,
        #           remainAmount: 0.01245,
        #           remainQuantity: 0,
        #           remainQ: 0,
        #           remainA: 0,
        #           id: '0b1bf3a33916499f8d1a711a7d5a6fc4',
        #           status: 2,
        #           tradeType: 1,
        #           orderType: 3,
        #           createTime: 1651499416000,
        #           isTaker: 1,
        #           symbolDisplay: 'LTC_USDT',
        #           clientOrderId: ''
        #         },
        #         channel: 'push.personal.order',
        #         eventTime: 1651499416639,
        #         symbol_display: 'LTC_USDT'
        #     }
        #
        if not self.handle_error_message(client, message):
            return
        if message == "pong":
            self.handle_pong(client, message)
            return
        channel = self.safe_string(message, "channel")
        methods = {
            "pong": self.handle_pong,
            "rs.login": self.handle_authenticate,
            "push.deal": self.handle_trades,
            "orderbook": self.handle_order_book,
            "push.kline": self.handle_ohlcv,
            "push.ticker": self.handle_ticker,
            "push.depth": self.handle_order_book,
            "push.limit.depth": self.handle_order_book,
            "push.personal.order": self.handle_order,
            "push.personal.trigger.order": self.handle_order,
            "push.personal.plan.order": self.handle_order,
            "push.personal.order.deal": self.handle_my_trade,
            "push.personal.asset": self.handle_balance,
            "push.funding.rate": self.handle_funding_rate,
        }
        method = self.safe_value(methods, channel)
        if method is not None:
            method(client, message)
