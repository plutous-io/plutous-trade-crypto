from ccxt.base.errors import BadSymbol
from ccxt.pro import phemex


class Phemex(phemex):
    def describe(self):
        return self.deep_extend(
            super().describe(),
            {
                "urls": {"api": {"v2": "https://{hostname}"}},
                "api": {
                    "v2": {
                        "get": [
                            "md/v2/ticker/24hr",  # ?symbol=<symbol>&id=<id>
                            "md/v2/ticker/24hr/all",  # ?id=<id>
                        ]
                    }
                },
            },
        )

    async def fetch_funding_rate(self, symbol, params={}):
        """
        fetch the current funding rate
        :param str symbol: unified market symbol
        :param dict params: extra parameters specific to the phemex api endpoint
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
        info = self.safe_value(market, "info", {})
        type = self.safe_string_lower(info, "type")
        if type == "perpetual":
            response = await self.v1GetMdTicker24hr(self.extend(request, params))
        else:
            response = await self.v2GetMdV2Ticker24hr(self.extend(request, params))
        #
        #     {
        #         "error": null,
        #         "id": 0,
        #         "result": {
        #             "askEp": 2332500,
        #             "bidEp": 2331000,
        #             "fundingRateEr": 10000,
        #             "highEp": 2380000,
        #             "indexEp": 2329057,
        #             "lastEp": 2331500,
        #             "lowEp": 2274000,
        #             "markEp": 2329232,
        #             "openEp": 2337500,
        #             "openInterest": 1298050,
        #             "predFundingRateEr": 19921,
        #             "symbol": "ETHUSD",
        #             "timestamp": 1592474241582701416,
        #             "turnoverEv": 47228362330,
        #             "volume": 4053863
        #         }
        #     }
        #
        result = self.safe_value(response, "result", {})
        return self.parse_funding_rate(result, market)
