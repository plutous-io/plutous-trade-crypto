from pydantic import BaseModel

from plutous.trade.enums import Action, PositionSide


class BotTradePost(BaseModel):
    symbol: str
    action: Action
    quantity: float 
    prev_position_side: PositionSide
    prev_position_size: float


class BotClosePost(BaseModel):
    symbol: str
    side: PositionSide
    quantity: float | None = None