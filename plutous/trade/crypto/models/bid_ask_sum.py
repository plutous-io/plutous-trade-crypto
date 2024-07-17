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
        match freq:
            case "1h":
                sql = sql.where(func.extract("minute", cls.datetime) == 0)
            case "30m":
                sql = sql.where(func.extract("minute", cls.datetime).in_([0, 30]))
            case "15m":
                sql = sql.where(
                    func.extract("minute", cls.datetime).in_([0, 15, 30, 45])
                )
            case "10m":
                sql = sql.where(
                    func.extract("minute", cls.datetime).in_([0, 10, 20, 30, 40, 50])
                )
            case "5m":
                pass
            case _:
                raise ValueError(f"Unsupported frequency: {freq}")
        return sql
