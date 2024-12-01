from ccxt.pro import bitmex

from plutous.trade.crypto.utils.paginate import paginate


class Bitmex(bitmex):
    @paginate(max_limit=1000)
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
