from __future__ import annotations

from datetime import date
from typing import Any, Callable

from quant_engine.datafeed import Kline
from quant_engine.strategies.ma_cross import Signal
from quant_engine.strategy import Strategy


SignalFunction = Callable[[list[Kline], dict[str, Any]], list[Any]]


class ScriptSignalStrategy(Strategy):
    def __init__(self, context) -> None:
        super().__init__(context)
        code = str(self.params.get("code", ""))
        self.signal_function = compile_signal_function(code)
        self.processed_signals: set[tuple[date, str]] = set()
        self.signals: list[Signal] = []

    def on_bar(self, kline: Kline) -> None:
        strategy_params = {
            key: value
            for key, value in self.params.items()
            if key not in {"code"}
        }
        generated_signals = self.signal_function(self.context.history, strategy_params)
        for raw_signal in generated_signals:
            signal = _normalize_signal(raw_signal, kline)
            if signal is None or signal.date != kline.date:
                continue

            signal_key = (signal.date, signal.action)
            if signal_key in self.processed_signals:
                continue

            self.processed_signals.add(signal_key)
            self.signals.append(signal)
            if signal.action == "buy":
                self.buy_all(kline)
            elif signal.action == "sell":
                self.sell_all(kline)


def compile_signal_function(code: str) -> SignalFunction:
    if not code.strip():
        raise ValueError("strategy code cannot be empty")

    namespace: dict[str, Any] = {
        "__builtins__": {
            "abs": abs,
            "bool": bool,
            "dict": dict,
            "enumerate": enumerate,
            "float": float,
            "int": int,
            "len": len,
            "list": list,
            "max": max,
            "min": min,
            "range": range,
            "round": round,
            "sum": sum,
            "zip": zip,
        }
    }
    exec(compile(code, "<strategy>", "exec"), namespace)
    signal_function = namespace.get("generate_signals")
    if not callable(signal_function):
        raise ValueError("custom strategy must define generate_signals(klines, params)")
    return signal_function


def _normalize_signal(raw_signal: Any, kline: Kline) -> Signal | None:
    if isinstance(raw_signal, Signal):
        return raw_signal
    if not isinstance(raw_signal, dict):
        return None

    action = raw_signal.get("action")
    if action not in {"buy", "sell"}:
        return None

    signal_date = raw_signal.get("date", kline.date)
    if isinstance(signal_date, str):
        signal_date = date.fromisoformat(signal_date)
    if not isinstance(signal_date, date):
        return None

    price = float(raw_signal.get("price", kline.close))
    return Signal(
        date=signal_date,
        action=action,
        price=price,
        short_ma=float(raw_signal.get("short_ma", 0.0)),
        long_ma=float(raw_signal.get("long_ma", 0.0)),
    )
