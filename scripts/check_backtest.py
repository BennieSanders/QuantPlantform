import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from quant_engine.backtest import run_ma_cross_backtest


def main() -> None:
    result = run_ma_cross_backtest(
        symbol="BTCUSDT",
        timeframe="1d",
        start_date="2024-01-01",
        end_date="2024-12-31",
        initial_cash=10000,
        short_window=7,
        long_window=30,
    )

    print(f"Symbol: {result.symbol}")
    print(f"Signals: {len(result.signals)}")
    print(f"Trades: {len(result.broker_result.trades)}")
    print(f"Metrics: {result.metrics}")
    print("First trades:")
    for trade in result.broker_result.trades[:6]:
        print(trade)
    print("Last equity point:")
    print(result.broker_result.equity_curve[-1])


if __name__ == "__main__":
    main()
