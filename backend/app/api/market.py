from typing import Literal

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.schemas.market import (
    MarketSeriesResponse,
    MarketRangeResponse,
    MarketSymbol,
    MarketSyncRequest,
    MarketSyncResponse,
    MarketTimeframe,
)
from app.services.market_data_service import (
    get_market_range,
    get_market_series,
    sync_market_klines,
)


router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/klines", response_model=MarketSeriesResponse)
def list_market_klines(
    symbol: MarketSymbol = Query(default="BTCUSDT"),
    timeframe: MarketTimeframe = Query(default="1m"),
    limit: int = Query(default=200, ge=1, le=2000),
    range: Literal["latest", "today_shanghai", "chart_window", "backtest_window"] = Query(default="latest"),
    db: Session = Depends(get_db),
    _user_id: str = Depends(get_current_user_id),
) -> MarketSeriesResponse:
    return get_market_series(
        db,
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
        range_name=range,
    )


@router.get("/range", response_model=MarketRangeResponse)
def get_market_data_range(
    symbol: MarketSymbol = Query(default="BTCUSDT"),
    timeframe: MarketTimeframe = Query(default="1d"),
    db: Session = Depends(get_db),
    _user_id: str = Depends(get_current_user_id),
) -> MarketRangeResponse:
    return get_market_range(db, symbol=symbol, timeframe=timeframe)


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
