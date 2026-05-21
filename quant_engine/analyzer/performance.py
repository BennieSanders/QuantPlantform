from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from statistics import mean, stdev

from quant_engine.models import EquityPoint, Trade


@dataclass(frozen=True)
class PerformanceMetrics:
    total_return: float
    annualized_return: float
    max_drawdown: float
    sharpe_ratio: float
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
    annualized_return = _calculate_annualized_return(equity_curve, total_return)
    max_drawdown = _calculate_max_drawdown(equity_curve)
    sharpe_ratio = _calculate_sharpe_ratio(equity_curve)
    win_rate = _calculate_win_rate(trades)

    return PerformanceMetrics(
        total_return=round(total_return, 6),
        annualized_return=round(annualized_return, 6),
        max_drawdown=round(max_drawdown, 6),
        sharpe_ratio=round(sharpe_ratio, 6),
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


def _calculate_annualized_return(equity_curve: list[EquityPoint], total_return: float) -> float:
    start_date = equity_curve[0].date
    end_date = equity_curve[-1].date
    days = (end_date - start_date).days
    if days <= 0:
        return total_return

    return (1 + total_return) ** (365 / days) - 1


def _calculate_sharpe_ratio(equity_curve: list[EquityPoint]) -> float:
    returns = []
    previous_equity = equity_curve[0].equity

    for point in equity_curve[1:]:
        if previous_equity <= 0:
            previous_equity = point.equity
            continue
        returns.append(point.equity / previous_equity - 1)
        previous_equity = point.equity

    if len(returns) < 2:
        return 0.0

    volatility = stdev(returns)
    if volatility == 0:
        return 0.0

    return mean(returns) / volatility * sqrt(365)


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
