import pandas as pd
from sqlalchemy import DECIMAL, Connection, select
from sqlalchemy.orm import Mapped, mapped_column

from plutous.enums import Exchange

from .base import Base


class FundingSettlement(Base):
    funding_rate: Mapped[float] = mapped_column(DECIMAL(7, 6))

    @classmethod
    def query(
        cls,
        exchange_type: Exchange,
        symbols: list[str],
        since: int,
        conn: Connection,
    ) -> pd.DataFrame:
        sql = (
            select(
                cls.timestamp,
                cls.datetime,
                cls.exchange,
                cls.symbol,
            )
            .where(
                cls.timestamp > since,
                cls.exchange == exchange_type,
            )
            .order_by(cls.timestamp.asc())
        )

        if symbols:
            sql = sql.where(cls.symbol.in_(symbols))

        return pd.read_sql(sql, conn)
