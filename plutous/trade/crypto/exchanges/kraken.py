from ccxt.pro import kraken

from plutous.trade.crypto.utils.paginate import paginate


class Kraken(kraken):
    @paginate(max_limit=720)
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
