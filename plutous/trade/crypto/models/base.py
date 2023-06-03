from datetime import datetime as dt

from sqlalchemy import BIGINT, Index, text
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

from plutous.enums import Exchange
from plutous.models.base import BaseMixin
from plutous.models.base import Enum as BaseEnum


class Enum(BaseEnum):
    schema = "crypto"


class Base(DeclarativeBase, BaseMixin):
    exchange: Mapped[Exchange] = mapped_column(Enum(Exchange, schema="public"))
    symbol: Mapped[str]
    timestamp: Mapped[int] = mapped_column(BIGINT)
    datetime: Mapped[dt]

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
            Index(
                f"ix_{cls.__tablename__}_timestamp",
                "timestamp",
            ),
            Index(
                f"ix_{cls.__tablename__}_time_of_minute",
                text("EXTRACT(minute from datetime)"),
            ),
            *super().__table_args__,
            {"schema": "crypto"},
        )
