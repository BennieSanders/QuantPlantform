from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.backtest_job import BacktestJob
from app.schemas.backtest import BacktestJobResponse, BacktestRequest
from app.services.backtest_service import run_backtest


TERMINAL_STATUSES = {"succeeded", "failed", "cancelled"}
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="backtest-job")


def create_backtest_job(
    request: BacktestRequest,
    db: Session,
    user_id: str,
    submit: bool = True,
    retry_of_job_id: str | None = None,
    attempt: int = 1,
) -> BacktestJobResponse:
    job = BacktestJob(
        id=f"job-{uuid4().hex[:10]}",
        user_id=user_id,
        status="queued",
        request_payload=request.model_dump(),
        result_backtest_id=None,
        retry_of_job_id=retry_of_job_id,
        attempt=attempt,
        cancel_requested=False,
        error_message="",
        created_at=_now(),
        started_at=None,
        finished_at=None,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    if submit:
        _executor.submit(run_backtest_job, job.id)

    return _job_to_response(job)


def run_backtest_job(job_id: str) -> None:
    with SessionLocal() as db:
        job = db.get(BacktestJob, job_id)
        if job is None or job.status in TERMINAL_STATUSES:
            return
        if job.cancel_requested:
            job.status = "cancelled"
            job.finished_at = _now()
            job.error_message = "Backtest job cancelled before execution"
            db.commit()
            return

        job.status = "running"
        job.started_at = _now()
        db.commit()

        try:
            request = BacktestRequest(**job.request_payload)
            response = run_backtest(request, db, user_id=job.user_id)
        except Exception as error:
            job.status = "failed"
            job.error_message = str(error)
            job.finished_at = _now()
            db.commit()
            return

        db.refresh(job)
        if job.cancel_requested:
            job.status = "cancelled"
            job.error_message = "Backtest job cancellation requested during execution"
            job.finished_at = _now()
            db.commit()
            return

        job.status = "succeeded"
        job.result_backtest_id = response.backtest_id
        job.error_message = ""
        job.finished_at = _now()
        db.commit()


def list_backtest_jobs(
    db: Session,
    user_id: str,
    limit: int = 20,
) -> list[BacktestJobResponse]:
    limit = min(max(limit, 1), 100)
    jobs = db.scalars(
        select(BacktestJob)
        .where(BacktestJob.user_id == user_id)
        .order_by(BacktestJob.created_at.desc())
        .limit(limit)
    ).all()
    return [_job_to_response(job) for job in jobs]


def get_backtest_job(
    job_id: str,
    db: Session,
    user_id: str,
) -> BacktestJobResponse | None:
    job = db.get(BacktestJob, job_id)
    if job is None or job.user_id != user_id:
        return None
    return _job_to_response(job)


def cancel_backtest_job(
    job_id: str,
    db: Session,
    user_id: str,
) -> BacktestJobResponse | None:
    job = db.get(BacktestJob, job_id)
    if job is None or job.user_id != user_id:
        return None
    if job.status in TERMINAL_STATUSES:
        return _job_to_response(job)

    job.cancel_requested = True
    if job.status == "queued":
        job.status = "cancelled"
        job.error_message = "Backtest job cancelled before execution"
        job.finished_at = _now()
    else:
        job.error_message = "Cancellation requested; running job will stop at the next safe point"
    db.commit()
    db.refresh(job)
    return _job_to_response(job)


def retry_backtest_job(
    job_id: str,
    db: Session,
    user_id: str,
    submit: bool = True,
) -> BacktestJobResponse | None:
    job = db.get(BacktestJob, job_id)
    if job is None or job.user_id != user_id:
        return None
    if job.status not in {"failed", "cancelled"}:
        raise ValueError("Only failed or cancelled jobs can be retried")

    request = BacktestRequest(**job.request_payload)
    return create_backtest_job(
        request,
        db,
        user_id=user_id,
        submit=submit,
        retry_of_job_id=job.id,
        attempt=job.attempt + 1,
    )


def recover_interrupted_jobs(db: Session) -> int:
    now = _now()
    jobs = db.scalars(
        select(BacktestJob).where(BacktestJob.status.in_(["queued", "running"]))
    ).all()
    for job in jobs:
        job.status = "failed"
        job.error_message = "Backtest job interrupted before completion"
        job.finished_at = now
    if jobs:
        db.commit()
    return len(jobs)


def _job_to_response(job: BacktestJob) -> BacktestJobResponse:
    return BacktestJobResponse(
        id=job.id,
        user_id=job.user_id,
        status=job.status,
        request_payload=job.request_payload,
        result_backtest_id=job.result_backtest_id,
        retry_of_job_id=job.retry_of_job_id,
        attempt=job.attempt,
        cancel_requested=job.cancel_requested,
        error_message=job.error_message,
        created_at=job.created_at.isoformat(),
        started_at=job.started_at.isoformat() if job.started_at else None,
        finished_at=job.finished_at.isoformat() if job.finished_at else None,
    )


def _now() -> datetime:
    return datetime.now(UTC)
