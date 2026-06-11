from pydantic import BaseModel


class AiAnalysisResponse(BaseModel):
    id: str
    backtest_id: str
    provider: str
    summary: str
    risk_level: str
    strengths: list[str]
    warnings: list[str]
    recommendations: list[str]
    suggested_params: dict[str, int | float]
    created_at: str
