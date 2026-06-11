from datetime import UTC, datetime
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.backtest_record import BacktestRecord
from app.models.strategy import Strategy
from app.schemas.backtest import (
    BacktestMetrics,
    BacktestRecordSummary,
    BacktestRequest,
    BacktestResponse,
    MarketCandle,
    EquityPoint,
    TradeRecord,
)
from quant_engine.backtest import run_builtin_backtest, run_script_backtest
from quant_engine.datafeed import load_klines


SAMPLE_DATA_DIR = get_settings().sample_data_dir


def run_backtest(
    request: BacktestRequest,
    db: Session,
    user_id: str | None = None,
) -> BacktestResponse:
    owner_id = user_id or get_settings().system_user_id
    strategy = _load_strategy(request, db, owner_id)
    params = _merge_params(strategy, request)

    try:
        if strategy.strategy_type == "builtin":
            result = run_builtin_backtest(
                strategy_name=_builtin_strategy_name(strategy),
                symbol=request.symbol,
                timeframe=request.timeframe,
                start_date=request.start_date,
                end_date=request.end_date,
                initial_cash=request.initial_cash,
                params=params,
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
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Backtest failed: {error}") from error

    response = BacktestResponse(
        backtest_id=f"bt-{uuid4().hex[:8]}",
        user_id=owner_id,
        asset_class=request.asset_class,
        market_type=request.market_type,
        symbol=result.symbol,
        timeframe=result.timeframe,
        position_mode=request.position_mode,
        strategy=result.strategy,
        metrics=BacktestMetrics(
            total_return=result.metrics.total_return,
            annualized_return=result.metrics.annualized_return,
            max_drawdown=result.metrics.max_drawdown,
            sharpe_ratio=result.metrics.sharpe_ratio,
            trade_count=result.metrics.trade_count,
            win_rate=result.metrics.win_rate,
            final_equity=result.metrics.final_equity,
        ),
        market_klines=[
            MarketCandle(
                date=kline.date.isoformat(),
                open=kline.open,
                high=kline.high,
                low=kline.low,
                close=kline.close,
                volume=kline.volume,
            )
            for kline in result.klines
        ],
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
    _save_backtest_record(
        db=db,
        request=request,
        response=response,
        strategy=strategy,
        params=params,
        user_id=owner_id,
    )
    return response


def list_backtest_records(
    db: Session,
    user_id: str | None = None,
    limit: int = 20,
) -> list[BacktestRecordSummary]:
    owner_id = user_id or get_settings().system_user_id
    limit = min(max(limit, 1), 100)
    records = db.scalars(
        select(BacktestRecord)
        .where(BacktestRecord.user_id == owner_id)
        .order_by(BacktestRecord.created_at.desc())
        .limit(limit)
    ).all()
    return [_record_to_summary(record) for record in records]


def get_backtest_record(
    record_id: str,
    db: Session,
    user_id: str | None = None,
) -> BacktestResponse | None:
    owner_id = user_id or get_settings().system_user_id
    record = db.get(BacktestRecord, record_id)
    if record is None:
        return None
    if record.user_id != owner_id:
        return None
    return _record_to_response(record)


def _load_strategy(request: BacktestRequest, db: Session, user_id: str) -> Strategy:
    strategy_id = request.strategy_id or "ma-cross-default"
    strategy = db.get(Strategy, strategy_id)
    if strategy is None:
        raise HTTPException(status_code=404, detail="Strategy not found")
    if strategy.strategy_type != "builtin" and strategy.user_id != user_id:
        raise HTTPException(status_code=404, detail="Strategy not found")
    if strategy.status != "active":
        raise HTTPException(status_code=400, detail="Only active strategies can be backtested")
    return strategy


def _merge_params(strategy: Strategy, request: BacktestRequest) -> dict:
    params = dict(strategy.default_params or {})
    params.update(request.params)
    return params


def _builtin_strategy_name(strategy: Strategy) -> str:
    if strategy.id == "ma-cross-default":
        return "ma_cross"
    if strategy.id == "rsi-reversal-default":
        return "rsi_reversal"
    raise HTTPException(status_code=400, detail=f"Unsupported built-in strategy: {strategy.id}")


def _save_backtest_record(
    db: Session,
    request: BacktestRequest,
    response: BacktestResponse,
    strategy: Strategy,
    params: dict,
    user_id: str,
) -> None:
    record = BacktestRecord(
        id=response.backtest_id,
        user_id=user_id,
        strategy_id=strategy.id,
        strategy_name=strategy.name,
        asset_class=request.asset_class,
        market_type=request.market_type,
        symbol=response.symbol,
        timeframe=response.timeframe,
        position_mode=response.position_mode,
        start_date=request.start_date,
        end_date=request.end_date,
        initial_cash=request.initial_cash,
        params=params,
        metrics=response.metrics.model_dump(),
        equity_curve=[point.model_dump() for point in response.equity_curve],
        trades=[trade.model_dump() for trade in response.trades],
        created_at=datetime.now(UTC),
    )
    db.add(record)
    db.commit()


def _record_to_summary(record: BacktestRecord) -> BacktestRecordSummary:
    return BacktestRecordSummary(
        id=record.id,
        user_id=record.user_id,
        symbol=record.symbol,
        timeframe=record.timeframe,
        strategy_id=record.strategy_id,
        strategy_name=record.strategy_name,
        start_date=record.start_date,
        end_date=record.end_date,
        initial_cash=record.initial_cash,
        metrics=BacktestMetrics(**record.metrics),
        created_at=record.created_at.isoformat(),
    )


def _record_to_response(record: BacktestRecord) -> BacktestResponse:
    market_klines = _load_record_market_klines(record)
    return BacktestResponse(
        backtest_id=record.id,
        user_id=record.user_id,
        asset_class=record.asset_class,
        market_type=record.market_type,
        symbol=record.symbol,
        timeframe=record.timeframe,
        position_mode=record.position_mode,
        strategy=record.strategy_id,
        metrics=BacktestMetrics(**record.metrics),
        market_klines=market_klines,
        equity_curve=[EquityPoint(**point) for point in record.equity_curve],
        trades=[TradeRecord(**trade) for trade in record.trades],
    )


def _load_record_market_klines(record: BacktestRecord) -> list[MarketCandle]:
    try:
        path = SAMPLE_DATA_DIR / f"{record.symbol.upper()}_{record.timeframe}.csv"
        klines = load_klines(
            path,
            start_date=record.start_date,
            end_date=record.end_date,
        )
    except Exception:
        return []

    return [
        MarketCandle(
            date=kline.date.isoformat(),
            open=kline.open,
            high=kline.high,
            low=kline.low,
            close=kline.close,
            volume=kline.volume,
        )
        for kline in klines
    ]
