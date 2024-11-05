from datetime import datetime
from typing import Optional

from sqlalchemy import BIGINT, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class FundingRate(Base):
    __main_columns__ = ["funding_rate"]

    funding_rate: Mapped[float] = mapped_column(DECIMAL(7, 6))
    settlement_timestamp: Mapped[int] = mapped_column(BIGINT)
    settlement_datetime: Mapped[Optional[datetime]]
