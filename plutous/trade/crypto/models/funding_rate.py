from sqlalchemy.orm import Mapped

from .base import Base


class FundingRate(Base):
    funding_rate: Mapped[float]
