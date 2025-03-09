import asyncio
import hashlib
import random
import string
import time

from ccxt.async_support.base.exchange import Exchange
from ccxt.base.types import Entry, FundingRate, FundingRates, Market, Strings


class ImplicitAPI:
    spot_public_get_market_last_price = spotPublicGetMarketLastPrice = Entry(
        "market/last_price", ["spot", "public"], "GET", {"cost": 1}
    )
    spot_public_get_market_depth = spotPublicGetMarketDepth = Entry(
        "market/depth", ["spot", "public"], "GET", {"cost": 1}
    )
    spot_public_get_market_kline = spotPublicGetMarketKline = Entry(
        "market/kline", ["spot", "public"], "GET", {"cost": 1}
    )
    spot_public_get_market_kline_history = spotPublicGetMarketKlineHistory = Entry(
        "market/kline/history", ["spot", "public"], "GET", {"cost": 1}
    )
    spot_public_get_common_coin_pair_list = spotPublicGetCommonCoinPairList = Entry(
        "common/coin_pair/list", ["spot", "public"], "GET", {"cost": 1}
    )
    spot_public_get_common_rate_list = spotPublicGetCommonRateList = Entry(
        "common/rate/list", ["spot", "public"], "GET", {"cost": 1}
    )
    spot_public_get_common_coin_coin_network_list = (
        spotPublicGetCommonCoinCoinNetworkList
    ) = Entry("common/coin/coin_network/list", ["spot", "public"], "GET", {"cost": 1})
    spot_private_get_user_account = spotPrivateGetUserAccount = Entry(
        "user/account", ["spot", "private"], "GET", {"cost": 1}
    )
    spot_private_get_order_deal_list = spotPrivateGetOrderDealList = Entry(
        "order/deal/list", ["spot", "private"], "GET", {"cost": 1}
    )
    spot_private_get_order_history_page = spotPrivateGetOrderHistoryPage = Entry(
        "order/history/page", ["spot", "private"], "GET", {"cost": 1}
    )
    spot_private_get_order_pending_list = spotPrivateGetOrderPendingList = Entry(
        "order/pending/list", ["spot", "private"], "GET", {"cost": 1}
    )
    spot_private_post_order_place_order = spotPrivatePostOrderPlaceOrder = Entry(
        "order/place_order", ["spot", "private"], "POST", {"cost": 1}
    )
    spot_private_post_order_place_order_batch = spotPrivatePostOrderPlaceOrderBatch = (
        Entry("order/place_order/batch", ["spot", "private"], "POST", {"cost": 1})
    )
    spot_private_post_order_cancel = spotPrivatePostOrderCancel = Entry(
        "order/cancel", ["spot", "private"], "POST", {"cost": 1}
    )
    futures_public_get_market_symbol_base_info = (
        futuresPublicGetMarketSymbolBaseInfo
    ) = Entry("market/symbol/baseInfo", ["futures", "public"], "GET", {"cost": 1})
    futures_public_get_market_depth = futuresPublicGetMarketDepth = Entry(
        "market/depth", ["futures", "public"], "GET", {"cost": 1}
    )
    futures_public_get_market_funding_rate = futuresPublicGetMarketFundingRate = Entry(
        "market/funding_rate", ["futures", "public"], "GET", {"cost": 1}
    )
    futures_public_get_market_kline = futuresPublicGetMarketKline = Entry(
        "market/kline", ["futures", "public"], "GET", {"cost": 1}
    )
    futures_public_get_market_tickers = futuresPublicGetMarkerTickers = Entry(
        "market/tickers", ["futures", "public"], "GET", {"cost": 1}
    )
    futures_public_get_market_trading_pairs = futuresPublicGetMarketTradingPairs = (
        Entry("market/trading_pairs", ["futures", "public"], "GET", {"cost": 1})
    )
    futures_private_get_account_get_leverage_margin_mode = (
        futuresPrivateGetAccountGetLeverageMarginMode
    ) = Entry(
        "account/get_leverage_margin_mode", ["futures", "private"], "GET", {"cost": 1}
    )
    futures_private_get_account = futuresPrivateGetAccount = Entry(
        "account", ["futures", "private"], "GET", {"cost": 1}
    )
    futures_private_get_position_get_history_positions = (
        futuresPrivateGetPositionGetHistoryPositions
    ) = Entry(
        "position/get_history_positions", ["futures", "private"], "GET", {"cost": 1}
    )
    futures_private_get_position_get_pending_positions = (
        futuresPrivateGetPositionGetPendingPositions
    ) = Entry(
        "position/get_pending_positions", ["futures", "private"], "GET", {"cost": 1}
    )
    futures_private_get_position_get_position_tiers = (
        futuresPrivateGetPositionGetPositionTiers
    ) = Entry("position/get_position_tiers", ["futures", "private"], "GET", {"cost": 1})
    futures_private_get_tpsl_get_history_orders = (
        futuresPrivateGetTpslGetHistoryOrders
    ) = Entry("tpsl/get_history_orders", ["futures", "private"], "GET", {"cost": 1})
    futures_private_get_tpsl_get_pending_orders = (
        futuresPrivateGetTpslGetPendingOrders
    ) = Entry("tpsl/get_pending_orders", ["futures", "private"], "GET", {"cost": 1})
    futures_private_get_trade_get_history_orders = (
        futuresPrivateGetTradeGetHistoryOrders
    ) = Entry("trade/get_history_orders", ["futures", "private"], "GET", {"cost": 1})
    futures_private_get_trade_get_history_trades = (
        futuresPrivateGetTradeGetHistoryTrades
    ) = Entry("trade/get_history_trades", ["futures", "private"], "GET", {"cost": 1})
    futures_private_get_trade_get_order_detail = (
        futuresPrivateGetTradeGetOrderDetail
    ) = Entry("trade/get_order_detail", ["futures", "private"], "GET", {"cost": 1})
    futures_private_get_trade_get_pending_orders = (
        futuresPrivateGetTradeGetPendingOrders
    ) = Entry("trade/get_pending_orders", ["futures", "private"], "GET", {"cost": 1})
    futures_private_post_account_adjust_position_margin = (
        futuresPrivatePostAccountAdjustPositionMargin
    ) = Entry(
        "account/adjust_position_margin", ["futures", "private"], "POST", {"cost": 2}
    )
    futures_private_post_account_change_leverage = (
        futuresPrivatePostAccountChangeLeverage
    ) = Entry("account/change_leverage", ["futures", "private"], "POST", {"cost": 1})
    futures_private_post_account_change_margin_mode = (
        futuresPrivatePostAccountChangeMarginMode
    ) = Entry("account/change_margin_mode", ["futures", "private"], "POST", {"cost": 1})
    futures_private_post_account_change_position_mode = (
        futuresPrivatePostAccountChangePositionMode
    ) = Entry(
        "account/change_position_mode", ["futures", "private"], "POST", {"cost": 1}
    )
    futures_private_post_tpsl_cancel_order = futuresPrivatePostTpslCancelOrder = Entry(
        "tpsl/cancel_order", ["futures", "private"], "POST", {"cost": 1}
    )
    futures_private_post_tpsl_position_modify_order = (
        futuresPrivatePostTpslPositionModifyOrder
    ) = Entry("tpsl/position/modify_order", ["futures", "private"], "POST", {"cost": 1})
    futures_private_post_tpsl_modify_order = futuresPrivatePostTpslModifyOrder = Entry(
        "tpsl/modify_order", ["futures", "private"], "POST", {"cost": 1}
    )
    futures_private_post_tpsl_position_place_order = (
        futuresPrivatePostTpslPositionPlaceOrder
    ) = Entry("tpsl/position/place_order", ["futures", "private"], "POST", {"cost": 1})
    futures_private_post_tpsl_place_order = futuresPrivatePostTpslPlaceOrder = Entry(
        "tpsl/place_order", ["futures", "private"], "POST", {"cost": 1}
    )
    futures_private_post_trade_batch_order = futuresPrivatePostTradeBatchOrder = Entry(
        "trade/batch_order", ["futures", "private"], "POST", {"cost": 2}
    )
    futures_private_post_trade_cancel_all_orders = (
        futuresPrivatePostTradeCancelAllOrders
    ) = Entry("trade/cancel_all_orders", ["futures", "private"], "POST", {"cost": 1})
    futures_private_post_trade_cancel_orders = futuresPrivatePostTradeCancelOrders = (
        Entry("trade/cancel_orders", ["futures", "private"], "POST", {"cost": 2})
    )
    futures_private_post_trade_close_all_position = (
        futuresPrivatePostTradeCloseAllPosition
    ) = Entry("trade/close_all_position", ["futures", "private"], "POST", {"cost": 10})
    futures_private_post_trade_flash_close_position = (
        futuresPrivatePostTradeFlashClosePosition
    ) = Entry("trade/flash_close_position", ["futures", "private"], "POST", {"cost": 2})
    futures_private_post_trade_modify_order = futuresPrivatePostTradeModifyOrder = (
        Entry("trade/modify_order", ["futures", "private"], "POST", {"cost": 1})
    )
    futures_private_post_trade_place_order = futuresPrivatePostTradePlaceOrder = Entry(
        "trade/place_order", ["futures", "private"], "POST", {"cost": 1}
    )
    futures_v2_public_get_market_symbol_base_info = (
        futuresV2PublicGetMarketSymbolBaseInfo
    ) = Entry("market/symbol/baseInfo", ["futuresV2", "public"], "GET", {"cost": 1})


