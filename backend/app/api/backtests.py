from fastapi import APIRouter, HTTPException
from fastapi.params import Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.schemas.backtest import (
    BacktestJobResponse,
    BacktestRecordSummary,
    BacktestRequest,
    BacktestResponse,
)
from app.services.backtest_job_service import (
    cancel_backtest_job,
    create_backtest_job,
    get_backtest_job,
    list_backtest_jobs,
    retry_backtest_job,
)
from app.services.backtest_service import get_backtest_record, list_backtest_records, run_backtest


router = APIRouter(prefix="/api/backtests", tags=["backtests"])


@router.post("", response_model=BacktestResponse)
def create_backtest(
    request: BacktestRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> BacktestResponse:
    return run_backtest(request, db, user_id=user_id)


@router.post("/jobs", response_model=BacktestJobResponse, status_code=202)
def create_backtest_job_item(
    request: BacktestRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> BacktestJobResponse:
    return create_backtest_job(request, db, user_id=user_id)


@router.get("/jobs", response_model=list[BacktestJobResponse])
def list_backtest_job_items(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> list[BacktestJobResponse]:
    return list_backtest_jobs(db, user_id=user_id, limit=limit)


@router.get("/jobs/{job_id}", response_model=BacktestJobResponse)
def get_backtest_job_item(
    job_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> BacktestJobResponse:
    job = get_backtest_job(job_id, db, user_id=user_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Backtest job not found")
    return job


@router.post("/jobs/{job_id}/cancel", response_model=BacktestJobResponse)
def cancel_backtest_job_item(
    job_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> BacktestJobResponse:
    job = cancel_backtest_job(job_id, db, user_id=user_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Backtest job not found")
    return job


@router.post("/jobs/{job_id}/retry", response_model=BacktestJobResponse, status_code=202)
def retry_backtest_job_item(
    job_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> BacktestJobResponse:
    try:
        job = retry_backtest_job(job_id, db, user_id=user_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    if job is None:
        raise HTTPException(status_code=404, detail="Backtest job not found")
    return job


@router.get("", response_model=list[BacktestRecordSummary])
def list_backtests(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> list[BacktestRecordSummary]:
    return list_backtest_records(db, user_id=user_id, limit=limit)


@router.get("/{backtest_id}", response_model=BacktestResponse)
def get_backtest(
    backtest_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> BacktestResponse:
    record = get_backtest_record(backtest_id, db, user_id=user_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Backtest record not found")
    return record
