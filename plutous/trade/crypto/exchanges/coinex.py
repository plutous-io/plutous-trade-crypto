from ccxt.base.errors import BadSymbol
from ccxt.pro.coinex import coinex


class CoinEx(coinex):
    def describe(self):
        return self.deep_extend(
            super(CoinEx, self).describe(),
            {"plutous_funcs": []},
        )