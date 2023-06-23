from datetime import datetime as dt

import pandas as pd
from loguru import logger
from sqlalchemy import (
    BIGINT,
    ColumnExpressionArgument,
    Connection,
    Index,
    func,
    select,
    text,
)
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

    @classmethod
    def query(
        cls,
        exchange: Exchange,
        symbols: list[str],
        since: int,
        frequency: str,
        conn: Connection,
        filters: list[ColumnExpressionArgument[bool]] = [],
    ) -> pd.DataFrame:
        logger.info(f"Loading {cls.__name__} data ")
        frequency = frequency.lower()
        sql = (
            select(
                cls.timestamp,
                cls.datetime,
                cls.exchange,
                cls.symbol,
                getattr(cls, cls.__main_column__),
            )
            .where(
                cls.timestamp > since,
                cls.exchange == exchange,
            )
            .order_by(cls.timestamp.asc())
        )
        if frequency == "1h":
            sql = sql.where(func.extract("minute", cls.datetime) == 55)
        elif frequency == "30m":
            sql = sql.where(func.extract("minute", cls.datetime).in_([25, 55]))
        elif frequency == "15m":
            sql = sql.where(func.extract("minute", cls.datetime).in_([10, 25, 40, 55]))
        elif frequency == "10m":
            sql = sql.where(
                func.extract("minute", cls.datetime).in_([5, 15, 25, 35, 45, 55])
            )
        elif frequency == "5m":
            pass

        if symbols:
            sql = sql.where(cls.symbol.in_(symbols))

        if filters:
            sql = sql.where(*filters)

        return pd.read_sql(sql, conn).pivot(
            index="datetime",
            columns="symbol",
            values=cls.__main_column__,
        )
