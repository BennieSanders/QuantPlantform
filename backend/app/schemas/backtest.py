from typing import Literal

from pydantic import BaseModel, Field, model_validator


class BacktestRequest(BaseModel):
    asset_class: Literal["crypto"] = "crypto"
    market_type: Literal["spot"] = "spot"
    symbol: Literal["BTCUSDT", "ETHUSDT"]
    timeframe: Literal["1d", "1h"] = "1d"
    position_mode: Literal["long_only"] = "long_only"
    strategy: Literal["ma_cross", "rsi_reversal", "custom_code"] = "ma_cross"
    strategy_id: str | None = None
    start_date: str
    end_date: str
    initial_cash: float = Field(gt=0)
    params: dict[str, int | float | str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_strategy_params(self) -> "BacktestRequest":
        if self.strategy == "rsi_reversal" or "period" in self.params:
            period = self.params.get("period", 14)
            oversold = self.params.get("oversold", 30)
            overbought = self.params.get("overbought", 70)
            if not all(isinstance(value, int | float) for value in [period, oversold, overbought]):
                raise ValueError("RSI params must be numbers")
            if period <= 1:
                raise ValueError("RSI period must be greater than 1")
            if not 0 < oversold < overbought < 100:
                raise ValueError("RSI thresholds must satisfy 0 < oversold < overbought < 100")
            return self

        if self.strategy != "ma_cross" and "short_window" not in self.params:
            return self
        short_window = self.params.get("short_window", 7)
        long_window = self.params.get("long_window", 30)
        if not isinstance(short_window, int | float) or not isinstance(long_window, int | float):
            raise ValueError("MA windows must be numbers")
        if short_window <= 0 or long_window <= 0:
            raise ValueError("MA windows must be positive")
        if short_window >= long_window:
            raise ValueError("short_window must be smaller than long_window")
        return self


class EquityPoint(BaseModel):
    date: str
    equity: float


class MarketCandle(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class BacktestMetrics(BaseModel):
    total_return: float
    annualized_return: float
    max_drawdown: float
    sharpe_ratio: float
    trade_count: int
    win_rate: float
    final_equity: float


class TradeRecord(BaseModel):
    date: str
    side: str
    price: float
    quantity: float
    fee: float


class BacktestResponse(BaseModel):
    backtest_id: str
    user_id: str
    asset_class: str
    market_type: str
    symbol: str
    timeframe: str
    position_mode: str
    strategy: str
    metrics: BacktestMetrics
    market_klines: list[MarketCandle]
    equity_curve: list[EquityPoint]
    trades: list[TradeRecord]


class BacktestRecordSummary(BaseModel):
    id: str
    user_id: str
    symbol: str
    timeframe: str
    strategy_id: str
    strategy_name: str
    start_date: str
    end_date: str
    initial_cash: float
    metrics: BacktestMetrics
    created_at: str


BacktestJobStatus = Literal["queued", "running", "succeeded", "failed", "cancelled"]


class BacktestJobResponse(BaseModel):
    id: str
    user_id: str
    status: BacktestJobStatus
    request_payload: dict
    result_backtest_id: str | None = None
    retry_of_job_id: str | None = None
    attempt: int = 1
    cancel_requested: bool = False
    error_message: str = ""
    created_at: str
    started_at: str | None = None
    finished_at: str | None = None
