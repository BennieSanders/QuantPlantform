from typing import Literal

from pydantic import BaseModel, Field, model_validator


class BacktestRequest(BaseModel):
    asset_class: Literal["crypto"] = "crypto"
    market_type: Literal["spot"] = "spot"
    symbol: Literal["BTCUSDT", "ETHUSDT"]
    timeframe: Literal["1d", "1h"] = "1d"
    position_mode: Literal["long_only"] = "long_only"
    strategy: Literal["ma_cross", "custom_code"] = "ma_cross"
    strategy_id: str | None = None
    start_date: str
    end_date: str
    initial_cash: float = Field(gt=0)
    params: dict[str, int | float | str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_ma_params(self) -> "BacktestRequest":
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


class BacktestMetrics(BaseModel):
    total_return: float
    max_drawdown: float
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
    asset_class: str
    market_type: str
    symbol: str
    timeframe: str
    position_mode: str
    strategy: str
    metrics: BacktestMetrics
    equity_curve: list[EquityPoint]
    trades: list[TradeRecord]
