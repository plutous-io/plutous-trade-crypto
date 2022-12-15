from ccxt.pro import okx

from ..utils import add_preprocess


@add_preprocess
class Okx(okx):
    def describe(self):
        return self.deep_extend(
            super(Okx, self).describe(),
            {
                "plutous_funcs": []
            },
        )
