from __future__ import annotations

from typing import Literal

from quant_engine.datafeed import Kline
from quant_engine.models import BrokerResult, EquityPoint, Trade
from quant_engine.strategies import Signal


TradeSide = Literal["buy", "sell"]


def run_spot_long_only(
    klines: list[Kline],
    signals: list[Signal],
    initial_cash: float,
    fee_rate: float = 0.001,
) -> BrokerResult:
    if initial_cash <= 0:
        raise ValueError("initial_cash must be positive")
    if fee_rate < 0:
        raise ValueError("fee_rate must be non-negative")

    cash = initial_cash
    position = 0.0
    trades: list[Trade] = []
    equity_curve: list[EquityPoint] = []
    signals_by_date = {signal.date: signal for signal in signals}

    for kline in klines:
        signal = signals_by_date.get(kline.date)
        if signal and signal.action == "buy" and position == 0 and cash > 0:
            quantity = cash / (signal.price * (1 + fee_rate))
            gross_cost = quantity * signal.price
            fee = gross_cost * fee_rate
            cash = cash - gross_cost - fee
            cash = _clean_zero(cash)
            position = quantity
            trades.append(
                Trade(
                    date=kline.date,
                    side="buy",
                    price=signal.price,
                    quantity=round(quantity, 10),
                    fee=round(fee, 6),
                    cash_after=round(cash, 6),
                    position_after=round(position, 10),
                )
            )
        elif signal and signal.action == "sell" and position > 0:
            gross_value = position * signal.price
            fee = gross_value * fee_rate
            cash = gross_value - fee
            trades.append(
                Trade(
                    date=kline.date,
                    side="sell",
                    price=signal.price,
                    quantity=round(position, 10),
                    fee=round(fee, 6),
                    cash_after=round(cash, 6),
                    position_after=0.0,
                )
            )
            position = 0.0

        equity = cash + position * kline.close
        equity_curve.append(
            EquityPoint(
                date=kline.date,
                equity=round(equity, 6),
                cash=round(cash, 6),
                position=round(position, 10),
                close=kline.close,
            )
        )

    return BrokerResult(
        trades=trades,
        equity_curve=equity_curve,
        final_cash=round(cash, 6),
        final_position=round(position, 10),
    )


def _clean_zero(value: float) -> float:
    if abs(value) < 1e-9:
        return 0.0
    return value
