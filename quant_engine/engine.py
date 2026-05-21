from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Type

from quant_engine.analyzer import PerformanceMetrics, analyze_performance
from quant_engine.broker.base import Broker
from quant_engine.datafeed import Kline
from quant_engine.models import BrokerResult
from quant_engine.strategy import Strategy, StrategyContext


@dataclass(frozen=True)
class EngineResult:
    broker_result: BrokerResult
    metrics: PerformanceMetrics
    strategy: Strategy


@dataclass
class BacktestEngine:
    data: list[Kline] = field(default_factory=list)
    broker: Broker | None = None
    strategy_cls: Type[Strategy] | None = None
    strategy_params: dict[str, Any] = field(default_factory=dict)

    def add_data(self, data: list[Kline]) -> None:
        if not data:
            raise ValueError("data cannot be empty")
        self.data = data

    def set_broker(self, broker: Broker) -> None:
        self.broker = broker

    def add_strategy(self, strategy_cls: Type[Strategy], **params: Any) -> None:
        self.strategy_cls = strategy_cls
        self.strategy_params = params

    def run(self) -> EngineResult:
        if not self.data:
            raise ValueError("data feed is required")
        if self.broker is None:
            raise ValueError("broker is required")
        if self.strategy_cls is None:
            raise ValueError("strategy is required")

        context = StrategyContext(
            broker=self.broker,
            params=self.strategy_params,
        )
        strategy = self.strategy_cls(context)
        strategy.on_start()

        for kline in self.data:
            self.broker.execute_pending_orders(kline)
            context.history.append(kline)
            strategy.on_bar(kline)
            self.broker.mark_to_market(kline)

        strategy.on_finish()
        broker_result = self.broker.result()
        metrics = analyze_performance(
            equity_curve=broker_result.equity_curve,
            trades=broker_result.trades,
            initial_cash=self.broker.initial_cash,
        )
        return EngineResult(
            broker_result=broker_result,
            metrics=metrics,
            strategy=strategy,
        )
