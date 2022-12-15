from ccxt.pro import bitget

from ..utils import add_preprocess


@add_preprocess
class Bitget(bitget):
    def describe(self):
        return self.deep_extend(
            super(Bitget, self).describe(),
            {
                "plutous_funcs": []
            },
        )
