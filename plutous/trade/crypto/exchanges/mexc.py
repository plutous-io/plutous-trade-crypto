import asyncio
import hashlib
import json
import time

from ccxt.base.decimal_to_precision import TRUNCATE
from ccxt.base.errors import BadRequest, InvalidOrder
from ccxt.base.types import Entry, FundingRates, Str, Strings
from ccxt.pro import mexc

from plutous.trade.crypto.exchanges.base.errors import OrderFilled, OrderNotCancellable


class Mexc(mexc):
    contract_private_post_order_submit = contractPrivatePostOrderSubmit = Entry(
        "order/create", ["futures", "private"], "POST", {"cost": 2}
    )
    contract_private_post_order_cancel = contractPrivatePostOrderCancel = Entry(
        "order/cancel", ["futures", "private"], "POST", {"cost": 2}
    )
    spot4_private_post_order_place = spot4PrivatePostOrderPlace = Entry(
        "order/place", ["spot4", "private"], "POST", {"cost": 1}
    )
    # userToken used to bypass Mexc Futures Order Maintenance and uses private endpoints
    # The preferred method is definitely to get it by using the MEXC app and using HTTP toolkit as a program to track the requests that your phone makes in MEXC. Because the app authorization stays forever if you open the app once in a while (I think every month once is even enough, maybe even less). Otherwise, you can obtain the authorization from the web which will not last that long so it's not advisable.
    # In all the requests that your app makes, there will be the header Authorization and Authentication that will start with APP. You will copy this string and define it as the authorization.
    # Example:
    # web: "WEBjd982q3jsd8293jsd98123kmd987982yh298fd304yd7734988djs7392uj87328"
    # app: "APPjd982q3jsd8293jsd98123kmd987982yh298fd304yd7734988djs7392uj87328"
    userToken: str | None = None

    def describe(self):
        return self.deep_extend(
            super(Mexc, self).describe(),
            {
                "urls": {
                    "api": {
                        "spot4": {
                            "public": "https://www.mexc.com/api/platform/spot/v4",
                            "private": "https://www.mexc.com/api/platform/spot/v4",
                        },
                        "futures": {
                            "public": "https://futures.mexc.com/api/v1",
                            "private": "https://futures.mexc.com/api/v1/private",
                        },
                    }
                },
                "options": {
                    "unavailableContracts": {
                        "BTC/USDT:USDT": False,
                        "LTC/USDT:USDT": False,
                        "ETH/USDT:USDT": False,
                    },
                },
                "exceptions": {
                    "exact": {
                        "-2011": OrderFilled,
                    }
                },
            },
        )

    def sign(
        self, path, api="public", method="GET", params={}, headers=None, body=None
    ):
        section = self.safe_string(api, 0)
        access = self.safe_string(api, 1)
        path, params = self.resolve_path(path, params)

        if section in ("futures", "spot4"):
            url = (
                self.urls["api"][section][access]
                + "/"
                + self.implode_params(path, params)
            )
            if self.userToken is None:
                raise Exception("Missing user token")
            params = self.omit(params, self.extract_params(path))
            timestamp = str(int(time.time() * 1000))
            concat = f"{self.userToken}{timestamp}"
            partial_hash = hashlib.md5(concat.encode("utf-8")).hexdigest()[7:]
            body = self.json(params)
            sign_param = f"{timestamp}{body}{partial_hash}"
            signature = hashlib.md5(sign_param.encode("utf-8")).hexdigest()
            headers = {
                "x-mxc-nonce": timestamp,
                "x-mxc-sign": signature,
                "authorization": self.userToken,
                "user-agent": "MEXC/7 CFNetwork/1474 Darwin/23.0.0",
                "content-type": "application/json",
                "origin": "https://futures.mexc.com",
                "referer": "https://futures.mexc.com/exchange",
            }
            if section == "spot4":
                headers["origin"] = "https://www.mexc.com"
                headers["referer"] = "https://www.mexc.com/exchange"
            return {"url": url, "method": method, "body": body, "headers": headers}
        return super().sign(path, api, method, params, headers, body)

    def prepare_request_headers(self, headers=None):
        headers = super().prepare_request_headers(headers)
        # Private endpoints dont require the following headers
        if "x-mxc-sign" in headers:
            del headers["User-Agent"]
            del headers["Accept-Encoding"]
        return headers

    def swap_amount_to_precision(self, symbol, amount):
        market = self.market(symbol)
        result = self.decimal_to_precision(
            amount,
            TRUNCATE,
            market["contractSize"],
            self.precisionMode,
            self.paddingMode,
        )
        if result == "0":
            raise InvalidOrder(
                self.id
                + " amount of "
                + market["symbol"]
                + " must be greater than minimum amount precision of "
                + self.number_to_string(market["contractSize"])
            )
        return result

    def create_spot_order_request(
        self, market, type, side, amount, price=None, marginMode=None, params={}
    ):
        symbol = market["symbol"]
        orderSide = side.upper()
        request: dict = {
            "symbol": market["id"],
            "side": orderSide,
            "type": type.upper(),
        }
        request["quantity"] = self.amount_to_precision(symbol, amount)
        if price is not None:
            request["price"] = self.price_to_precision(symbol, price)
        clientOrderId = self.safe_string(params, "clientOrderId")
        if clientOrderId is not None:
            request["newClientOrderId"] = clientOrderId
            params = self.omit(params, ["type", "clientOrderId"])
        if marginMode is not None:
            if marginMode != "isolated":
                raise BadRequest(
                    self.id
                    + " createOrder() does not support marginMode "
                    + marginMode
                    + " for spot-margin trading"
                )
        postOnly = None
        postOnly, params = self.handle_post_only(
            type == "market", type == "LIMIT_MAKER", params
        )
        if postOnly:
            request["type"] = "LIMIT_MAKER"
        return self.extend(request, params)

    async def create_swap_order(
        self, market, type, side, amount, price=None, marginMode=None, params={}
    ):
        await self.load_markets()
        amount = (
            float(
                self.decimal_to_precision(
                    amount,
                    TRUNCATE,
                    market["contractSize"],
                    self.precisionMode,
                    self.paddingMode,
                )
            )
            / market["contractSize"]
        )
        if amount < 1:
            raise InvalidOrder(
                self.id
                + " amount of "
                + market["symbol"]
                + " must be greater than minimum amount precision of "
                + self.number_to_string(market["contractSize"])
            )

        response = await super().create_swap_order(
            market, type, side, amount, price, marginMode, params
        )
        info = json.loads(response["id"].replace("'", '"'))
        response["id"] = self.safe_string(info, "orderId")
        response["timestamp"] = ts = self.safe_integer(info, "ts")
        response["datetime"] = self.iso8601(ts)
        return response

    def parse_trade(self, trade, market=None):
        trade = super().parse_trade(trade, market)
        if market is not None:
            if market.get("contractSize") is not None:
                trade["amount"] = trade["amount"] * market["contractSize"]
        return trade

    async def fetch_my_trades(self, symbol=None, since=None, limit=None, params={}):
        if params.get("orderId") is not None:
            return await self.fetch_order_trades(
                params["orderId"], symbol, since, limit, params
            )
        return await super().fetch_my_trades(symbol, since, limit, params)

    async def cancel_order(self, id: str, symbol: Str = None, params={}):
        try:
            return await super().cancel_order(id, symbol, params)
        except InvalidOrder as e:
            for error in (
                "order does not exist",
                "order state cannot be cancelled",
            ):
                if error in e.args[0]:
                    raise OrderNotCancellable(e.args[0])
                raise OrderNotCancellable(e.args[0])
            raise e

    async def fetch_funding_rates(
        self, symbols: Strings = None, params={}
    ) -> FundingRates:
        markets = await self.load_markets()
        if symbols is None:
            symbols = [symbol for symbol, market in markets.items() if market["swap"]]
        funding_rates = await asyncio.gather(
            *[self.fetch_funding_rate(symbol, params) for symbol in symbols]
        )
        return {rate["symbol"]: rate for rate in funding_rates}


