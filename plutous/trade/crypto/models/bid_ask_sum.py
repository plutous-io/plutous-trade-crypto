from sqlalchemy import func
from sqlalchemy.orm import Mapped

from .base import Base


class BidAskSum(Base):
    __main_columns__ = ["bids_sum_5", "asks_sum_5"]

    bids_sum_5: Mapped[float]
    bids_sum_10: Mapped[float]
    bids_sum_15: Mapped[float]
    bids_sum_20: Mapped[float]
    asks_sum_5: Mapped[float]
    asks_sum_10: Mapped[float]
    asks_sum_15: Mapped[float]
    asks_sum_20: Mapped[float]

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
