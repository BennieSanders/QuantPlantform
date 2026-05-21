import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from quant_engine.datafeed import build_sample_path, load_klines
from quant_engine.strategies import generate_ma_cross_signals


def main() -> None:
    data_dir = Path("data/sample")
    path = build_sample_path("BTCUSDT", "1d", data_dir)
    klines = load_klines(path, start_date="2024-01-01", end_date="2024-12-31")
    signals = generate_ma_cross_signals(klines, short_window=7, long_window=30)

    print(f"Loaded {len(klines)} klines from {path}")
    print(f"Generated {len(signals)} signals")
    for signal in signals[:10]:
        print(signal)


if __name__ == "__main__":
    main()
