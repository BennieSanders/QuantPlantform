from fastapi import APIRouter, HTTPException
from fastapi.params import Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.backtest import BacktestRecordSummary, BacktestRequest, BacktestResponse
from app.services.backtest_service import get_backtest_record, list_backtest_records, run_backtest


router = APIRouter(prefix="/api/backtests", tags=["backtests"])


@router.post("", response_model=BacktestResponse)
def create_backtest(
    request: BacktestRequest,
    db: Session = Depends(get_db),
) -> BacktestResponse:
    return run_backtest(request, db)


@router.get("", response_model=list[BacktestRecordSummary])
def list_backtests(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[BacktestRecordSummary]:
    return list_backtest_records(db, limit=limit)


@router.get("/{backtest_id}", response_model=BacktestResponse)
def get_backtest(
    backtest_id: str,
    db: Session = Depends(get_db),
) -> BacktestResponse:
    record = get_backtest_record(backtest_id, db)
    if record is None:
        raise HTTPException(status_code=404, detail="Backtest record not found")
    return record
