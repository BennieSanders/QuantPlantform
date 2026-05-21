from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from quant_engine.datafeed import Kline
from quant_engine.models import BrokerResult, Order


ExchangeName = Literal["binance", "okx"]
TradingMode = Literal["backtest", "paper", "live"]


@dataclass(frozen=True)
class ExchangeCredentialsRef:
    exchange: ExchangeName
    account_label: str


class ExchangeBroker:
    """Base shape for future live exchange adapters.

    This class intentionally does not implement real order placement. Concrete
    adapters must add authentication, exchange filters, balances, order status
    sync, rate limits, and fail-safe handling before live trading is enabled.
    """

    def __init__(self, credentials: ExchangeCredentialsRef) -> None:
        self.credentials = credentials

    @property
    def initial_cash(self) -> float:
        raise NotImplementedError

    def submit_order(self, order: Order) -> Order:
        raise NotImplementedError

    def buy_all(self, created_at=None) -> Order:
        raise NotImplementedError

    def sell_all(self, created_at=None) -> Order:
        raise NotImplementedError

    def buy(self, quantity: float, created_at=None) -> Order:
        raise NotImplementedError

    def sell(self, quantity: float, created_at=None) -> Order:
        raise NotImplementedError

    def execute_pending_orders(self, kline: Kline) -> None:
        raise NotImplementedError

    def mark_to_market(self, kline: Kline) -> None:
        raise NotImplementedError

    def result(self) -> BrokerResult:
        raise NotImplementedError
