from ccxt.base.errors import InvalidOrder


class OrderNotCancellable(InvalidOrder):
    pass


class OrderFilled(OrderNotCancellable):
    pass
