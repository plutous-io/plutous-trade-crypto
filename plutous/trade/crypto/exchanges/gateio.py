from ccxt.pro import gateio


class GateIO(gateio):
    def describe(self):
        return self.deep_extend(
            super(GateIO, self).describe(),
            {"plutous_funcs": []},
        )
