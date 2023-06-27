import pandas as pd
from loguru import logger
from sqlalchemy import DECIMAL, ColumnExpressionArgument, Connection, select
from sqlalchemy.orm import Mapped, mapped_column

from plutous.enums import Exchange

from .base import Base


class FundingSettlement(Base):
    funding_rate: Mapped[float] = mapped_column(DECIMAL(7, 6))

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
        sql = (
            select(
                cls.timestamp,
                cls.datetime,
                cls.exchange,
                cls.symbol,
                cls.funding_rate,
            )
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

        return pd.read_sql(sql, conn).pivot(
            index="datetime",
            columns="symbol",
            values="funding_rate",
        )
