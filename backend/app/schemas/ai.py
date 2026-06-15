from typing import Literal

from pydantic import BaseModel


AiAnalysisMode = Literal["gemini", "openai", "local"]


class AiAnalysisResponse(BaseModel):
    id: str
    backtest_id: str
    provider: str
    summary: str
    risk_level: str
    analysis_type: str
    readiness: str
    score: float
    confidence: float
    strengths: list[str]
    warnings: list[str]
    recommendations: list[str]
    fit_profile: list[str]
    avoid_profile: list[str]
    execution_plan: list[str]
    suggested_params: dict[str, int | float]
    created_at: str


class AiAnalysisRequest(BaseModel):
    mode: AiAnalysisMode = "gemini"
