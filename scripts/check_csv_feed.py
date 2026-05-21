import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from quant_engine.datafeed import build_sample_path, load_klines


def main() -> None:
    data_dir = Path("data/sample")
    path = build_sample_path("BTCUSDT", "1d", data_dir)
    klines = load_klines(path, start_date="2024-01-01", end_date="2024-01-31")

    print(f"Loaded {len(klines)} rows from {path}")
    print(f"First: {klines[0]}")
    print(f"Last: {klines[-1]}")


if __name__ == "__main__":
    main()
