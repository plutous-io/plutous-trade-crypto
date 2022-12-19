from ccxt.pro import kucoin
from ccxt.async_support import kucoinfutures


class Kucoin(kucoin):
    def describe(self):
        return self.deep_extend(
            super(Kucoin, self).describe(),
            {"plutous_funcs": []},
        )


class KucoinFutures(kucoinfutures):
    def describe(self):
        return self.deep_extend(
            super(KucoinFutures, self).describe(),
            {"plutous_funcs": []},
        )
