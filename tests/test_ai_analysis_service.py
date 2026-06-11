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


class AiAnalysisServiceTest(unittest.TestCase):
    def test_analysis_is_persisted_and_user_scoped(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            clear_app_modules()
            os.environ["QUANT_PLATFORM_DATABASE_URL"] = (
                f"sqlite:///{Path(tmp_dir) / 'test.db'}"
            )

            from app.core.database import SessionLocal, init_db
            from app.schemas.backtest import BacktestRequest
            from app.services.ai_analysis_service import analyze_backtest, list_backtest_analyses
            from app.services.backtest_service import run_backtest
            from app.services.strategy_service import seed_builtin_strategies
            from app.services.user_service import ensure_system_user

            init_db()
            with SessionLocal() as db:
                ensure_system_user(db)
                seed_builtin_strategies(db)
                backtest = run_backtest(
                    BacktestRequest(
                        symbol="BTCUSDT",
                        timeframe="1d",
                        strategy_id="ma-cross-default",
                        start_date="2024-01-01",
                        end_date="2024-12-31",
                        initial_cash=10000,
                        params={"short_window": 7, "long_window": 30},
                    ),
                    db,
                    user_id="dev-user",
                )

                analysis = analyze_backtest(backtest.backtest_id, db, "dev-user")
                self.assertIsNotNone(analysis)
                assert analysis is not None
                self.assertEqual(analysis.provider, "local-quant-analyst-v1")
                self.assertIn(analysis.risk_level, {"low", "medium", "high"})
                self.assertIn("short_window", analysis.suggested_params)

                history = list_backtest_analyses(backtest.backtest_id, db, "dev-user")
                self.assertEqual(len(history or []), 1)
                self.assertIsNone(analyze_backtest(backtest.backtest_id, db, "other-user"))
                self.assertIsNone(list_backtest_analyses(backtest.backtest_id, db, "other-user"))


if __name__ == "__main__":
    unittest.main()
