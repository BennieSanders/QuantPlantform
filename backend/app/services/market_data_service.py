from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
from typing import Callable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.market_kline import MarketKline
from app.schemas.market import (
    MarketKlineResponse,
    MarketSeriesResponse,
    MarketSyncRequest,
    MarketSyncResponse,
)


KlineFetcher = Callable[[str, str, int], list[list]]


def sync_market_klines(
    payload: MarketSyncRequest,
    db: Session,
    fetcher: KlineFetcher | None = None,
) -> MarketSyncResponse:
    if fetcher:
        rows = fetcher(payload.symbol, payload.timeframe, payload.limit)
    else:
        start_time = _shanghai_day_start_utc() if payload.range == "today_shanghai" else None
        rows = fetch_binance_klines(
            payload.symbol,
            payload.timeframe,
            payload.limit,
            start_time=start_time,
        )
    inserted = 0
    updated = 0
    latest_open_time: datetime | None = None
    now = datetime.now(UTC)

    for row in rows:
        values = _parse_binance_row(payload.symbol, payload.timeframe, row, now)
        latest_open_time = max(latest_open_time, values["open_time"]) if latest_open_time else values["open_time"]
        existing = db.get(MarketKline, values["id"])
        if existing is None:
            db.add(MarketKline(**values))
            inserted += 1
            continue
        for key, value in values.items():
            if key != "id":
                setattr(existing, key, value)
        updated += 1

    db.commit()
    return MarketSyncResponse(
        symbol=payload.symbol,
        timeframe=payload.timeframe,
        fetched=len(rows),
        inserted=inserted,
        updated=updated,
        latest_open_time=latest_open_time.isoformat() if latest_open_time else None,
    )


def get_market_series(
    db: Session,
    symbol: str,
    timeframe: str,
    limit: int = 200,
    range_name: str = "latest",
) -> MarketSeriesResponse:
    limit = min(max(limit, 1), 2000)
    query = select(MarketKline).where(
        MarketKline.symbol == symbol.upper(),
        MarketKline.timeframe == timeframe,
    )
    if range_name == "today_shanghai":
        query = query.where(MarketKline.open_time >= _shanghai_day_start_utc())
    rows = list(
        reversed(
            db.scalars(
                query.order_by(MarketKline.open_time.desc()).limit(limit)
            ).all()
        )
    )
    last_price = rows[-1].close if rows else None
    first_price = rows[0].open if rows else None
    change_rate = None
    if last_price is not None and first_price:
        change_rate = round(last_price / first_price - 1, 6)

    return MarketSeriesResponse(
        symbol=symbol.upper(),
        timeframe=timeframe,
        count=len(rows),
        last_price=last_price,
        change_rate=change_rate,
        last_open_time=rows[-1].open_time.isoformat() if rows else None,
        last_ingested_at=rows[-1].ingested_at.isoformat() if rows else None,
        klines=[_to_response(row) for row in rows],
    )


def fetch_binance_klines(
    symbol: str,
    timeframe: str,
    limit: int,
    start_time: datetime | None = None,
) -> list[list]:
    settings = get_settings()
    remaining = min(max(limit, 1), 2000)
    next_start_ms = int(start_time.timestamp() * 1000) if start_time else None
    rows: list[list] = []

    while remaining > 0:
        request_limit = min(remaining, 1000)
        params = {
            "symbol": symbol.upper(),
            "interval": timeframe,
            "limit": request_limit,
        }
        if next_start_ms is not None:
            params["startTime"] = next_start_ms
        query = urlencode(params)
        request = Request(
            f"{settings.market_data_base_url}/api/v3/klines?{query}",
            headers={"User-Agent": "quant-platform/0.1"},
        )
        with urlopen(request, timeout=settings.market_data_timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if not isinstance(payload, list):
            raise ValueError("Market data provider returned an invalid response")
        if not payload:
            break

        rows.extend(payload)
        remaining -= len(payload)
        if next_start_ms is None or len(payload) < request_limit:
            break
        next_start_ms = int(payload[-1][6]) + 1

    return rows


def _shanghai_day_start_utc(now: datetime | None = None) -> datetime:
    current_utc = now or datetime.now(UTC)
    shanghai_now = current_utc + timedelta(hours=8)
    shanghai_midnight_as_utc = datetime(
        shanghai_now.year,
        shanghai_now.month,
        shanghai_now.day,
        tzinfo=UTC,
    )
    return shanghai_midnight_as_utc - timedelta(hours=8)


def _parse_binance_row(symbol: str, timeframe: str, row: list, now: datetime) -> dict:
    if len(row) < 7:
        raise ValueError("Market data row is incomplete")
    open_time = datetime.fromtimestamp(int(row[0]) / 1000, tz=UTC)
    close_time = datetime.fromtimestamp(int(row[6]) / 1000, tz=UTC)
    return {
        "id": f"{symbol.upper()}:{timeframe}:{int(row[0])}",
        "symbol": symbol.upper(),
        "timeframe": timeframe,
        "open_time": open_time,
        "close_time": close_time,
        "open": float(row[1]),
        "high": float(row[2]),
        "low": float(row[3]),
        "close": float(row[4]),
        "volume": float(row[5]),
        "source": "binance",
        "ingested_at": now,
    }


def _to_response(row: MarketKline) -> MarketKlineResponse:
    return MarketKlineResponse(
        symbol=row.symbol,
        timeframe=row.timeframe,
        open_time=row.open_time.isoformat(),
        close_time=row.close_time.isoformat(),
        open=row.open,
        high=row.high,
        low=row.low,
        close=row.close,
        volume=row.volume,
        source=row.source,
    )
