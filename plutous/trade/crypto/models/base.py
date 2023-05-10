import re
from datetime import datetime as dt

from sqlalchemy import TIMESTAMP, Index, String
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


class Base(DeclarativeBase):
    __table_args__ = (
        Index(
            "ix_exchange_symbol_timestamp",
            "exchange",
            "symbol",
            "timestamp",
        ),
        {"schema": "crypto_data"},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[dt] = mapped_column(TIMESTAMP, nullable=False)
    updated_at: Mapped[dt] = mapped_column(
        TIMESTAMP,
        nullable=False,
        default=dt.utcnow,
        onupdate=dt.utcnow,
    )
    exchange: Mapped[str] = mapped_column(String, nullable=False)
    symbol: Mapped[str] = mapped_column(String, nullable=False)
    timestamp: Mapped[int] = mapped_column(TIMESTAMP, nullable=False)
    datetime: Mapped[dt] = mapped_column(TIMESTAMP, nullable=False)

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return re.sub("(?<!^)(?=[A-Z])", "_", cls.__name__).lower()
