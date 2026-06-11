"""initial engineering schema

Revision ID: 0001_initial_engineering_schema
Revises:
Create Date: 2026-05-28
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0001_initial_engineering_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    op.create_table(
        "strategies",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("strategy_type", sa.String(length=32), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("default_params", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_strategies_id"), "strategies", ["id"], unique=False)
    op.create_index(op.f("ix_strategies_user_id"), "strategies", ["user_id"], unique=False)

    op.create_table(
        "backtest_records",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("strategy_id", sa.String(length=64), nullable=False),
        sa.Column("strategy_name", sa.String(length=80), nullable=False),
        sa.Column("asset_class", sa.String(length=32), nullable=False),
        sa.Column("market_type", sa.String(length=32), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("timeframe", sa.String(length=16), nullable=False),
        sa.Column("position_mode", sa.String(length=32), nullable=False),
        sa.Column("start_date", sa.String(length=16), nullable=False),
        sa.Column("end_date", sa.String(length=16), nullable=False),
        sa.Column("initial_cash", sa.Float(), nullable=False),
        sa.Column("params", sa.JSON(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("equity_curve", sa.JSON(), nullable=False),
        sa.Column("trades", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_backtest_records_id"), "backtest_records", ["id"], unique=False)
    op.create_index(
        op.f("ix_backtest_records_strategy_id"),
        "backtest_records",
        ["strategy_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_backtest_records_symbol"),
        "backtest_records",
        ["symbol"],
        unique=False,
    )
    op.create_index(
        op.f("ix_backtest_records_user_id"),
        "backtest_records",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "backtest_jobs",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("request_payload", sa.JSON(), nullable=False),
        sa.Column("result_backtest_id", sa.String(length=64), nullable=True),
        sa.Column("retry_of_job_id", sa.String(length=64), nullable=True),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("cancel_requested", sa.Boolean(), nullable=False),
        sa.Column("error_message", sa.String(length=1000), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_backtest_jobs_id"), "backtest_jobs", ["id"], unique=False)
    op.create_index(
        op.f("ix_backtest_jobs_result_backtest_id"),
        "backtest_jobs",
        ["result_backtest_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_backtest_jobs_retry_of_job_id"),
        "backtest_jobs",
        ["retry_of_job_id"],
        unique=False,
    )
    op.create_index(op.f("ix_backtest_jobs_status"), "backtest_jobs", ["status"], unique=False)
    op.create_index(op.f("ix_backtest_jobs_user_id"), "backtest_jobs", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_backtest_jobs_user_id"), table_name="backtest_jobs")
    op.drop_index(op.f("ix_backtest_jobs_status"), table_name="backtest_jobs")
    op.drop_index(op.f("ix_backtest_jobs_retry_of_job_id"), table_name="backtest_jobs")
    op.drop_index(op.f("ix_backtest_jobs_result_backtest_id"), table_name="backtest_jobs")
    op.drop_index(op.f("ix_backtest_jobs_id"), table_name="backtest_jobs")
    op.drop_table("backtest_jobs")
    op.drop_index(op.f("ix_backtest_records_user_id"), table_name="backtest_records")
    op.drop_index(op.f("ix_backtest_records_symbol"), table_name="backtest_records")
    op.drop_index(op.f("ix_backtest_records_strategy_id"), table_name="backtest_records")
    op.drop_index(op.f("ix_backtest_records_id"), table_name="backtest_records")
    op.drop_table("backtest_records")
    op.drop_index(op.f("ix_strategies_user_id"), table_name="strategies")
    op.drop_index(op.f("ix_strategies_id"), table_name="strategies")
    op.drop_table("strategies")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")
