from __future__ import annotations

from dataclasses import dataclass

from quant_engine.models import Order, OrderSide, OrderSizeType, Position


@dataclass(frozen=True)
class RiskDecision:
    accepted: bool
    reason: str = ""


@dataclass(frozen=True)
class RiskContext:
    cash: float
    position: Position
    last_price: float | None = None


class RiskManager:
    def validate_order(self, order: Order, context: RiskContext) -> RiskDecision:
        if order.size_type == OrderSizeType.QUANTITY:
            if order.quantity is None or order.quantity <= 0:
                return RiskDecision(False, "quantity must be positive")

        if order.side == OrderSide.BUY and context.position.quantity > 0:
            return RiskDecision(False, "long-only broker already has an open position")

        if order.side == OrderSide.SELL and context.position.quantity <= 0:
            return RiskDecision(False, "no position available to sell")

        if order.side == OrderSide.BUY and context.cash <= 0:
            return RiskDecision(False, "cash is not available")

        return RiskDecision(True)
