import asyncio

from ccxt.async_support.base.exchange import Exchange
from ccxt.base.types import Entry, FundingRate, FundingRates, Strings


class ImplicitAPI:
    futures_public_get_instruments = futuresPublicGetInstruments = Entry(
        "instruments", ["futures", "public"], "GET", {"cost": 1}
    )
    futures_public_get_funding_rate = futuresPublicGetFundingRate = Entry(
        "fundingRate", ["futures", "public"], "GET", {"cost": 4}
    )


class CoinW(Exchange, ImplicitAPI):
    def describe(self):
        return self.deep_extend(
            super(CoinW, self).describe(),
            {
                "id": "coinw",
                "name": "CoinW",
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
                            "public": "https://api.coinw.sh",
                            "private": "https://api.coinw.sh",
                        },
                        "futures": {
                            "public": "https://api.coinw.com/v1/perpum",
                            "private": "https://api.coinw.com/v1/perpum",
                        },
                    },
                },
                "api": {
                    "futures": {
                        "public": {
                            "get": {
                                "instruments": 1,
                                "fundingRate": 4,
                            },
                        },
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
        assert self.urls is not None
        url = self.urls["api"][section][access] + "/" + path
        if method == "GET":
            to_auth = self.urlencode(params)
            url += "?" + to_auth
        else:
            to_auth = self.json(params) if params else ""
            body = to_auth
        return {"url": url, "method": method, "body": body, "headers": headers}

    async def fetch_markets(self, params={}):
        # {
        #     "code": 0,
        #     "data": [
        #         {
        #             "base": "btc",
        #             "closeSpread": 0.0002,
        #             "commissionRate": 0.0006,
        #             "configBo": {
        #                 "margins": {
        #                     "100": 0.075,
        #                     "5": 0.00375,
        #                     "50": 0.0375,
        #                     "20": 0.015,
        #                     "10": 0.0075,
        #                 },
        #                 "simulatedMargins": {"5": 0.00375, "20": 0.015, "10": 0.0075},
        #             },
        #             "createdDate": 1548950400000,
        #             "defaultLeverage": 20,
        #             "defaultStopLossRate": 0.99,
        #             "defaultStopProfitRate": 100,
        #             "depthPrecision": "0.1,1,10,50,100",
        #             "iconUrl": "https://hkto-prod.oss-accelerate.aliyuncs.com/201810020046047_T9g8i.png",
        #             "id": 1,
        #             "indexId": 1,
        #             "leverage": [5, 10, 20, 50, 100, 125, 200],
        #             "makerFee": "0.0001",
        #             "maxLeverage": 200,
        #             "maxPosition": 20000,
        #             "minLeverage": 1,
        #             "minSize": 1,
        #             "name": "BTC",
        #             "oneLotMargin": 1,
        #             "oneLotSize": 0.001,
        #             "oneMaxPosition": 15000,
        #             "openSpread": 0.0003,
        #             "partitionIds": "2013,2011",
        #             "pricePrecision": 1,
        #             "quote": "usdt",
        #             "selected": 0,
        #             "settledAt": 1741507200000,
        #             "settledPeriod": 8,
        #             "settlementRate": 0.0004,
        #             "sort": 1,
        #             "status": "online",
        #             "stopCrossPositionRate": 0.1,
        #             "stopSurplusRate": 0.01,
        #             "takerFee": "0.0006",
        #             "updatedDate": 1731394149000,
        #         },
        #     ],
        #     "msg": "",
        # }
        response = await self.futuresPublicGetInstruments(params)
        data: list[dict] = self.safe_value(response, "data", [])
        markets = []
        for market in data:
            base = self.safe_string(market, "base").upper()
            quote = self.safe_string(market, "quote").upper()
            symbol = base + "/" + quote + ":" + quote
            id = self.safe_string(market, "id")
            maker_fee = self.safe_string(market, "makerFee")
            taker_fee = self.safe_string(market, "takerFee")
            min_size = self.safe_number(market, "minSize")
            price_precision = self.safe_number(market, "pricePrecision")
            status = self.safe_string(market, "status")
            oneLotSize = self.safe_number(market, "oneLotSize")
            markets.append(
                {
                    "id": id,
                    "symbol": symbol,
                    "base": base,
                    "quote": quote,
                    "settle": quote,
                    "baseId": base,
                    "quoteId": quote,
                    "settleId": quote,
                    "maker": maker_fee,
                    "taker": taker_fee,
                    "type": "swap",
                    "spot": False,
                    "margin": False,
                    "swap": True,
                    "future": True,
                    "option": False,
                    "active": status == "online",
                    "contract": True,
                    "linear": True,
                    "inverse": False,
                    "contractSize": oneLotSize,
                    "expiry": None,
                    "expiryDatetime": None,
                    "strike": None,
                    "optionType": None,
                    "precision": {
                        "price": price_precision,
                        "amount": None,
                    },
                    "limits": {
                        "amount": {
                            "min": min_size,
                            "max": None,
                        },
                        "price": {
                            "min": None,
                            "max": None,
                        },
                        "leverage": {
                            "min": self.safe_float(market, "minLeverage"),
                            "max": self.safe_float(market, "maxLeverage"),
                        },
                        "cost": {
                            "min": None,
                            "max": None,
                        },
                    },
                    "created": None,
                    "info": market,
                }
            )
        return markets

    async def fetch_funding_rate(self, symbol: str, params={}) -> FundingRate:
        # {
        #     "code":0,
        #     "data":{
        #         "value":0.0001
        #     },
        #     "msg":""
        # }
        await self.load_markets()
        market = self.market(symbol)
        base = self.safe_string(market, "base").lower()
        response = await self.futuresPublicGetFundingRate({"instrument": base})
        data: dict = self.safe_value(response, "data", {})
        fundingRate = self.safe_number(data, "value")
        info = self.safe_value(market, "info", {})
        settledAt = self.safe_integer(info, "settledAt")
        settledPeriod = self.safe_integer(info, "settledPeriod")
        interval = str(settledPeriod) + "h"
        return {
            "info": data,
            "symbol": symbol,
            "markPrice": None,
            "indexPrice": None,
            "interestRate": None,
            "estimatedSettlePrice": None,
            "timestamp": self.milliseconds(),
            "datetime": self.iso8601(self.milliseconds()),
            "fundingRate": fundingRate,
            "fundingTimestamp": settledAt,
            "fundingDatetime": self.iso8601(settledAt),
            "nextFundingRate": None,
            "nextFundingTimestamp": None,
            "nextFundingDatetime": None,
            "previousFundingRate": None,
            "previousFundingTimestamp": None,
            "previousFundingDatetime": None,
            "interval": interval,
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