# funding_rates = None

# def describe(self):
#     return self.deep_extend(
#         super(Mexc, self).describe(),
#         {
#             "plutous_funcs": [
#                 "handle_funding_rate",
#                 "watch_funding_rate",
#             ],
#         },
#     )

# async def watch_funding_rate(self, symbol, params={}):
#     """
#     get the live funing rate for a particular symbol
#     :param str symbol: unified symbol of the market to fetch trades for
#     :param dict params: extra parameters specific to the mexc api endpoint
#     :returns [dict]: a list of `trade structures <https://docs.ccxt.com/en/latest/manual.html?#public-trades>`
#     """
#     await self.load_markets()
#     market = self.market(symbol)
#     symbol = market["symbol"]
#     channel = "sub.funding.rate"
#     messageHash = "funding.rate" + ":" + symbol
#     requestParams = {
#         "symbol": market["id"],
#     }
#     return await self.watch_swap_public(messageHash, channel, requestParams, params)

# def handle_funding_rate(self, client, message):
#     # funding rates
#     #     {
#     #         "channel":"push.funding.rate",
#     #         "data":{
#     #             "rate":0.001,
#     #             "symbol":"BTC_USDT"
#     #         },
#     #         "symbol":"BTC_USDT",
#     #         "ts":1587442022003
#     #     }
#     #
#     if self.funding_rates is None:
#         self.funding_rates = dict()
#     data = self.safe_value(message, "data", {})
#     data["fundingRate"] = self.safe_number(data, "rate")
#     data["timestamp"] = self.safe_integer(message, "ts")
#     marketId = self.safe_string(message, "symbol")
#     market = self.safe_market(marketId)
#     symbol = market["symbol"]
#     funding_rate = self.parse_funding_rate(data, market)
#     self.funding_rates[symbol] = funding_rate
#     messageHash = "funding.rate:" + symbol
#     client.resolve(funding_rate, messageHash)
#     return message

