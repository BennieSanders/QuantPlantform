from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from quant_engine.analyzer import PerformanceMetrics
from quant_engine.broker import BrokerResult, SimulatedSpotBroker
from quant_engine.datafeed import Kline, build_sample_path, load_klines
from quant_engine.engine import BacktestEngine
from quant_engine.strategies import (
    MovingAverageCrossStrategy,
    RsiReversalStrategy,
    ScriptSignalStrategy,
)


@dataclass(frozen=True)
class BacktestResult:
    symbol: str
    timeframe: str
    strategy: str
    metrics: PerformanceMetrics
    signals: list[object]
    klines: list[Kline]
    broker_result: BrokerResult


def run_ma_cross_backtest(
    symbol: str,
    timeframe: str,
    start_date: str,
    end_date: str,
    initial_cash: float,
    short_window: int = 7,
    long_window: int = 30,
    fee_rate: float = 0.001,
    data_dir: str | Path = "data/sample",
) -> BacktestResult:
    path = build_sample_path(symbol, timeframe, data_dir)
    klines = load_klines(path, start_date=start_date, end_date=end_date)
    return _run_strategy_backtest(
        symbol=symbol,
        timeframe=timeframe,
        strategy_name="ma_cross",
        klines=klines,
        initial_cash=initial_cash,
        fee_rate=fee_rate,
        strategy_cls=MovingAverageCrossStrategy,
        strategy_params={
            "short_window": short_window,
            "long_window": long_window,
        },
    )


def run_script_backtest(
    symbol: str,
    timeframe: str,
    start_date: str,
    end_date: str,
    initial_cash: float,
    code: str,
    params: dict,
    fee_rate: float = 0.001,
    data_dir: str | Path = "data/sample",
    strategy_name: str = "custom_code",
) -> BacktestResult:
    path = build_sample_path(symbol, timeframe, data_dir)
    klines = load_klines(path, start_date=start_date, end_date=end_date)
    strategy_params = dict(params)
    strategy_params["code"] = code
    return _run_strategy_backtest(
        symbol=symbol,
        timeframe=timeframe,
        strategy_name=strategy_name,
        klines=klines,
        initial_cash=initial_cash,
        fee_rate=fee_rate,
        strategy_cls=ScriptSignalStrategy,
        strategy_params=strategy_params,
    )


def run_builtin_backtest(
    strategy_name: str,
    symbol: str,
    timeframe: str,
    start_date: str,
    end_date: str,
    initial_cash: float,
    params: dict,
    fee_rate: float = 0.001,
    data_dir: str | Path = "data/sample",
) -> BacktestResult:
    if strategy_name == "ma_cross":
        return run_ma_cross_backtest(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            initial_cash=initial_cash,
            short_window=int(params.get("short_window", 7)),
            long_window=int(params.get("long_window", 30)),
            fee_rate=fee_rate,
            data_dir=data_dir,
        )
    if strategy_name == "rsi_reversal":
        path = build_sample_path(symbol, timeframe, data_dir)
        klines = load_klines(path, start_date=start_date, end_date=end_date)
        return _run_strategy_backtest(
            symbol=symbol,
            timeframe=timeframe,
            strategy_name="rsi_reversal",
            klines=klines,
            initial_cash=initial_cash,
            fee_rate=fee_rate,
            strategy_cls=RsiReversalStrategy,
            strategy_params={
                "period": int(params.get("period", 14)),
                "oversold": float(params.get("oversold", 30)),
                "overbought": float(params.get("overbought", 70)),
            },
        )

    raise ValueError(f"Unsupported built-in strategy: {strategy_name}")


def _run_strategy_backtest(
    symbol: str,
    timeframe: str,
    strategy_name: str,
    klines: list,
    initial_cash: float,
    fee_rate: float,
    strategy_cls,
    strategy_params: dict,
) -> BacktestResult:
    engine = BacktestEngine()
    engine.add_data(klines)
    engine.set_broker(SimulatedSpotBroker(initial_cash=initial_cash, fee_rate=fee_rate))
    engine.add_strategy(strategy_cls, **strategy_params)
    result = engine.run()
    signals = getattr(result.strategy, "signals", [])

    return BacktestResult(
        symbol=symbol.upper(),
        timeframe=timeframe,
        strategy=strategy_name,
        metrics=result.metrics,
        signals=signals,
        klines=klines,
        broker_result=result.broker_result,
    )
