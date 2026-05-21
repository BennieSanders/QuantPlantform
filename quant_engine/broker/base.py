from __future__ import annotations

from typing import Protocol

from quant_engine.datafeed import Kline
from quant_engine.models import BrokerResult, Order


class Broker(Protocol):
    initial_cash: float

    def submit_order(self, order: Order) -> Order:
        ...

    def buy_all(self, created_at=None) -> Order:
        ...

    def sell_all(self, created_at=None) -> Order:
        ...

    def buy(self, quantity: float, created_at=None) -> Order:
        ...

    def sell(self, quantity: float, created_at=None) -> Order:
        ...

    def execute_pending_orders(self, kline: Kline) -> None:
        ...

    def mark_to_market(self, kline: Kline) -> None:
        ...

    def result(self) -> BrokerResult:
        ...
