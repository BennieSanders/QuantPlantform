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


class BacktestServiceTest(unittest.TestCase):
    def test_backtest_service_persists_and_returns_records(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            clear_app_modules()
            os.environ["QUANT_PLATFORM_DATABASE_URL"] = (
                f"sqlite:///{Path(tmp_dir) / 'test.db'}"
            )

            from app.core.database import SessionLocal, init_db
            from app.models.strategy import Strategy
            from app.schemas.backtest import BacktestRequest
            from app.schemas.strategy import StrategyCreate
            from app.services.backtest_service import (
                get_backtest_record,
                list_backtest_records,
                run_backtest,
            )
            from app.services.strategy_service import create_strategy, seed_builtin_strategies

            init_db()
            with SessionLocal() as db:
                seed_builtin_strategies(db)
                strategies = [strategy.id for strategy in db.query(Strategy).all()]
                self.assertIn("ma-cross-default", strategies)
                self.assertIn("rsi-reversal-default", strategies)

                response = run_backtest(
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
                )

                self.assertEqual(response.metrics.total_return, 0.587727)
                self.assertEqual(response.metrics.sharpe_ratio, 1.322291)

                records = list_backtest_records(db, limit=5)
                self.assertEqual(len(records), 1)
                self.assertEqual(records[0].id, response.backtest_id)
                self.assertEqual(records[0].strategy_name, "均线交叉策略")

                detail = get_backtest_record(response.backtest_id, db)
                self.assertIsNotNone(detail)
                assert detail is not None
                self.assertEqual(len(detail.equity_curve), 366)
                self.assertEqual(len(detail.trades), 14)

                rsi_response = run_backtest(
                    BacktestRequest(
                        asset_class="crypto",
                        market_type="spot",
                        symbol="BTCUSDT",
                        timeframe="1d",
                        position_mode="long_only",
                        strategy="rsi_reversal",
                        strategy_id="rsi-reversal-default",
                        start_date="2024-01-01",
                        end_date="2024-12-31",
                        initial_cash=10000,
                        params={"period": 14, "oversold": 30, "overbought": 70},
                    ),
                    db,
                )

                self.assertEqual(rsi_response.strategy, "rsi_reversal")
                self.assertEqual(rsi_response.metrics.total_return, 0.208876)
                self.assertEqual(len(rsi_response.trades), 9)

                with self.assertRaisesRegex(ValueError, "Invalid custom strategy code"):
                    create_strategy(
                        db,
                        StrategyCreate(
                            name="无效策略",
                            strategy_type="custom_code",
                            code="def nope():\n    return []",
                            default_params={},
                            status="draft",
                        ),
                    )

                custom_strategy = create_strategy(
                    db,
                    StrategyCreate(
                        name="自定义买入持有",
                        strategy_type="custom_code",
                        code=(
                            "def generate_signals(klines, params):\n"
                            "    if len(klines) == 2:\n"
                            "        return [{\"date\": klines[-1].date, \"action\": \"buy\"}]\n"
                            "    return []\n"
                        ),
                        default_params={},
                        status="active",
                    ),
                )
                custom_response = run_backtest(
                    BacktestRequest(
                        asset_class="crypto",
                        market_type="spot",
                        symbol="BTCUSDT",
                        timeframe="1d",
                        position_mode="long_only",
                        strategy="custom_code",
                        strategy_id=custom_strategy.id,
                        start_date="2024-01-01",
                        end_date="2024-01-31",
                        initial_cash=10000,
                        params={},
                    ),
                    db,
                )

                self.assertEqual(custom_response.strategy, custom_strategy.id)
                self.assertEqual(len(custom_response.trades), 1)


if __name__ == "__main__":
    unittest.main()
