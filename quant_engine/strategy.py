from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from quant_engine.broker.base import Broker
from quant_engine.datafeed import Kline


@dataclass
class StrategyContext:
    broker: Broker
    params: dict[str, Any]
    history: list[Kline] = field(default_factory=list)


class Strategy:
    def __init__(self, context: StrategyContext) -> None:
        self.context = context

    @property
    def params(self) -> dict[str, Any]:
        return self.context.params

    @property
    def broker(self) -> Broker:
        return self.context.broker

    def on_start(self) -> None:
        pass

    def on_bar(self, kline: Kline) -> None:
        raise NotImplementedError

    def on_finish(self) -> None:
        pass

    def buy_all(self, kline: Kline) -> None:
        self.broker.buy_all(created_at=kline.date)

    def sell_all(self, kline: Kline) -> None:
        self.broker.sell_all(created_at=kline.date)
