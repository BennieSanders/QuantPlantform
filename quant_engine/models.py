from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from itertools import count


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, Enum):
    SUBMITTED = "submitted"
    FILLED = "filled"
    REJECTED = "rejected"


class OrderSizeType(str, Enum):
    QUANTITY = "quantity"
    ALL_CASH = "all_cash"
    ALL_POSITION = "all_position"


_order_id_counter = count(1)


@dataclass(frozen=True)
class Order:
    side: OrderSide
    size_type: OrderSizeType
    quantity: float | None = None
    created_at: date | None = None
    id: str = field(default_factory=lambda: f"ord-{next(_order_id_counter)}")


@dataclass(frozen=True)
class OrderEvent:
    order_id: str
    status: OrderStatus
    date: date | None = None
    message: str = ""
    price: float | None = None
    quantity: float | None = None


@dataclass(frozen=True)
class Trade:
    date: date
    side: str
    price: float
    quantity: float
    fee: float
    cash_after: float
    position_after: float
    order_id: str | None = None


@dataclass(frozen=True)
class EquityPoint:
    date: date
    equity: float
    cash: float
    position: float
    close: float


@dataclass(frozen=True)
class Position:
    quantity: float = 0.0
    average_price: float = 0.0


@dataclass(frozen=True)
class BrokerResult:
    trades: list[Trade]
    equity_curve: list[EquityPoint]
    final_cash: float
    final_position: float
    orders: list[Order] = field(default_factory=list)
    order_events: list[OrderEvent] = field(default_factory=list)
