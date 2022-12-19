from ccxt.pro import okx


class Okx(okx):
    def describe(self):
        return self.deep_extend(
            super(Okx, self).describe(),
            {"plutous_funcs": []},
        )
