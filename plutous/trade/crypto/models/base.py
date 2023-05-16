from datetime import datetime as dt

from sqlalchemy import TIMESTAMP, Index, String
from sqlalchemy.orm import DeclarativeBase,Mapped, declared_attr, mapped_column
from plutous.models import BaseMixin


class Base(DeclarativeBase, BaseMixin):
    exchange: Mapped[str] = mapped_column(String, nullable=False)
    symbol: Mapped[str] = mapped_column(String, nullable=False)
    timestamp: Mapped[int] = mapped_column(TIMESTAMP, nullable=False)
    datetime: Mapped[dt] = mapped_column(TIMESTAMP, nullable=False)

    @declared_attr.directive
    def __table_args__(cls) -> tuple:
        return (
            Index(
                f"ix_{cls.__tablename__}_exchange_symbol_timestamp",
                "exchange",
                "symbol",
                "timestamp",
                unique=True,
            ),
            {"schema": "crypto"},
        )
