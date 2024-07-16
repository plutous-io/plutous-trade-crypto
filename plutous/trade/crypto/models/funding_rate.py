from sqlalchemy import DECIMAL
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class FundingRate(Base):
    __main_columns__ = ["funding_rate"]

    funding_rate: Mapped[float] = mapped_column(DECIMAL(7, 6))
