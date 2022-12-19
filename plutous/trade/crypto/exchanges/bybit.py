from ccxt.pro import bybit


class Bybit(bybit):
    def describe(self):
        return self.deep_extend(
            super(Bybit, self).describe(),
            {"plutous_funcs": []},
        )
