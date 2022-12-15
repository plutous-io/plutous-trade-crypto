from ccxt.pro import bybit

from ..utils import add_preprocess


@add_preprocess
class Bybit(bybit):
    def describe(self):
        return self.deep_extend(
            super(Bybit, self).describe(),
            {
                "plutous_funcs": []
            },
        )
