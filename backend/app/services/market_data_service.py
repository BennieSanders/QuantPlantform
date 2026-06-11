from __future__ import annotations

from datetime import UTC, datetime
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
    rows = (fetcher or fetch_binance_klines)(payload.symbol, payload.timeframe, payload.limit)
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
) -> MarketSeriesResponse:
    limit = min(max(limit, 1), 1000)
    rows = list(
        reversed(
            db.scalars(
                select(MarketKline)
                .where(
                    MarketKline.symbol == symbol.upper(),
                    MarketKline.timeframe == timeframe,
                )
                .order_by(MarketKline.open_time.desc())
                .limit(limit)
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


def fetch_binance_klines(symbol: str, timeframe: str, limit: int) -> list[list]:
    settings = get_settings()
    query = urlencode({"symbol": symbol.upper(), "interval": timeframe, "limit": limit})
    request = Request(
        f"{settings.market_data_base_url}/api/v3/klines?{query}",
        headers={"User-Agent": "quant-platform/0.1"},
    )
    with urlopen(request, timeout=settings.market_data_timeout_seconds) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Market data provider returned an invalid response")
    return payload


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
