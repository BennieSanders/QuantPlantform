from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from quant_engine.backtest import run_builtin_backtest


def main() -> None:
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

    print(f"Symbol: {result.symbol}")
    print(f"Signals: {len(result.signals)}")
    print(f"Trades: {len(result.broker_result.trades)}")
    print(f"Metrics: {result.metrics}")
    print("First trades:")
    for trade in result.broker_result.trades[:6]:
        print(trade)


if __name__ == "__main__":
    main()
