from ccxt.base.types import FundingRate, Market
from ccxt.pro import hyperliquid


class Hyperliquid(hyperliquid):
    def parse_funding_rate(self, info, market: Market = None) -> FundingRate:
        fr = super().parse_funding_rate(info, market)
        fr["timestamp"] = self.milliseconds()
        fr["datetime"] = self.iso8601(fr["timestamp"])
        return fr
