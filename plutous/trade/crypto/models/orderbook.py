from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Orderbook(Base):
    __main_columns__ = ["bids", "asks"]

    bids: Mapped[list[list[float]]] = mapped_column(JSONB)
    asks: Mapped[list[list[float]]] = mapped_column(JSONB)

    @classmethod
    def _filter_by_frequency(cls, sql, freq: str):
        if freq == "1m":
            return sql
        if freq == "1h":
            freq = "60m"
        steps = int(freq[:-1])
        sql = sql.where(
            func.extract("minute", cls.datetime).in_([i for i in range(0, 60, steps)])
        )
        return sql
