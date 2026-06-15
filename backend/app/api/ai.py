from fastapi import APIRouter, Body, HTTPException
from fastapi.params import Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.schemas.ai import AiAnalysisRequest, AiAnalysisResponse
from app.services.ai_analysis_service import analyze_backtest, list_backtest_analyses


router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/backtests/{backtest_id}/analyze", response_model=AiAnalysisResponse)
def analyze_backtest_item(
    backtest_id: str,
    payload: AiAnalysisRequest | None = Body(default=None),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> AiAnalysisResponse:
    mode = payload.mode if payload is not None else "gemini"
    result = analyze_backtest(backtest_id, db, user_id, mode=mode)
    if result is None:
        raise HTTPException(status_code=404, detail="Backtest record not found")
    return result


@router.get("/backtests/{backtest_id}/analyses", response_model=list[AiAnalysisResponse])
def list_backtest_analysis_items(
    backtest_id: str,
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> list[AiAnalysisResponse]:
    results = list_backtest_analyses(backtest_id, db, user_id, limit)
    if results is None:
        raise HTTPException(status_code=404, detail="Backtest record not found")
    return results
