import os
import sys
import unittest
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


if __name__ == "__main__":
    unittest.main()
