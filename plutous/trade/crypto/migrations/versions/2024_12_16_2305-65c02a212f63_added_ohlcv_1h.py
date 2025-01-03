"""added ohlcv_1h

Revision ID: 65c02a212f63
Revises: 724b55f51ade
Create Date: 2024-12-16 23:05:06.799955

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "65c02a212f63"
down_revision = "724b55f51ade"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    exchange_enum = postgresql.ENUM(name="exchange", schema="public", create_type=False)
    op.create_table(
        "ohlcv_1h",
        sa.Column("open", sa.Float(), nullable=False),
        sa.Column("high", sa.Float(), nullable=False),
        sa.Column("low", sa.Float(), nullable=False),
        sa.Column("close", sa.Float(), nullable=False),
        sa.Column("volume", sa.Float(), nullable=False),
        sa.Column("exchange", exchange_enum, nullable=False),
        sa.Column("symbol", sa.String(), nullable=False),
        sa.Column("timestamp", sa.BIGINT(), nullable=False),
        sa.Column("datetime", sa.DateTime(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="crypto",
    )
    op.create_index(
        "ix_ohlcv_1h_created_at",
        "ohlcv_1h",
        ["created_at"],
        unique=False,
        schema="crypto",
    )
    op.create_index(
        "ix_ohlcv_1h_exchange_symbol_timestamp",
        "ohlcv_1h",
        ["exchange", "symbol", "timestamp"],
        unique=True,
        schema="crypto",
    )
    op.create_index(
        "ix_ohlcv_1h_timestamp",
        "ohlcv_1h",
        ["timestamp"],
        unique=False,
        schema="crypto",
    )
    op.create_index(
        "ix_ohlcv_1h_time_of_minute",
        "ohlcv_1h",
        [sa.text("EXTRACT(minute from datetime)")],
        unique=False,
        schema="crypto",
    )
    op.create_index(
        "ix_ohlcv_1h_updated_at",
        "ohlcv_1h",
        ["updated_at"],
        unique=False,
        schema="crypto",
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index("ix_ohlcv_1h_updated_at", table_name="ohlcv_1h", schema="crypto")
    op.drop_index("ix_ohlcv_1h_time_of_minute", table_name="ohlcv_1h", schema="crypto")
    op.drop_index(
        "ix_ohlcv_1h_timestamp_exchange_symbol", table_name="ohlcv_1h", schema="crypto"
    )
    op.drop_index("ix_ohlcv_1h_created_at", table_name="ohlcv_1h", schema="crypto")
    op.drop_table("ohlcv_1h", schema="crypto")
    # ### end Alembic commands ###