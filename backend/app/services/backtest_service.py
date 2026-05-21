from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.strategy import Strategy
from app.schemas.backtest import (
    BacktestMetrics,
    BacktestRequest,
    BacktestResponse,
    EquityPoint,
    TradeRecord,
)
from quant_engine.backtest import run_ma_cross_backtest, run_script_backtest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SAMPLE_DATA_DIR = PROJECT_ROOT / "data" / "sample"


def run_backtest(request: BacktestRequest, db: Session) -> BacktestResponse:
    strategy = _load_strategy(request, db)
    params = _merge_params(strategy, request)

    if strategy.strategy_type == "builtin":
        result = run_ma_cross_backtest(
            symbol=request.symbol,
            timeframe=request.timeframe,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_cash=request.initial_cash,
            short_window=int(params.get("short_window", 7)),
            long_window=int(params.get("long_window", 30)),
            data_dir=SAMPLE_DATA_DIR,
        )
    else:
        result = run_script_backtest(
            symbol=request.symbol,
            timeframe=request.timeframe,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_cash=request.initial_cash,
            code=strategy.code,
            params=params,
            data_dir=SAMPLE_DATA_DIR,
            strategy_name=strategy.id,
        )

    return BacktestResponse(
        backtest_id=f"bt-{uuid4().hex[:8]}",
        asset_class=request.asset_class,
        market_type=request.market_type,
        symbol=result.symbol,
        timeframe=result.timeframe,
        position_mode=request.position_mode,
        strategy=result.strategy,
        metrics=BacktestMetrics(
            total_return=result.metrics.total_return,
            max_drawdown=result.metrics.max_drawdown,
            trade_count=result.metrics.trade_count,
            win_rate=result.metrics.win_rate,
            final_equity=result.metrics.final_equity,
        ),
        equity_curve=[
            EquityPoint(date=point.date.isoformat(), equity=point.equity)
            for point in result.broker_result.equity_curve
        ],
        trades=[
            TradeRecord(
                date=trade.date.isoformat(),
                side=trade.side,
                price=trade.price,
                quantity=trade.quantity,
                fee=trade.fee,
            )
            for trade in result.broker_result.trades
        ],
    )


def _load_strategy(request: BacktestRequest, db: Session) -> Strategy:
    strategy_id = request.strategy_id or "ma-cross-default"
    strategy = db.get(Strategy, strategy_id)
    if strategy is None:
        raise HTTPException(status_code=404, detail="Strategy not found")
    if strategy.status != "active":
        raise HTTPException(status_code=400, detail="Only active strategies can be backtested")
    return strategy


def _merge_params(strategy: Strategy, request: BacktestRequest) -> dict:
    params = dict(strategy.default_params or {})
    params.update(request.params)
    return params
