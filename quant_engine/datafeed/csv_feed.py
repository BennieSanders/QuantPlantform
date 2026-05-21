from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class Kline:
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float


def load_klines(
    file_path: str | Path,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[Kline]:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"K-line CSV not found: {path}")

    start = _parse_optional_date(start_date)
    end = _parse_optional_date(end_date)
    if start and end and start > end:
        raise ValueError("start_date must be earlier than or equal to end_date")

    klines: list[Kline] = []
    first_date: date | None = None
    last_date: date | None = None
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        _validate_header(reader.fieldnames)

        for row in reader:
            kline = _parse_row(row)
            if first_date is None or kline.date < first_date:
                first_date = kline.date
            if last_date is None or kline.date > last_date:
                last_date = kline.date
            if start and kline.date < start:
                continue
            if end and kline.date > end:
                continue
            klines.append(kline)

    if not klines:
        requested_range = _format_requested_range(start, end)
        available_range = _format_available_range(first_date, last_date)
        raise ValueError(
            f"No K-line rows loaded from {path} for {requested_range}. "
            f"Available data: {available_range}"
        )

    return klines


def build_sample_path(symbol: str, timeframe: str, data_dir: str | Path) -> Path:
    return Path(data_dir) / f"{symbol.upper()}_{timeframe}.csv"


def _validate_header(fieldnames: list[str] | None) -> None:
    expected = ["date", "open", "high", "low", "close", "volume"]
    if fieldnames != expected:
        raise ValueError(f"Invalid CSV header: expected {expected}, got {fieldnames}")


def _parse_row(row: dict[str, str]) -> Kline:
    return Kline(
        date=date.fromisoformat(row["date"]),
        open=float(row["open"]),
        high=float(row["high"]),
        low=float(row["low"]),
        close=float(row["close"]),
        volume=float(row["volume"]),
    )


def _parse_optional_date(value: str | None) -> date | None:
    if value is None:
        return None
    return date.fromisoformat(value)


def _format_requested_range(start: date | None, end: date | None) -> str:
    if start and end:
        return f"requested range {start.isoformat()} to {end.isoformat()}"
    if start:
        return f"requested range starting {start.isoformat()}"
    if end:
        return f"requested range ending {end.isoformat()}"
    return "the requested range"


def _format_available_range(start: date | None, end: date | None) -> str:
    if start and end:
        return f"{start.isoformat()} to {end.isoformat()}"
    return "unknown"
