from pydantic import BaseModel

from plutous.trade.enums import Action


class BotTradePost(BaseModel):
    symbol: str
    action: Action
    quantity: float | None = None


class BotClosePost(BaseModel):
    symbol: str