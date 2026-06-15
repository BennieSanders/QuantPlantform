import os
import sys
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(BACKEND_ROOT))


def clear_app_modules() -> None:
    for module_name in list(sys.modules):
        if module_name == "app" or module_name.startswith("app."):
            del sys.modules[module_name]


class MarketDataServiceTest(unittest.TestCase):
    def test_shanghai_day_start_is_converted_to_utc(self) -> None:
        from app.services.market_data_service import _shanghai_day_start_utc

        start = _shanghai_day_start_utc(datetime(2026, 6, 11, 10, 30, tzinfo=UTC))
        self.assertEqual(start, datetime(2026, 6, 10, 16, 0, tzinfo=UTC))

    def test_sync_upserts_and_returns_ordered_series(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            clear_app_modules()
            os.environ["QUANT_PLATFORM_DATABASE_URL"] = (
                f"sqlite:///{Path(tmp_dir) / 'test.db'}"
            )

            from app.core.database import SessionLocal, init_db
            from app.schemas.market import MarketSyncRequest
            from app.services.market_data_service import get_market_series, sync_market_klines

            rows = [
                [1_700_000_000_000, "100", "110", "90", "105", "12", 1_700_000_059_999],
                [1_700_000_060_000, "105", "115", "101", "112", "14", 1_700_000_119_999],
            ]
            init_db()
            with SessionLocal() as db:
                result = sync_market_klines(
                    MarketSyncRequest(symbol="BTCUSDT", timeframe="1m", limit=2),
                    db,
                    fetcher=lambda _symbol, _timeframe, _limit: rows,
                )
                self.assertEqual(result.inserted, 2)
                self.assertEqual(result.updated, 0)

                rows[-1][4] = "113"
                second = sync_market_klines(
                    MarketSyncRequest(symbol="BTCUSDT", timeframe="1m", limit=2),
                    db,
                    fetcher=lambda _symbol, _timeframe, _limit: rows,
                )
                self.assertEqual(second.inserted, 0)
                self.assertEqual(second.updated, 2)

                series = get_market_series(db, "BTCUSDT", "1m", limit=10)
                self.assertEqual(series.count, 2)
                self.assertEqual(series.last_price, 113)
                self.assertGreater(series.change_rate, 0)
                self.assertLess(series.klines[0].open_time, series.klines[1].open_time)

    def test_market_series_reports_gap_health(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            clear_app_modules()
            os.environ["QUANT_PLATFORM_DATABASE_URL"] = (
                f"sqlite:///{Path(tmp_dir) / 'test.db'}"
            )

            from app.core.database import SessionLocal, init_db
            from app.schemas.market import MarketSyncRequest
            from app.services.market_data_service import get_market_series, sync_market_klines

            rows = [
                [1_700_000_000_000, "100", "110", "90", "105", "12", 1_700_000_059_999],
                [1_700_000_120_000, "105", "115", "101", "112", "14", 1_700_000_179_999],
                [1_700_000_180_000, "112", "116", "108", "114", "16", 1_700_000_239_999],
            ]
            init_db()
            with SessionLocal() as db:
                sync_market_klines(
                    MarketSyncRequest(symbol="BTCUSDT", timeframe="1m", limit=3),
                    db,
                    fetcher=lambda _symbol, _timeframe, _limit: rows,
                )

                series = get_market_series(db, "BTCUSDT", "1m", limit=10)
                self.assertEqual(series.count, 3)
                self.assertEqual(series.health.gap_count, 1)
                self.assertEqual(series.health.missing_bars, 1)
                self.assertEqual(series.health.status, "stale")

    def test_recent_database_klines_can_drive_backtest(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            clear_app_modules()
            os.environ["QUANT_PLATFORM_DATABASE_URL"] = (
                f"sqlite:///{Path(tmp_dir) / 'test.db'}"
            )

            from app.core.database import SessionLocal, init_db
            from app.models.market_kline import MarketKline
            from app.schemas.backtest import BacktestRequest
            from app.services.backtest_service import run_backtest
            from app.services.strategy_service import seed_builtin_strategies
            from app.services.user_service import ensure_system_user

            init_db()
            with SessionLocal() as db:
                ensure_system_user(db)
                seed_builtin_strategies(db)
                start = datetime(2026, 1, 1, tzinfo=UTC)
                for index in range(40):
                    opened = start + timedelta(days=index)
                    price = 100 + index + (5 if index % 8 < 4 else -5)
                    db.add(
                        MarketKline(
                            id=f"BTCUSDT:1d:{int(opened.timestamp() * 1000)}",
                            symbol="BTCUSDT",
                            timeframe="1d",
                            open_time=opened,
                            close_time=opened + timedelta(days=1) - timedelta(milliseconds=1),
                            open=price - 1,
                            high=price + 2,
                            low=price - 2,
                            close=price,
                            volume=1000 + index,
                            source="test",
                            ingested_at=opened,
                        )
                    )
                db.commit()

                result = run_backtest(
                    BacktestRequest(
                        symbol="BTCUSDT",
                        timeframe="1d",
                        strategy_id="ma-cross-default",
                        start_date="2026-01-01",
                        end_date="2026-02-09",
                        initial_cash=10000,
                        params={"short_window": 3, "long_window": 7},
                    ),
                    db,
                    user_id="dev-user",
                )
                self.assertEqual(len(result.market_klines), 40)
                self.assertEqual(result.market_klines[-1].date, "2026-02-09")

    def test_hourly_sharpe_uses_hourly_annualization(self) -> None:
        from quant_engine.analyzer.performance import _periods_per_year
        from quant_engine.models import EquityPoint

        start = datetime(2026, 1, 1, tzinfo=UTC)
        curve = [
            EquityPoint(
                date=start + timedelta(hours=index),
                equity=10000 + index,
                cash=10000,
                position=0,
                close=100,
            )
            for index in range(3)
        ]
        self.assertEqual(_periods_per_year(curve), 365 * 24)


if __name__ == "__main__":
    unittest.main()
