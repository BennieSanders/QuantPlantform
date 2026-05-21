from __future__ import annotations

from dataclasses import dataclass

from quant_engine.models import EquityPoint, Trade


@dataclass(frozen=True)
class PerformanceMetrics:
    total_return: float
    max_drawdown: float
    trade_count: int
    win_rate: float
    final_equity: float


def analyze_performance(
    equity_curve: list[EquityPoint],
    trades: list[Trade],
    initial_cash: float,
) -> PerformanceMetrics:
    if not equity_curve:
        raise ValueError("equity_curve cannot be empty")
    if initial_cash <= 0:
        raise ValueError("initial_cash must be positive")

    final_equity = equity_curve[-1].equity
    total_return = final_equity / initial_cash - 1
    max_drawdown = _calculate_max_drawdown(equity_curve)
    win_rate = _calculate_win_rate(trades)

    return PerformanceMetrics(
        total_return=round(total_return, 6),
        max_drawdown=round(max_drawdown, 6),
        trade_count=len(trades),
        win_rate=round(win_rate, 6),
        final_equity=round(final_equity, 6),
    )


def _calculate_max_drawdown(equity_curve: list[EquityPoint]) -> float:
    peak = equity_curve[0].equity
    max_drawdown = 0.0

    for point in equity_curve:
        peak = max(peak, point.equity)
        drawdown = point.equity / peak - 1
        max_drawdown = min(max_drawdown, drawdown)

    return max_drawdown


def _calculate_win_rate(trades: list[Trade]) -> float:
    round_trips = []
    current_buy: Trade | None = None

    for trade in trades:
        if trade.side == "buy":
            current_buy = trade
        elif trade.side == "sell" and current_buy is not None:
            round_trips.append((current_buy, trade))
            current_buy = None

    if not round_trips:
        return 0.0

    wins = 0
    for buy, sell in round_trips:
        if sell.price > buy.price:
            wins += 1

    return wins / len(round_trips)
