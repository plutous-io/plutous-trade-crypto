from ccxt.pro import huobi


class Huobi(huobi):
    def describe(self):
        return self.deep_extend(
            super(Huobi, self).describe(),
            {"plutous_funcs": []},
        )
