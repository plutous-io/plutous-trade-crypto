from sqlalchemy.orm import Mapped, declared_attr

from .base import Base


class OHLCV(Base):
    open: Mapped[float]
    high: Mapped[float]
    low: Mapped[float]
    close: Mapped[float]
    volume: Mapped[float]

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return "ohlcv"
