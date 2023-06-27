import pandas as pd
from loguru import logger
from sqlalchemy import ColumnExpressionArgument, Connection, func, select, text
from sqlalchemy.orm import Mapped, declared_attr

from plutous.enums import Exchange

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

    @classmethod
    def query(
        cls,
        conn: Connection,
        exchange: Exchange,
        symbols: list[str],
        frequency: str,
        since: int,
        until: int | None = None,
        filters: list[ColumnExpressionArgument[bool]] = [],
    ) -> pd.DataFrame:
        logger.info(f"Loading {cls.__name__} data ")
        frequency = frequency.lower()
        miniute_interval = 60 if frequency == "1h" else int(frequency[:-1])
        dt = func.date_trunc("hour", cls.datetime) + func.floor(
            func.extract("minute", cls.datetime) / miniute_interval
        ) * text(f"'{frequency}'::interval")
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
        )
        if symbols:
            sql = sql.where(cls.symbol.in_(symbols))

        if until:
            sql = sql.where(cls.timestamp < until)

        if filters:
            sql = sql.where(*filters)

        df = pd.read_sql(sql, conn).pivot(
            index="datetime",
            columns="symbol",
            values=["open", "high", "low", "close", "volume"],
        )

        df.columns = df.columns.swaplevel(0, 1)

        return df
