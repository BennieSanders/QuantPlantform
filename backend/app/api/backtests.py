from fastapi import APIRouter
from fastapi.params import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.backtest import BacktestRequest, BacktestResponse
from app.services.backtest_service import run_backtest


router = APIRouter(prefix="/api/backtests", tags=["backtests"])


@router.post("", response_model=BacktestResponse)
def create_backtest(
    request: BacktestRequest,
    db: Session = Depends(get_db),
) -> BacktestResponse:
    return run_backtest(request, db)
