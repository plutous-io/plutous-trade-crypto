from datetime import datetime
from typing import Optional

from sqlalchemy import BIGINT, DECIMAL, INT
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class FundingRate(Base):
    __main_columns__ = ["funding_rate"]

    funding_rate: Mapped[float] = mapped_column(DECIMAL(7, 6))
    funding_interval: Mapped[Optional[int]] = mapped_column(INT)
    settlement_timestamp: Mapped[Optional[int]] = mapped_column(BIGINT)
    settlement_datetime: Mapped[Optional[datetime]]
