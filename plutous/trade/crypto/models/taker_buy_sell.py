from sqlalchemy.orm import Mapped

from .base import Base


class TakerBuySell(Base):
    __main_columns__ = ["buy_vol", "sell_vol"]

    buy_vol: Mapped[float]
    sell_vol: Mapped[float]
