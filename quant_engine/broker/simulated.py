from __future__ import annotations

from dataclasses import dataclass, field

from quant_engine.datafeed import Kline
from quant_engine.models import (
    BrokerResult,
    EquityPoint,
    Order,
    OrderEvent,
    OrderSide,
    OrderSizeType,
    OrderStatus,
    Position,
    Trade,
)
from quant_engine.risk import RiskContext, RiskManager


@dataclass
class SimulatedSpotBroker:
    initial_cash: float
    fee_rate: float = 0.001
    risk_manager: RiskManager = field(default_factory=RiskManager)
    cash: float = field(init=False)
    position: Position = field(init=False)
    pending_orders: list[Order] = field(default_factory=list, init=False)
    orders: list[Order] = field(default_factory=list, init=False)
    order_events: list[OrderEvent] = field(default_factory=list, init=False)
    trades: list[Trade] = field(default_factory=list, init=False)
    equity_curve: list[EquityPoint] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        if self.initial_cash <= 0:
            raise ValueError("initial_cash must be positive")
        if self.fee_rate < 0:
            raise ValueError("fee_rate must be non-negative")
        self.cash = self.initial_cash
        self.position = Position()

    def submit_order(self, order: Order) -> Order:
        decision = self.risk_manager.validate_order(
            order,
            RiskContext(
                cash=self.cash,
                position=self.position,
            ),
        )
        if not decision.accepted:
            self.orders.append(order)
            self.order_events.append(
                OrderEvent(
                    order_id=order.id,
                    status=OrderStatus.REJECTED,
                    date=order.created_at,
                    message=decision.reason,
                )
            )
            return order

        self.pending_orders.append(order)
        self.orders.append(order)
        self.order_events.append(
            OrderEvent(
                order_id=order.id,
                status=OrderStatus.SUBMITTED,
                date=order.created_at,
            )
        )
        return order

    def buy_all(self, created_at=None) -> Order:
        return self.submit_order(
            Order(
                side=OrderSide.BUY,
                size_type=OrderSizeType.ALL_CASH,
                created_at=created_at,
            )
        )

    def sell_all(self, created_at=None) -> Order:
        return self.submit_order(
            Order(
                side=OrderSide.SELL,
                size_type=OrderSizeType.ALL_POSITION,
                created_at=created_at,
            )
        )

    def buy(self, quantity: float, created_at=None) -> Order:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        return self.submit_order(
            Order(
                side=OrderSide.BUY,
                size_type=OrderSizeType.QUANTITY,
                quantity=quantity,
                created_at=created_at,
            )
        )

    def sell(self, quantity: float, created_at=None) -> Order:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        return self.submit_order(
            Order(
                side=OrderSide.SELL,
                size_type=OrderSizeType.QUANTITY,
                quantity=quantity,
                created_at=created_at,
            )
        )

    def execute_pending_orders(self, kline: Kline) -> None:
        orders = self.pending_orders
        self.pending_orders = []

        for order in orders:
            price = kline.open
            if price <= 0:
                self._reject_order(order, kline, "execution price must be positive")
                continue
            if order.side == OrderSide.BUY:
                self._execute_buy(order, price, kline)
            elif order.side == OrderSide.SELL:
                self._execute_sell(order, price, kline)

    def mark_to_market(self, kline: Kline) -> None:
        equity = self.cash + self.position.quantity * kline.close
        self.equity_curve.append(
            EquityPoint(
                date=kline.date,
                equity=round(equity, 6),
                cash=round(self.cash, 6),
                position=round(self.position.quantity, 10),
                close=kline.close,
            )
        )

    def result(self) -> BrokerResult:
        return BrokerResult(
            trades=self.trades,
            equity_curve=self.equity_curve,
            final_cash=round(self.cash, 6),
            final_position=round(self.position.quantity, 10),
            orders=self.orders,
            order_events=self.order_events,
        )

    def _execute_buy(self, order: Order, price: float, kline: Kline) -> None:
        if self.position.quantity > 0:
            self._reject_order(order, kline, "long-only broker already has an open position")
            return

        if order.size_type == OrderSizeType.ALL_CASH:
            quantity = self.cash / (price * (1 + self.fee_rate))
        else:
            quantity = order.quantity or 0.0

        gross_cost = quantity * price
        fee = gross_cost * self.fee_rate
        total_cost = gross_cost + fee
        if quantity <= 0 or total_cost > self.cash + 1e-9:
            self._reject_order(order, kline, "cash is not enough to fill the order")
            return

        self.cash = _clean_zero(self.cash - total_cost)
        self.position = Position(quantity=quantity, average_price=price)
        self.order_events.append(
            OrderEvent(
                order_id=order.id,
                status=OrderStatus.FILLED,
                date=kline.date,
                price=round(price, 6),
                quantity=round(quantity, 10),
            )
        )
        self.trades.append(
            Trade(
                date=kline.date,
                side="buy",
                price=price,
                quantity=round(quantity, 10),
                fee=round(fee, 6),
                cash_after=round(self.cash, 6),
                position_after=round(self.position.quantity, 10),
                order_id=order.id,
            )
        )

    def _execute_sell(self, order: Order, price: float, kline: Kline) -> None:
        if self.position.quantity <= 0:
            self._reject_order(order, kline, "no position available to sell")
            return

        if order.size_type == OrderSizeType.ALL_POSITION:
            quantity = self.position.quantity
        else:
            quantity = min(order.quantity or 0.0, self.position.quantity)
        if quantity <= 0:
            self._reject_order(order, kline, "quantity must be positive")
            return

        gross_value = quantity * price
        fee = gross_value * self.fee_rate
        self.cash = self.cash + gross_value - fee
        remaining_quantity = _clean_zero(self.position.quantity - quantity)
        self.position = Position(
            quantity=remaining_quantity,
            average_price=self.position.average_price if remaining_quantity > 0 else 0.0,
        )
        self.order_events.append(
            OrderEvent(
                order_id=order.id,
                status=OrderStatus.FILLED,
                date=kline.date,
                price=round(price, 6),
                quantity=round(quantity, 10),
            )
        )
        self.trades.append(
            Trade(
                date=kline.date,
                side="sell",
                price=price,
                quantity=round(quantity, 10),
                fee=round(fee, 6),
                cash_after=round(self.cash, 6),
                position_after=round(self.position.quantity, 10),
                order_id=order.id,
            )
        )

    def _reject_order(self, order: Order, kline: Kline, message: str) -> None:
        self.order_events.append(
            OrderEvent(
                order_id=order.id,
                status=OrderStatus.REJECTED,
                date=kline.date,
                message=message,
            )
        )


def _clean_zero(value: float) -> float:
    if abs(value) < 1e-9:
        return 0.0
    return value
