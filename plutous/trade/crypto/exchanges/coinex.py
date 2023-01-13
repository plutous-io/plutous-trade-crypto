from ccxt.pro.coinex import coinex
from ccxt.base.errors import BadSymbol


class CoinEx(coinex):
    async def fetch_funding_rate(self, symbol, params={}):
        """
        fetch the current funding rate
        :param str symbol: unified market symbol
        :param dict params: extra parameters specific to the coinex api endpoint
        :returns dict: a `funding rate structure <https://docs.ccxt.com/en/latest/manual.html#funding-rate-structure>`
        """
        await self.load_markets()
        market = self.market(symbol)
        if not market['swap']:
            raise BadSymbol(self.id + ' fetchFundingRate() supports swap contracts only')
        request = {
            'market': market['id'],
        }
        response = await self.perpetualPublicGetMarketTicker(self.extend(request, params))
        #
        #     {
        #          "code": 0,
        #         "data":
        #         {
        #             "date": 1650678472474,
        #             "ticker": {
        #                 "vol": "6090.9430",
        #                 "low": "39180.30",
        #                 "open": "40474.97",
        #                 "high": "40798.01",
        #                 "last": "39659.30",
        #                 "buy": "39663.79",
        #                 "period": 86400,
        #                 "funding_time": 372,
        #                 "position_amount": "270.1956",
        #                 "funding_rate_last": "0.00022913",
        #                 "funding_rate_next": "0.00013158",
        #                 "funding_rate_predict": "0.00016552",
        #                 "insurance": "16045554.83969682659674035672",
        #                 "sign_price": "39652.48",
        #                 "index_price": "39648.44250000",
        #                 "sell_total": "22.3913",
        #                 "buy_total": "19.4498",
        #                 "buy_amount": "12.8942",
        #                 "sell": "39663.80",
        #                 "sell_amount": "0.9388"
        #             }
        #         },
        #         "message": "OK"
        #     }
        #
        data = self.safe_value(response, 'data', {})
        ticker = self.safe_value(data, 'ticker', {})
        timestamp = self.safe_integer(data, 'date')
        return self.parse_funding_rate(ticker, market, timestamp)

    def parse_funding_rate(self, contract, market=None, timestamp=None):
        #
        # fetchFundingRate
        #
        #     {
        #         "vol": "6090.9430",
        #         "low": "39180.30",
        #         "open": "40474.97",
        #         "high": "40798.01",
        #         "last": "39659.30",
        #         "buy": "39663.79",
        #         "period": 86400,
        #         "funding_time": 372,
        #         "position_amount": "270.1956",
        #         "funding_rate_last": "0.00022913",
        #         "funding_rate_next": "0.00013158",
        #         "funding_rate_predict": "0.00016552",
        #         "insurance": "16045554.83969682659674035672",
        #         "sign_price": "39652.48",
        #         "index_price": "39648.44250000",
        #         "sell_total": "22.3913",
        #         "buy_total": "19.4498",
        #         "buy_amount": "12.8942",
        #         "sell": "39663.80",
        #         "sell_amount": "0.9388"
        #     }
        #
        fundingDelta = self.safe_integer(contract, 'funding_time') * 60 * 1000
        fundingHour = (timestamp + fundingDelta) / 3600000
        fundingTimestamp = int(round(fundingHour)) * 3600000
        return {
            'info': contract,
            'symbol': self.safe_symbol(None, market),
            'markPrice': self.safe_number(contract, 'sign_price'),
            'indexPrice': self.safe_number(contract, 'index_price'),
            'interestRate': None,
            'estimatedSettlePrice': None,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'fundingRate': self.safe_number(contract, 'funding_rate_next'),
            'fundingTimestamp': fundingTimestamp,
            'fundingDatetime': self.iso8601(fundingTimestamp),
            'nextFundingRate': self.safe_number(contract, 'funding_rate_predict'),
            'nextFundingTimestamp': None,
            'nextFundingDatetime': None,
            'previousFundingRate': self.safe_number(contract, 'funding_rate_last'),
            'previousFundingTimestamp': None,
            'previousFundingDatetime': None,
        }

    async def fetch_funding_rates(self, symbols=None, params={}):
        """
         *  @method
        fetch the current funding rates
        :param array symbols: unified market symbols
        :param dict params: extra parameters specific to the coinex api endpoint
        :returns array: an array of `funding rate structures <https://docs.ccxt.com/en/latest/manual.html#funding-rate-structure>`
        """
        await self.load_markets()
        symbols = self.market_symbols(symbols)
        market = None
        if symbols is not None:
            symbol = self.safe_value(symbols, 0)
            market = self.market(symbol)
            if not market['swap']:
                raise BadSymbol(self.id + ' fetchFundingRates() supports swap contracts only')
        response = await self.perpetualPublicGetMarketTickerAll(params)
        #
        #     {
        #         "code": 0,
        #         "data":
        #         {
        #             "date": 1650678472474,
        #             "ticker": {
        #                 "BTCUSDT": {
        #                     "vol": "6090.9430",
        #                     "low": "39180.30",
        #                     "open": "40474.97",
        #                     "high": "40798.01",
        #                     "last": "39659.30",
        #                     "buy": "39663.79",
        #                     "period": 86400,
        #                     "funding_time": 372,
        #                     "position_amount": "270.1956",
        #                     "funding_rate_last": "0.00022913",
        #                     "funding_rate_next": "0.00013158",
        #                     "funding_rate_predict": "0.00016552",
        #                     "insurance": "16045554.83969682659674035672",
        #                     "sign_price": "39652.48",
        #                     "index_price": "39648.44250000",
        #                     "sell_total": "22.3913",
        #                     "buy_total": "19.4498",
        #                     "buy_amount": "12.8942",
        #                     "sell": "39663.80",
        #                     "sell_amount": "0.9388"
        #                 }
        #             }
        #         },
        #         "message": "OK"
        #     }
        data = self.safe_value(response, 'data', {})
        tickers = self.safe_value(data, 'ticker', {})
        timestamp = self.safe_integer(data, 'date')
        result = []
        marketIds = list(tickers.keys())
        for i in range(0, len(marketIds)):
            marketId = marketIds[i]
            if marketId.find('_') == -1:  # skip _signprice and _indexprice
                market = self.safe_market(marketId, None, None, 'swap')
                ticker = tickers[marketId]
                result.append(self.parse_funding_rate(ticker, market, timestamp))
        return self.filter_by_array(result, 'symbol', symbols)
