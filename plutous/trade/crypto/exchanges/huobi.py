from ccxt.pro import huobi

from ..utils import add_preprocess


@add_preprocess
class Huobi(huobi):
    def describe(self):
        return self.deep_extend(
            super(Huobi, self).describe(),
            {
                "plutous_funcs": []
            },
        )
