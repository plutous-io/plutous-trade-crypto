from sqlalchemy import DECIMAL
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class LongShortRatio(Base):
    long_account: Mapped[float] = mapped_column(DECIMAL(5, 4))
    short_account: Mapped[float] = mapped_column(DECIMAL(5, 4))
    long_short_ratio: Mapped[float] = mapped_column(DECIMAL(6, 4))
