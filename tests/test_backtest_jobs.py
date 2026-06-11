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


class BacktestJobServiceTest(unittest.TestCase):
    def test_backtest_job_runs_and_links_result_record(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            clear_app_modules()
            os.environ["QUANT_PLATFORM_DATABASE_URL"] = (
                f"sqlite:///{Path(tmp_dir) / 'test.db'}"
            )

            from app.core.database import SessionLocal, init_db
            from app.schemas.backtest import BacktestRequest
            from app.services.backtest_job_service import (
                cancel_backtest_job,
                create_backtest_job,
                get_backtest_job,
                list_backtest_jobs,
                recover_interrupted_jobs,
                retry_backtest_job,
                run_backtest_job,
            )
            from app.services.backtest_service import get_backtest_record
            from app.services.strategy_service import seed_builtin_strategies
            from app.services.user_service import ensure_system_user

            init_db()
            with SessionLocal() as db:
                ensure_system_user(db)
                seed_builtin_strategies(db)
                job = create_backtest_job(
                    BacktestRequest(
                        asset_class="crypto",
                        market_type="spot",
                        symbol="BTCUSDT",
                        timeframe="1d",
                        position_mode="long_only",
                        strategy_id="ma-cross-default",
                        start_date="2024-01-01",
                        end_date="2024-12-31",
                        initial_cash=10000,
                        params={"short_window": 7, "long_window": 30},
                    ),
                    db,
                    user_id="dev-user",
                    submit=False,
                )

                self.assertEqual(job.status, "queued")

            run_backtest_job(job.id)

            with SessionLocal() as db:
                finished = get_backtest_job(job.id, db, user_id="dev-user")
                self.assertIsNotNone(finished)
                assert finished is not None
                self.assertEqual(finished.status, "succeeded")
                self.assertTrue(finished.result_backtest_id)
                self.assertEqual(finished.error_message, "")
                self.assertIsNotNone(finished.started_at)
                self.assertIsNotNone(finished.finished_at)

                result = get_backtest_record(finished.result_backtest_id, db, user_id="dev-user")
                self.assertIsNotNone(result)
                assert result is not None
                self.assertEqual(result.metrics.total_return, 0.587727)

                jobs = list_backtest_jobs(db, user_id="dev-user")
                self.assertEqual([item.id for item in jobs], [job.id])
                self.assertIsNone(get_backtest_job(job.id, db, user_id="other-user"))

    def test_backtest_job_cancel_retry_and_recover(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            clear_app_modules()
            os.environ["QUANT_PLATFORM_DATABASE_URL"] = (
                f"sqlite:///{Path(tmp_dir) / 'test.db'}"
            )

            from app.core.database import SessionLocal, init_db
            from app.schemas.backtest import BacktestRequest
            from app.services.backtest_job_service import (
                cancel_backtest_job,
                create_backtest_job,
                get_backtest_job,
                recover_interrupted_jobs,
                retry_backtest_job,
            )
            from app.services.strategy_service import seed_builtin_strategies
            from app.services.user_service import ensure_system_user

            request = BacktestRequest(
                asset_class="crypto",
                market_type="spot",
                symbol="BTCUSDT",
                timeframe="1d",
                position_mode="long_only",
                strategy_id="ma-cross-default",
                start_date="2024-01-01",
                end_date="2024-12-31",
                initial_cash=10000,
                params={"short_window": 7, "long_window": 30},
            )

            init_db()
            with SessionLocal() as db:
                ensure_system_user(db)
                seed_builtin_strategies(db)
                queued = create_backtest_job(request, db, user_id="dev-user", submit=False)
                cancelled = cancel_backtest_job(queued.id, db, user_id="dev-user")

                self.assertIsNotNone(cancelled)
                assert cancelled is not None
                self.assertEqual(cancelled.status, "cancelled")
                self.assertTrue(cancelled.cancel_requested)
                self.assertIsNotNone(cancelled.finished_at)

                retry = retry_backtest_job(cancelled.id, db, user_id="dev-user", submit=False)
                self.assertIsNotNone(retry)
                assert retry is not None
                self.assertEqual(retry.status, "queued")
                self.assertEqual(retry.retry_of_job_id, cancelled.id)
                self.assertEqual(retry.attempt, 2)

                with self.assertRaisesRegex(ValueError, "Only failed or cancelled"):
                    retry_backtest_job(retry.id, db, user_id="dev-user", submit=False)

                recovered_count = recover_interrupted_jobs(db)
                self.assertEqual(recovered_count, 1)

                recovered = get_backtest_job(retry.id, db, user_id="dev-user")
                self.assertIsNotNone(recovered)
                assert recovered is not None
                self.assertEqual(recovered.status, "failed")
                self.assertIn("interrupted", recovered.error_message)


if __name__ == "__main__":
    unittest.main()
