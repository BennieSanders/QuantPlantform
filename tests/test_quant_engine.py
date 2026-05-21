from pathlib import Path
import unittest

from quant_engine.backtest import run_builtin_backtest, run_ma_cross_backtest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class QuantEngineTest(unittest.TestCase):
    def test_ma_cross_backtest_metrics_are_stable(self) -> None:
        result = run_ma_cross_backtest(
            symbol="BTCUSDT",
            timeframe="1d",
            start_date="2024-01-01",
            end_date="2024-12-31",
            initial_cash=10000,
            short_window=7,
            long_window=30,
            data_dir=PROJECT_ROOT / "data" / "sample",
        )

        self.assertEqual(result.symbol, "BTCUSDT")
        self.assertEqual(result.timeframe, "1d")
        self.assertEqual(len(result.signals), 14)
        self.assertEqual(len(result.broker_result.trades), 14)
        self.assertEqual(len(result.broker_result.equity_curve), 366)
        self.assertEqual(result.metrics.total_return, 0.587727)
        self.assertEqual(result.metrics.annualized_return, 0.587727)
        self.assertEqual(result.metrics.max_drawdown, -0.367244)
        self.assertEqual(result.metrics.sharpe_ratio, 1.322291)
        self.assertEqual(result.metrics.win_rate, 0.428571)
        self.assertEqual(result.metrics.final_equity, 15877.274734)

    def test_rsi_reversal_backtest_metrics_are_stable(self) -> None:
        result = run_builtin_backtest(
            strategy_name="rsi_reversal",
            symbol="BTCUSDT",
            timeframe="1d",
            start_date="2024-01-01",
            end_date="2024-12-31",
            initial_cash=10000,
            params={"period": 14, "oversold": 30, "overbought": 70},
            data_dir=PROJECT_ROOT / "data" / "sample",
        )

        self.assertEqual(result.strategy, "rsi_reversal")
        self.assertEqual(len(result.signals), 9)
        self.assertEqual(len(result.broker_result.trades), 9)
        self.assertEqual(len(result.broker_result.equity_curve), 366)
        self.assertEqual(result.metrics.total_return, 0.208876)
        self.assertEqual(result.metrics.max_drawdown, -0.159717)
        self.assertEqual(result.metrics.sharpe_ratio, 0.831862)
        self.assertEqual(result.metrics.win_rate, 0.75)
        self.assertEqual(result.metrics.final_equity, 12088.757443)

    def test_ma_cross_backtest_reports_available_range_when_empty(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "Available data: 2024-01-01 to 2024-12-31",
        ):
            run_ma_cross_backtest(
                symbol="BTCUSDT",
                timeframe="1d",
                start_date="2025-01-01",
                end_date="2026-12-31",
                initial_cash=10000,
                short_window=7,
                long_window=30,
                data_dir=PROJECT_ROOT / "data" / "sample",
            )


if __name__ == "__main__":
    unittest.main()
