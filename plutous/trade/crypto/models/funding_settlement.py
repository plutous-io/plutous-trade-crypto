from sqlalchemy import DECIMAL
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class FundingSettlement(Base):
    funding_rate: Mapped[float] = mapped_column(DECIMAL(7, 6))