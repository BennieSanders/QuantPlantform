from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from quant_engine.analyzer import PerformanceMetrics
from quant_engine.broker import BrokerResult, SimulatedSpotBroker
from quant_engine.datafeed import build_sample_path, load_klines
from quant_engine.engine import BacktestEngine
from quant_engine.strategies import MovingAverageCrossStrategy, ScriptSignalStrategy, Signal


@dataclass(frozen=True)
class BacktestResult:
    symbol: str
    timeframe: str
    strategy: str
    metrics: PerformanceMetrics
    signals: list[Signal]
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
        broker_result=result.broker_result,
    )
