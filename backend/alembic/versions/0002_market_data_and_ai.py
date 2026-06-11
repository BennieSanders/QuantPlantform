"""add persisted market data and ai analyses

Revision ID: 0002_market_data_and_ai
Revises: 0001_initial_engineering_schema
Create Date: 2026-06-11
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0002_market_data_and_ai"
down_revision: str | None = "0001_initial_engineering_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "market_klines",
        sa.Column("id", sa.String(length=96), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("timeframe", sa.String(length=16), nullable=False),
        sa.Column("open_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("close_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open", sa.Float(), nullable=False),
        sa.Column("high", sa.Float(), nullable=False),
        sa.Column("low", sa.Float(), nullable=False),
        sa.Column("close", sa.Float(), nullable=False),
        sa.Column("volume", sa.Float(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("symbol", "timeframe", "open_time", name="uq_market_kline_series_time"),
    )
    op.create_index(op.f("ix_market_klines_symbol"), "market_klines", ["symbol"])
    op.create_index(op.f("ix_market_klines_timeframe"), "market_klines", ["timeframe"])
    op.create_index(op.f("ix_market_klines_open_time"), "market_klines", ["open_time"])

    op.create_table(
        "ai_analyses",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("backtest_id", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("risk_level", sa.String(length=16), nullable=False),
        sa.Column("strengths", sa.JSON(), nullable=False),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("recommendations", sa.JSON(), nullable=False),
        sa.Column("suggested_params", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ai_analyses_id"), "ai_analyses", ["id"])
    op.create_index(op.f("ix_ai_analyses_user_id"), "ai_analyses", ["user_id"])
    op.create_index(op.f("ix_ai_analyses_backtest_id"), "ai_analyses", ["backtest_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_ai_analyses_backtest_id"), table_name="ai_analyses")
    op.drop_index(op.f("ix_ai_analyses_user_id"), table_name="ai_analyses")
    op.drop_index(op.f("ix_ai_analyses_id"), table_name="ai_analyses")
    op.drop_table("ai_analyses")
    op.drop_index(op.f("ix_market_klines_open_time"), table_name="market_klines")
    op.drop_index(op.f("ix_market_klines_timeframe"), table_name="market_klines")
    op.drop_index(op.f("ix_market_klines_symbol"), table_name="market_klines")
    op.drop_table("market_klines")