# def handle_message(self, client, message):
#     #
#     # spot pong
#     #
#     #  "ping"
#     #
#     # swap pong
#     #  {channel: 'pong', data: 1651570941402, ts: 1651570941402}
#     #
#     # auth spot
#     #
#     #  {channel: 'sub.personal', msg: 'OK'}
#     #
#     # auth swap
#     #
#     #  {channel: 'rs.login', data: 'success', ts: 1651486643082}
#     #
#     # subscription
#     #
#     #  {channel: 'rs.sub.depth', data: 'success', ts: 1651239594401}
#     #
#     # swap ohlcv
#     #     {
#     #         "channel":"push.kline",
#     #         "data":{
#     #             "a":233.740269343644737245,
#     #             "c":6885,
#     #             "h":6910.5,
#     #             "interval":"Min60",
#     #             "l":6885,
#     #             "o":6894.5,
#     #             "q":1611754,
#     #             "symbol":"BTC_USDT",
#     #             "t":1587448800
#     #         },
#     #         "symbol":"BTC_USDT",
#     #         "ts":1587442022003
#     #     }
#     #
#     # swap ticker
#     #     {
#     #         channel: 'push.ticker',
#     #         data: {
#     #           amount24: 491939387.90105,
#     #           ask1: 39530.5,
#     #           bid1: 39530,
#     #           contractId: 10,
#     #           fairPrice: 39533.4,
#     #           fundingRate: 0.00015,
#     #           high24Price: 40310.5,
#     #           holdVol: 187680157,
#     #           indexPrice: 39538.5,
#     #           lastPrice: 39530,
#     #           lower24Price: 38633,
#     #           maxBidPrice: 43492,
#     #           minAskPrice: 35584.5,
#     #           riseFallRate: 0.0138,
#     #           riseFallValue: 539.5,
#     #           symbol: 'BTC_USDT',
#     #           timestamp: 1651160401009,
#     #           volume24: 125171687
#     #         },
#     #         symbol: 'BTC_USDT',
#     #         ts: 1651160401009
#     #       }
#     #
#     # swap trades
#     #     {
#     #         "channel":"push.deal",
#     #         "data":{
#     #             "M":1,
#     #             "O":1,
#     #             "T":1,
#     #             "p":6866.5,
#     #             "t":1587442049632,
#     #             "v":2096
#     #         },
#     #         "symbol":"BTC_USDT",
#     #         "ts":1587442022003
#     #     }
#     #
#     # spot trades
#     #
#     #    {
#     #        "symbol":"BTC_USDT",
#     #        "data":{
#     #           "deals":[
#     #              {
#     #                 "t":1651227552839,
#     #                 "p":"39190.01",
#     #                 "q":"0.001357",
#     #                 "T":2
#     #              }
#     #           ]
#     #        },
#     #        "channel":"push.deal"
#     #     }
#     #
#     # spot order
#     #     {
#     #         symbol: 'LTC_USDT',
#     #         data: {
#     #           price: 100.25,
#     #           quantity: 0.0498,
#     #           amount: 4.99245,
#     #           remainAmount: 0.01245,
#     #           remainQuantity: 0,
#     #           remainQ: 0,
#     #           remainA: 0,
#     #           id: '0b1bf3a33916499f8d1a711a7d5a6fc4',
#     #           status: 2,
#     #           tradeType: 1,
#     #           orderType: 3,
#     #           createTime: 1651499416000,
#     #           isTaker: 1,
#     #           symbolDisplay: 'LTC_USDT',
#     #           clientOrderId: ''
#     #         },
#     #         channel: 'push.personal.order',
#     #         eventTime: 1651499416639,
#     #         symbol_display: 'LTC_USDT'
#     #     }
#     #
#     if not self.handle_error_message(client, message):
#         return
#     if message == "pong":
#         self.handle_pong(client, message)
#         return
#     channel = self.safe_string(message, "channel")
#     methods = {
#         "pong": self.handle_pong,
#         "rs.login": self.handle_authenticate,
#         "push.deal": self.handle_trades,
#         "orderbook": self.handle_order_book,
#         "push.kline": self.handle_ohlcv,
#         "push.ticker": self.handle_ticker,
#         "push.depth": self.handle_order_book,
#         "push.limit.depth": self.handle_order_book,
#         "push.personal.order": self.handle_order,
#         "push.personal.trigger.order": self.handle_order,
#         "push.personal.plan.order": self.handle_order,
#         "push.personal.order.deal": self.handle_my_trade,
#         "push.personal.asset": self.handle_balance,
#         "push.funding.rate": self.handle_funding_rate,
#     }
#     method = self.safe_value(methods, channel)
#     if method is not None:
#         method(client, message)