class Bitunix(Exchange, ImplicitAPI):

    def describe(self):
        return self.deep_extend(
            super(Bitunix, self).describe(),
            {
                "id": "bitunix",
                "name": "Bitunix",
                "countries": ["US"],  # Example country
                "rateLimit": 100,  # default rate limit is 10 times per second
                "certified": False,
                "pro": False,
                "has": {
                    "CORS": None,
                    "spot": True,
                    "margin": False,
                    "swap": False,
                    "future": False,
                    "option": False,
                },
                "urls": {
                    "logo": "https://example.com/logo.jpg",
                    "api": {
                        "spot": {
                            "public": "https://openapi.bitunix.com/api/spot/v1",
                            "private": "https://openapi.bitunix.com/api/spot/v1",
                        },
                        "futures": {
                            "public": "https://fapi.bitunix.com/api/v1/futures",
                            "private": "https://fapi.bitunix.com/api/v1/futures",
                        },
                        "futuresV2": {
                            "public": "https://api.bitunix.com/futures/futures",
                        },
                    },
                    "www": "https://www.bitunix.com",
                    "doc": "https://docs.bitunix.com",
                    "fees": "https://www.bitunix.com/fees",
                },
                "api": {
                    "spot": {
                        "public": {
                            "get": {
                                "market/last_price": 1,
                                "market/depth": 1,
                                "market/kline": 1,
                                "market/kline/history": 1,
                                "common/coin_pair/list": 1,
                                "common/rate/list": 1,
                                "common/coin/coin_network/list": 1,
                            },
                        },
                        "private": {
                            "get": {
                                "user/account": 1,
                                "order/deal/list": 1,
                                "order/history/page": 1,
                                "order/pending/list": 1,
                            },
                            "post": {
                                "order/place_order": 1,
                                "order/place_order/batch": 1,
                                "order/cancel": 1,
                            },
                        },
                    },
                    "futures": {
                        "public": {
                            "get": {
                                "market/symbol/baseInfo": 1,
                                "market/depth": 1,
                                "market/funding_rate": 1,
                                "market/kline": 1,
                                "market/tickers": 1,
                                "market/trading_pairs": 1,
                            },
                        },
                        "private": {
                            "get": {
                                "account/get_leverage_margin_mode": 1,
                                "account": 1,
                                "position/get_history_positions": 1,
                                "position/get_pending_positions": 1,
                                "position/get_position_tiers": 1,
                                "tpsl/get_history_orders": 1,
                                "tpsl/get_pending_orders": 1,
                                "trade/get_history_orders": 1,
                                "trade/get_history_trades": 1,
                                "trade/get_order_detail": 1,
                                "trade/get_pending_orders": 1,
                            },
                            "post": {
                                "account/adjust_position_margin": 2,
                                "account/change_leverage": 1,
                                "account/change_margin_mode": 1,
                                "account/change_position_mode": 1,
                                "tpsl/cancel_order": 1,
                                "tpsl/position/modify_order": 1,
                                "tpsl/modify_order": 1,
                                "tpsl/position/place_order": 1,
                                "tpsl/place_order": 1,
                                "trade/batch_order": 2,
                                "trade/cancel_all_orders": 1,
                                "trade/cancel_orders": 2,
                                "trade/close_all_position": 10,
                                "trade/flash_close_position": 2,
                                "trade/modify_order": 1,
                                "trade/place_order": 1,
                            },
                        },
                    },
                    "futuresV2": {
                        "public": {
                            "get": {
                                "market/symbol/baseInfo": 1,
                            },
                        },
                    },
                },
            },
        )

    def sign(
        self, path, api="public", method="GET", params={}, headers=None, body=None
    ):
        section = self.safe_string(api, 0)
        access = self.safe_string(api, 1)
        path, params = self.resolve_path(path, params)
        assert self.urls is not None
        url = self.urls["api"][section][access] + "/" + path
        if method == "GET":
            to_auth = self.urlencode(params)
            url += "?" + to_auth
        else:
            to_auth = self.json(params) if params else ""
            body = to_auth
        if access == "private":
            self.check_required_credentials()
            nonce = "".join(random.choices(string.ascii_letters + string.digits, k=32))
            timestamp = str(int(time.time() * 1000))
            digest_input = nonce + timestamp + self.apiKey + to_auth
            signature = self.hmac(
                self.encode(digest_input), self.encode(self.secret), hashlib.sha256
            )
            headers = {
                "api-key": self.apiKey,
                "nonce": nonce,
                "timestamp": timestamp,
                "sign": signature,
                "Content-Type": "application/json",
            }
        return {"url": url, "method": method, "body": body, "headers": headers}

    async def fetch_markets(self, params={}) -> list[Market]:

        spotMarketPromise = self.fetch_spot_markets(params)
        swapMarketPromise = self.fetch_swap_markets(params)
        spotMarket, swapMarket = await asyncio.gather(
            *[spotMarketPromise, swapMarketPromise]
        )
        return self.array_concat(spotMarket, swapMarket)

    async def fetch_spot_markets(self, params={}):
        # {
        #     "code": "0",
        #     "msg": "result.success",
        #     "data": [
        #         {
        #             "id": 1,
        #             "symbol": "btcusdt",
        #             "base": "BTC",
        #             "baseIcon": "https://bitunix-public.oss-ap-northeast-1.aliyuncs.com/config/kv/227307.png",
        #             "quote": "USDT",
        #             "quoteIcon": "https://bitunix-public.oss-ap-northeast-1.aliyuncs.com/config/coin/USDT.png",
        #             "basePrecision": 5,
        #             "quotePrecision": 2,
        #             "minPrice": "10.0000000000000000",
        #             "minVolume": "0.0000500000000000",
        #             "maxAmount": "500000.0000000000000000",
        #             "maxSlippage": "0.0500",
        #             "premiumFactor": "0.0500",
        #             "isOpen": 1,
        #             "isHot": 1,
        #             "isRecommend": 1,
        #             "isShow": 1,
        #             "tradeArea": "USDT",
        #             "sort": 1,
        #             "openTime": None,
        #             "ctime": "2023-05-12T18:03:08Z",
        #             "precisions": [
        #                 "0.0100000000000000",
        #                 "0.1000000000000000",
        #                 "1.0000000000000000",
        #                 "10.0000000000000000",
        #                 "100.0000000000000000",
        #             ],
        #         },
        #     ],
        # }
        response = await self.spotPublicGetCommonCoinPairList(params)
        data: list[dict] = self.safe_value(response, "data", [])
        result = []
        for market in data:
            id = self.safe_string(market, "symbol")
            baseId = self.safe_string(market, "base")
            quoteId = self.safe_string(market, "quote")
            base = self.safe_currency_code(baseId)
            quote = self.safe_currency_code(quoteId)
            status = self.safe_integer(market, "isOpen")
            result.append(
                {
                    "id": id,
                    "symbol": base + "/" + quote,
                    "base": base,
                    "quote": quote,
                    "settle": None,
                    "baseId": baseId,
                    "quoteId": quoteId,
                    "settleId": None,
                    "type": "spot",
                    "spot": True,
                    "margin": False,
                    "swap": False,
                    "future": False,
                    "option": False,
                    "active": status == 1,
                    "contract": False,
                    "linear": False,
                    "inverse": False,
                    "taker": None,
                    "maker": None,
                    "contractSize": None,
                    "expiry": None,
                    "expiryDatetime": None,
                    "strike": None,
                    "optionType": None,
                    "precision": {
                        "price": self.safe_integer(market, "quotePrecision"),
                        "amount": self.safe_integer(market, "basePrecision"),
                    },
                    "limits": {
                        "amount": {
                            "min": self.safe_float(market, "minVolume"),
                            "max": self.safe_float(market, "maxAmount"),
                        },
                        "price": {
                            "min": self.safe_float(market, "minPrice"),
                            "max": None,
                        },
                        "leverage": {
                            "min": None,
                            "max": None,
                        },
                        "cost": {
                            "min": None,
                            "max": None,
                        },
                        "created": None,
                        "info": market,
                    },
                }
            )
        return result

    async def fetch_swap_markets(self, params={}):
        # {
        #     "code": 0,
        #     "data": [
        #         {
        #             "symbol": "BTCUSDT",
        #             "base": "BTC",
        #             "quote": "USDT",
        #             "minTradeVolume": "0.001",
        #             "minBuyPriceOffset": "-0.95",
        #             "maxSellPriceOffset": "100",
        #             "maxLimitOrderVolume": "1000",
        #             "maxMarketOrderVolume": "120",
        #             "basePrecision": 4,
        #             "quotePrecision": 1,
        #             "maxLeverage": 125,
        #             "minLeverage": 1,
        #             "defaultLeverage": 20,
        #             "defaultMarginMode": "2",
        #             "priceProtectScope": None,
        #             "symbolStatus": "OPEN",
        #         },
        #     ],
        # }
        response = await self.futuresPublicGetMarketTradingPairs(params)
        data: list[dict] = self.safe_value(response, "data", [])
        result = []
        for market in data:
            id = self.safe_string(market, "symbol")
            baseId = self.safe_string(market, "base")
            quoteId = self.safe_string(market, "quote")
            base = self.safe_currency_code(baseId)
            quote = self.safe_currency_code(quoteId)
            status = self.safe_string(market, "symbolStatus")
            result.append(
                {
                    "id": id,
                    "symbol": base + "/" + quote + ":" + quote,
                    "base": base,
                    "quote": quote,
                    "settle": quote,
                    "baseId": baseId,
                    "quoteId": quoteId,
                    "settleId": quoteId,
                    "type": "swap",
                    "spot": False,
                    "margin": False,
                    "swap": True,
                    "future": False,
                    "option": False,
                    "active": status == "OPEN",
                    "contract": True,
                    "linear": True,
                    "inverse": False,
                    "taker": None,
                    "maker": None,
                    "contractSize": None,
                    "expiry": None,
                    "expiryDatetime": None,
                    "strike": None,
                    "optionType": None,
                    "precision": {
                        "price": self.safe_integer(market, "quotePrecision"),
                        "amount": self.safe_integer(market, "basePrecision"),
                    },
                    "limits": {
                        "amount": {
                            "min": self.safe_float(market, "minTradeVolume"),
                            "max": self.safe_float(market, "maxLimitOrderVolume"),
                        },
                        "price": {
                            "min": self.safe_float(market, "minBuyPriceOffset"),
                            "max": self.safe_float(market, "maxSellPriceOffset"),
                        },
                        "leverage": {
                            "min": self.safe_float(market, "minLeverage"),
                            "max": self.safe_float(market, "maxLeverage"),
                        },
                        "cost": {
                            "min": None,
                            "max": None,
                        },
                        "created": None,
                        "info": market,
                    },
                }
            )
        return result

    async def fetch_funding_rate(self, symbol: str, params={}) -> FundingRate:
        # {
        #     "code": 0,
        #     "data": {
        #         "symbol": "BTCUSDT",
        #         "base": "BTC",
        #         "baseCoin": "BTC",
        #         "quote": "USDT",
        #         "type": "Futures Account",
        #         "marginCoinSymbol": "USDT",
        #         "minBaseAmount": "0.001",
        #         "fundingRateNext": "0.00001247",
        #         "maxLeverage": 125,
        #         "fundingTimes": ["00:00:00", "08:00:00", "16:00:00"],
        #         "indexSources": ["bybit", "binance", "bitget"],
        #         "amount": "45993.7335",
        #     },
        #     "msg": "Success",
        # }
        await self.load_markets()
        market = self.market(symbol)
        request: dict = {
            "symbol": market["id"],
        }
        response = await self.futuresV2PublicGetMarketSymbolBaseInfo(request)
        result = self.safe_value(response, "data", {})
        return self.parse_funding_rate(result, market)

    def parse_funding_rate(self, contract, market: Market = None) -> FundingRate:
        # {
        #     "symbol": "BTCUSDT",
        #     "base": "BTC",
        #     "baseCoin": "BTC",
        #     "quote": "USDT",
        #     "type": "Futures Account",
        #     "marginCoinSymbol": "USDT",
        #     "minBaseAmount": "0.001",
        #     "fundingRateNext": "0.00001247",
        #     "maxLeverage": 125,
        #     "fundingTimes": ["00:00:00", "08:00:00", "16:00:00"],
        #     "indexSources": ["bybit", "binance", "bitget"],
        #     "amount": "45993.7335",
        # },
        nextFundingRate = self.safe_number(contract, "fundingRateNext")
        markerId = self.safe_string(contract, "symbol")
        symbol = self.safe_symbol(markerId, market, None, "contract")
        fundingTimes: list[str] = self.safe_value(contract, "fundingTimes", [])
        interval = int(24 / len(fundingTimes))
        intervalString = str(interval) + "h"
        intervalMillsecond = interval * 60 * 60 * 1000
        fundingTimestamp = (
            (self.milliseconds() // intervalMillsecond) + 1
        ) * intervalMillsecond
        fundingDatetime = self.iso8601(fundingTimestamp)
        return {
            "info": contract,
            "symbol": symbol,
            "markPrice": None,
            "indexPrice": None,
            "interestRate": None,
            "estimatedSettlePrice": None,
            "timestamp": self.milliseconds(),
            "datetime": self.iso8601(self.milliseconds()),
            "fundingRate": nextFundingRate,
            "fundingTimestamp": fundingTimestamp,
            "fundingDatetime": fundingDatetime,
            "nextFundingRate": None,
            "nextFundingTimestamp": None,
            "nextFundingDatetime": None,
            "previousFundingRate": None,
            "previousFundingTimestamp": None,
            "previousFundingDatetime": None,
            "interval": intervalString,
        }

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
