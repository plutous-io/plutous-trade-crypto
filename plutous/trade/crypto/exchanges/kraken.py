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
        max_interval = self.parse_timeframe(timeframe) * 1000 * 720
        now = self.milliseconds()
        # Kraken only allows 720 bars from the current time
        if since is not None:
            if (now - since) > max_interval:
                raise ValueError(
                    f"Since: {since} is too far. Kraken only allows 720 bars from the current time. "
                )

        return await super().fetch_ohlcv(
            symbol,
            timeframe,
            since,
            limit,
            params,
        )
