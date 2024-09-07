from datetime import datetime as dt
from typing import Literal

import pandas as pd
from loguru import logger
from sqlalchemy import (
    BIGINT,
    ColumnExpressionArgument,
    Connection,
    Index,
    TextClause,
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


SupportedFreq = Literal["1m", "5m", "10m", "15m", "30m", "1h"]


class Base(DeclarativeBase, BaseMixin):
    __main_columns__: list[str]
    __default_frequency__: SupportedFreq = "5m"

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
    def _filter_by_frequency(cls, sql, freq: str):
        match freq:
            case "1h":
                sql = sql.where(func.extract("minute", cls.datetime) == 55)
            case "30m":
                sql = sql.where(func.extract("minute", cls.datetime).in_([25, 55]))
            case "15m":
                sql = sql.where(
                    func.extract("minute", cls.datetime).in_([10, 25, 40, 55])
                )
            case "10m":
                sql = sql.where(
                    func.extract("minute", cls.datetime).in_([5, 15, 25, 35, 45, 55])
                )
            case "5m":
                pass
            case _:
                raise ValueError(f"Unsupported frequency: {freq}")
        return sql

    @classmethod
    def query(
        cls,
        conn: Connection,
        exchange: Exchange,
        symbols: list[str],
        frequency: SupportedFreq,
        since: int,
        columns: list[str] = [],
        until: int | None = None,
        limit: int | None = None,
        filters: list[ColumnExpressionArgument[bool]] | list[TextClause] = [],
    ) -> pd.DataFrame:
        logger.info(f"Loading {cls.__name__} data ")
        cols = columns or cls.__main_columns__
        freq = frequency.lower()
        miniute_interval = 60 if freq == "1h" else int(freq[:-1])
        dt = func.date_trunc("hour", cls.datetime) + func.floor(
            func.extract("minute", cls.datetime) / miniute_interval
        ) * text(f"'{freq}'::interval")
        sql = (
            select(
                cls.timestamp,
                dt.label("datetime"),
                cls.exchange,
                cls.symbol,
                *[getattr(cls, col) for col in cols],
            )
            .where(
                cls.timestamp >= since,
                cls.exchange == exchange,
            )
            .order_by(cls.timestamp.asc())
        )
        sql = cls._filter_by_frequency(sql, freq)

        if symbols:
            sql = sql.where(cls.symbol.in_(symbols))
        if until:
            sql = sql.where(cls.timestamp < until)
        if filters:
            sql = sql.where(*filters)
        if limit:
            sql = sql.limit(limit)

        df = pd.read_sql(sql, conn).pivot(
            index="datetime",
            columns="symbol",
            values=cols,
        )

        df.columns = df.columns.swaplevel(0, 1)
        return df
