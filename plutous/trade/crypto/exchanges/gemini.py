from ccxt.pro import gemini

from plutous.trade.crypto.utils.paginate import paginate


class Gemini(gemini):
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
