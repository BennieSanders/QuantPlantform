from sqlalchemy import Float, JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AiAnalysis(Base):
    __tablename__ = "ai_analyses"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    backtest_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(16), nullable=False)
    analysis_type: Mapped[str] = mapped_column(String(32), default="", nullable=False)
    readiness: Mapped[str] = mapped_column(String(32), default="", nullable=False)
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    strengths: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    warnings: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    recommendations: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    fit_profile: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    avoid_profile: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    execution_plan: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    suggested_params: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
