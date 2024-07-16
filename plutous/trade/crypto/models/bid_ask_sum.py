import pandas as pd
from loguru import logger
from sqlalchemy import ColumnExpressionArgument, Connection, func, select, text
from sqlalchemy.orm import Mapped, declared_attr

from plutous.enums import Exchange

from .base import Base, SupportedFreq


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
