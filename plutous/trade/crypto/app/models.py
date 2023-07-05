from decimal import Decimal

from pydantic import BaseModel, Field

from plutous.trade.enums import Action, PositionSide


class BotTradePost(BaseModel):
    symbol: str
    action: Action
    quantity: Decimal = Field(max_digits=20, decimal_places=8)
    prev_position_side: PositionSide
    prev_position_size: Decimal = Field(max_digits=20, decimal_places=8)


class BotClosePost(BaseModel):
    symbol: str
    side: PositionSide
    quantity: Decimal | None = Field(default=None, max_digits=20, decimal_places=8)
