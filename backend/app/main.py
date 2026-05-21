from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.backtests import router as backtests_router
from app.api.strategies import router as strategies_router
from app.core.database import SessionLocal, init_db
from app.services.strategy_service import seed_builtin_strategies


app = FastAPI(title="Quant Platform API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
init_db()
with SessionLocal() as db:
    seed_builtin_strategies(db)
app.include_router(backtests_router)
app.include_router(strategies_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
