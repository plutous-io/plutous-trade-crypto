from sqlalchemy import DECIMAL, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Orderbook(Base):
    bids: Mapped[list[list[float]]] = mapped_column(JSONB)
    asks: Mapped[list[list[float]]] = mapped_column(JSONB)
