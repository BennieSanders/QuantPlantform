from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

from quant_engine.datafeed import Kline
from quant_engine.strategy import Strategy


SignalAction = Literal["buy", "sell"]


@dataclass(frozen=True)
class RsiSignal:
    date: date
    action: SignalAction
    price: float
    rsi: float


class RsiReversalStrategy(Strategy):
    def __init__(self, context) -> None:
        super().__init__(context)
        self.period = int(self.params.get("period", 14))
        self.oversold = float(self.params.get("oversold", 30))
        self.overbought = float(self.params.get("overbought", 70))
        if self.period <= 1:
            raise ValueError("RSI period must be greater than 1")
        if not 0 < self.oversold < self.overbought < 100:
            raise ValueError("RSI thresholds must satisfy 0 < oversold < overbought < 100")

        self.in_position = False
        self.signals: list[RsiSignal] = []

    def on_bar(self, kline: Kline) -> None:
        history = self.context.history
        if len(history) < self.period + 1:
            return

        closes = [item.close for item in history]
        rsi = calculate_rsi(closes[-self.period - 1 :])

        if not self.in_position and rsi <= self.oversold:
            self.signals.append(
                RsiSignal(
                    date=kline.date,
                    action="buy",
                    price=kline.close,
                    rsi=round(rsi, 6),
                )
            )
            self.buy_all(kline)
            self.in_position = True
        elif self.in_position and rsi >= self.overbought:
            self.signals.append(
                RsiSignal(
                    date=kline.date,
                    action="sell",
                    price=kline.close,
                    rsi=round(rsi, 6),
                )
            )
            self.sell_all(kline)
            self.in_position = False


def calculate_rsi(closes: list[float]) -> float:
    if len(closes) < 2:
        raise ValueError("at least two closes are required")

    gains = []
    losses = []
    for previous, current in zip(closes, closes[1:]):
        change = current - previous
        gains.append(max(change, 0.0))
        losses.append(max(-change, 0.0))

    average_gain = sum(gains) / len(gains)
    average_loss = sum(losses) / len(losses)
    if average_loss == 0:
        return 100.0

    relative_strength = average_gain / average_loss
    return 100 - (100 / (1 + relative_strength))
