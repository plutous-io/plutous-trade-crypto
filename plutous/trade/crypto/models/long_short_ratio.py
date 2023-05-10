from sqlalchemy.orm import Mapped

from .base import Base


class LongShortRatio(Base):
    long_account: Mapped[float]
    short_account: Mapped[float]
    long_short_ratio: Mapped[float]
