from enum import Enum


class OrderType(Enum):
    LIMIT = "limit"
    MARKET = "market"
    LIMIT_CHASING = "limit_chasing"