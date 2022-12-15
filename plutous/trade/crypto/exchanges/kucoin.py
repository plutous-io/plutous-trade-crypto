from ccxt.pro import kucoin
from ccxt.async_support import kucoinfutures

from ..utils import add_preprocess


@add_preprocess
class Kucoin(kucoin):
    def describe(self):
        return self.deep_extend(
            super(Kucoin, self).describe(),
            {
                "plutous_funcs": []
            },
        )


@add_preprocess
class KucoinFutures(kucoinfutures):
    def describe(self):
        return self.deep_extend(
            super(KucoinFutures, self).describe(),
            {
                "plutous_funcs": []
            },
        )