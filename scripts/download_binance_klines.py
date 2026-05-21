from __future__ import annotations

import argparse
import csv
import io
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


BASE_URL = "https://data.binance.vision/data/spot/monthly/klines"
CSV_HEADER = ["date", "open", "high", "low", "close", "volume"]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download Binance spot kline CSV files into data/sample."
    )
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--interval", default="1d")
    parser.add_argument("--start", default="2024-01", help="Start month, YYYY-MM")
    parser.add_argument("--end", default="2024-12", help="End month, YYYY-MM")
    parser.add_argument(
        "--output-dir",
        default="data/sample",
        help="Directory for normalized CSV output.",
    )
    args = parser.parse_args()

    symbol = args.symbol.upper()
    months = list(iter_months(args.start, args.end))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{symbol}_{args.interval}.csv"

    rows: list[list[str]] = []
    for year_month in months:
        rows.extend(download_month(symbol, args.interval, year_month))

    if not rows:
        print(f"No rows downloaded for {symbol} {args.interval}", file=sys.stderr)
        return 1

    rows.sort(key=lambda row: row[0])
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(CSV_HEADER)
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {output_path}")
    return 0


def iter_months(start: str, end: str):
    start_year, start_month = parse_year_month(start)
    end_year, end_month = parse_year_month(end)

    year = start_year
    month = start_month
    while (year, month) <= (end_year, end_month):
        yield f"{year:04d}-{month:02d}"
        month += 1
        if month == 13:
            year += 1
            month = 1


def parse_year_month(value: str) -> tuple[int, int]:
    try:
        year_text, month_text = value.split("-", maxsplit=1)
        year = int(year_text)
        month = int(month_text)
    except ValueError as exc:
        raise SystemExit(f"Invalid month {value!r}; expected YYYY-MM") from exc

    if month < 1 or month > 12:
        raise SystemExit(f"Invalid month {value!r}; month must be 01-12")
    return year, month


def download_month(symbol: str, interval: str, year_month: str) -> list[list[str]]:
    url = f"{BASE_URL}/{symbol}/{interval}/{symbol}-{interval}-{year_month}.zip"
    print(f"Downloading {url}")

    try:
        with urlopen(url, timeout=30) as response:
            archive_bytes = response.read()
    except HTTPError as exc:
        if exc.code == 404:
            print(f"Skip missing month: {year_month}", file=sys.stderr)
            return []
        raise
    except URLError as exc:
        raise SystemExit(f"Download failed for {url}: {exc}") from exc

    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        csv_name = archive.namelist()[0]
        with archive.open(csv_name) as file:
            text = io.TextIOWrapper(file, encoding="utf-8")
            reader = csv.reader(text)
            return [normalize_binance_row(row) for row in reader if row]


def normalize_binance_row(row: list[str]) -> list[str]:
    open_time_ms = int(row[0])
    trade_date = datetime.fromtimestamp(open_time_ms / 1000, UTC).date().isoformat()
    return [
        trade_date,
        row[1],
        row[2],
        row[3],
        row[4],
        row[5],
    ]


if __name__ == "__main__":
    raise SystemExit(main())
