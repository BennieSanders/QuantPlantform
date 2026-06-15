from typing import Literal

from pydantic import BaseModel, Field


MarketSymbol = Literal["BTCUSDT", "ETHUSDT"]
MarketTimeframe = Literal["1m", "5m", "15m", "1h", "1d"]


class MarketSyncRequest(BaseModel):
    symbol: MarketSymbol
    timeframe: MarketTimeframe = "1m"
    limit: int = Field(default=200, ge=1, le=2000)
    range: Literal["latest", "today_shanghai", "chart_window", "backtest_window"] = "latest"


class MarketRangeResponse(BaseModel):
    symbol: str
    timeframe: str
    start_date: str | None
    end_date: str | None
    count: int


class MarketDataHealthResponse(BaseModel):
    status: Literal["empty", "fresh", "watch", "stale"]
    expected_bar_seconds: int
    age_minutes: float | None
    gap_count: int
    missing_bars: int
    latest_close_time: str | None
    latest_ingested_at: str | None


class MarketKlineResponse(BaseModel):
    symbol: str
    timeframe: str
    open_time: str
    close_time: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    source: str


class MarketSeriesResponse(BaseModel):
    symbol: str
    timeframe: str
    count: int
    last_price: float | None
    change_rate: float | None
    last_open_time: str | None
    last_ingested_at: str | None
    health: MarketDataHealthResponse
    klines: list[MarketKlineResponse]


class MarketSyncResponse(BaseModel):
    symbol: str
    timeframe: str
    fetched: int
    inserted: int
    updated: int
    latest_open_time: str | None
