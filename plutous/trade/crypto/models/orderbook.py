from sqlalchemy import DECIMAL, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Orderbook(Base):
    bids: Mapped[list[list[float]]] = mapped_column(JSONB)
    bids_sum_5: Mapped[float]
    bids_sum_10: Mapped[float]
    bids_sum_15: Mapped[float]
    bids_sum_20: Mapped[float]
    asks: Mapped[list[list[float]]] = mapped_column(JSONB)
    asks_sum_5: Mapped[float]
    asks_sum_10: Mapped[float]
    asks_sum_15: Mapped[float]
    asks_sum_20: Mapped[float]
