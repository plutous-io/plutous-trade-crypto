from pydantic import BaseModel

from plutous.enums import Exchange


class TradePost(BaseModel):
    strategy_id: int
    symbol: str
    exchange: Exchange
    action: str
    order_type: str


class TradesPost(BaseModel):
    trades: list[TradePost]
