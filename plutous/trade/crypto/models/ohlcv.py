import pandas as pd
from loguru import logger
from sqlalchemy import ColumnExpressionArgument, Connection, func, select, text
from sqlalchemy.orm import Mapped, declared_attr

from plutous.enums import Exchange

from .base import Base, SupportedFreq


class OHLCVMixin:
    open: Mapped[float]
    high: Mapped[float]
    low: Mapped[float]
    close: Mapped[float]
    volume: Mapped[float]


class OHLCV(Base, OHLCVMixin):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return "ohlcv"

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
        filters: list[ColumnExpressionArgument[bool]] = [],
    ) -> pd.DataFrame:
        logger.info(f"Loading {cls.__name__} data ")
        freq = frequency.lower()
        miniute_interval = 60 if freq == "1h" else int(freq[:-1])
        dt = func.date_trunc("hour", cls.datetime) + func.floor(
            func.extract("minute", cls.datetime) / miniute_interval
        ) * text(f"'{freq}'::interval")
        sql = (
            select(
                cls.symbol,
                dt.label("datetime"),
                func.first_value(cls.timestamp)
                .over(partition_by=[dt, cls.symbol], order_by=cls.timestamp)
                .label("timestamp"),
                func.first_value(cls.open)
                .over(partition_by=[dt, cls.symbol], order_by=cls.timestamp)
                .label("open"),
                func.max(cls.high)
                .over(partition_by=[dt, cls.symbol], order_by=cls.high.desc())
                .label("high"),
                func.min(cls.low)
                .over(partition_by=[dt, cls.symbol], order_by=cls.low)
                .label("low"),
                func.first_value(cls.close)
                .over(partition_by=[dt, cls.symbol], order_by=cls.timestamp.desc())
                .label("close"),
                func.sum(cls.volume)
                .over(partition_by=[dt, cls.symbol], order_by=cls.timestamp.desc())
                .label("volume"),
            )
            .distinct(dt.label("datetime"), cls.symbol)
            .where(
                cls.timestamp >= since,
                cls.exchange == exchange,
            )
            .order_by(cls.timestamp.asc())
        )
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
            values=["open", "high", "low", "close", "volume"],
        )

        df.columns = df.columns.swaplevel(0, 1)

        return df


class OHLCV1h(Base, OHLCVMixin):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return "ohlcv_1h"
