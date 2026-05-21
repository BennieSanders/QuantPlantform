from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

from quant_engine.datafeed import Kline
from quant_engine.strategy import Strategy


SignalAction = Literal["buy", "sell"]


@dataclass(frozen=True)
class Signal:
    date: date
    action: SignalAction
    price: float
    short_ma: float
    long_ma: float


class MovingAverageCrossStrategy(Strategy):
    def __init__(self, context) -> None:
        super().__init__(context)
        self.short_window = int(self.params.get("short_window", 7))
        self.long_window = int(self.params.get("long_window", 30))
        if self.short_window <= 0 or self.long_window <= 0:
            raise ValueError("MA windows must be positive")
        if self.short_window >= self.long_window:
            raise ValueError("short_window must be smaller than long_window")

        self.previous_relation: int | None = None
        self.signals: list[Signal] = []

    def on_bar(self, kline: Kline) -> None:
        history = self.context.history
        if len(history) < self.long_window:
            return

        closes = [item.close for item in history]
        short_ma = _mean(closes[-self.short_window :])
        long_ma = _mean(closes[-self.long_window :])
        current_relation = _compare(short_ma, long_ma)

        if self.previous_relation is not None:
            if self.previous_relation <= 0 and current_relation > 0:
                self.signals.append(
                    Signal(
                        date=kline.date,
                        action="buy",
                        price=kline.close,
                        short_ma=round(short_ma, 6),
                        long_ma=round(long_ma, 6),
                    )
                )
                self.buy_all(kline)
            elif self.previous_relation >= 0 and current_relation < 0:
                self.signals.append(
                    Signal(
                        date=kline.date,
                        action="sell",
                        price=kline.close,
                        short_ma=round(short_ma, 6),
                        long_ma=round(long_ma, 6),
                    )
                )
                self.sell_all(kline)

        if current_relation != 0:
            self.previous_relation = current_relation


def generate_ma_cross_signals(
    klines: list[Kline],
    short_window: int = 7,
    long_window: int = 30,
) -> list[Signal]:
    if short_window <= 0 or long_window <= 0:
        raise ValueError("MA windows must be positive")
    if short_window >= long_window:
        raise ValueError("short_window must be smaller than long_window")
    if len(klines) < long_window:
        return []

    closes = [kline.close for kline in klines]
    signals: list[Signal] = []
    previous_relation: int | None = None

    for index in range(long_window - 1, len(klines)):
        short_ma = _mean(closes[index - short_window + 1 : index + 1])
        long_ma = _mean(closes[index - long_window + 1 : index + 1])
        current_relation = _compare(short_ma, long_ma)

        if previous_relation is not None:
            if previous_relation <= 0 and current_relation > 0:
                signals.append(
                    Signal(
                        date=klines[index].date,
                        action="buy",
                        price=klines[index].close,
                        short_ma=round(short_ma, 6),
                        long_ma=round(long_ma, 6),
                    )
                )
            elif previous_relation >= 0 and current_relation < 0:
                signals.append(
                    Signal(
                        date=klines[index].date,
                        action="sell",
                        price=klines[index].close,
                        short_ma=round(short_ma, 6),
                        long_ma=round(long_ma, 6),
                    )
                )

        current_is_crossable = current_relation != 0
        if current_is_crossable:
            previous_relation = current_relation

    return signals


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _compare(left: float, right: float) -> int:
    if left > right:
        return 1
    if left < right:
        return -1
    return 0
