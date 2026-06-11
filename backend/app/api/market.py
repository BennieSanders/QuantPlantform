from fastapi import APIRouter, HTTPException
from fastapi.params import Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.schemas.market import (
    MarketSeriesResponse,
    MarketSymbol,
    MarketSyncRequest,
    MarketSyncResponse,
    MarketTimeframe,
)
from app.services.market_data_service import get_market_series, sync_market_klines


router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/klines", response_model=MarketSeriesResponse)
def list_market_klines(
    symbol: MarketSymbol = Query(default="BTCUSDT"),
    timeframe: MarketTimeframe = Query(default="1m"),
    limit: int = Query(default=200, ge=1, le=1000),
    db: Session = Depends(get_db),
    _user_id: str = Depends(get_current_user_id),
) -> MarketSeriesResponse:
    return get_market_series(db, symbol=symbol, timeframe=timeframe, limit=limit)


@router.post("/sync", response_model=MarketSyncResponse)
def sync_market_data(
    payload: MarketSyncRequest,
    db: Session = Depends(get_db),
    _user_id: str = Depends(get_current_user_id),
) -> MarketSyncResponse:
    try:
        return sync_market_klines(payload, db)
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Market data sync failed: {error}") from error
