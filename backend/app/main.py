from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.ai import router as ai_router
from app.api.auth import router as auth_router
from app.api.backtests import router as backtests_router
from app.api.market import router as market_router
from app.api.strategies import router as strategies_router
from app.api.users import router as users_router
from app.core.config import get_settings
from app.core.database import SessionLocal, init_db
from app.services.backtest_job_service import recover_interrupted_jobs
from app.services.strategy_service import seed_builtin_strategies
from app.services.user_service import ensure_system_user


settings = get_settings()
app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
init_db()
with SessionLocal() as db:
    recover_interrupted_jobs(db)
    ensure_system_user(db)
    seed_builtin_strategies(db)
app.include_router(backtests_router)
app.include_router(strategies_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(market_router)
app.include_router(ai_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
