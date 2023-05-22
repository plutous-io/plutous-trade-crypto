from pydantic import BaseModel

from plutous.trade.enums import Action


class BotTradePost(BaseModel):
    symbol: str
    action: Action

