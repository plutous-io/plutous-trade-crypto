from ccxt.pro import mexc

from ..utils import add_preprocess


@add_preprocess
class Mexc(mexc):
    def describe(self):
        return self.deep_extend(
            super(Mexc, self).describe(),
            {
                "plutous_funcs": []
            },
        )
