from ccxt.pro import deribit

from plutous.trade.crypto.utils.paginate import paginate


class Deribit(deribit):
    @paginate(max_limit=5000)
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
