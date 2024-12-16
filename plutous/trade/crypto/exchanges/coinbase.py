from ccxt.pro import coinbase

from plutous.trade.crypto.utils.paginate import paginate


class Coinbase(coinbase):
    @paginate(max_limit=300)
    async def fetch_ohlcv(
        self,
        symbol,
        timeframe,
        since=None,
        limit=None,
        params={},
    ):
        return await super().fetch_ohlcv(
            symbol,
            timeframe,
            since,
            limit,
            params,
        )
