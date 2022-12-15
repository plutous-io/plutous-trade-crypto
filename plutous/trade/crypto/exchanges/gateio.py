from ccxt.pro import gateio

from ..utils import add_preprocess


@add_preprocess
class GateIO(gateio):
    def describe(self):
        return self.deep_extend(
            super(GateIO, self).describe(),
            {
                "plutous_funcs": []
            },
        )
