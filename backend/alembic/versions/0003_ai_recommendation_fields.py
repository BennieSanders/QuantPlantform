"""add ai recommendation fields

Revision ID: 0003_ai_recommendation_fields
Revises: 0002_market_data_and_ai
Create Date: 2026-06-15
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0003_ai_recommendation_fields"
down_revision: str | None = "0002_market_data_and_ai"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("ai_analyses", sa.Column("analysis_type", sa.String(length=32), nullable=False, server_default=""))
    op.add_column("ai_analyses", sa.Column("readiness", sa.String(length=32), nullable=False, server_default=""))
    op.add_column("ai_analyses", sa.Column("score", sa.Float(), nullable=False, server_default="0"))
    op.add_column("ai_analyses", sa.Column("confidence", sa.Float(), nullable=False, server_default="0"))
    op.add_column("ai_analyses", sa.Column("fit_profile", sa.JSON(), nullable=False, server_default=sa.text("'[]'")))
    op.add_column("ai_analyses", sa.Column("avoid_profile", sa.JSON(), nullable=False, server_default=sa.text("'[]'")))
    op.add_column("ai_analyses", sa.Column("execution_plan", sa.JSON(), nullable=False, server_default=sa.text("'[]'")))


def downgrade() -> None:
    op.drop_column("ai_analyses", "execution_plan")
    op.drop_column("ai_analyses", "avoid_profile")
    op.drop_column("ai_analyses", "fit_profile")
    op.drop_column("ai_analyses", "confidence")
    op.drop_column("ai_analyses", "score")
    op.drop_column("ai_analyses", "readiness")
    op.drop_column("ai_analyses", "analysis_type")
