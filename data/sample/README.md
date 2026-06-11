# Sample K-Line Data

This directory stores local CSV data for the first demo backtest.

Current files:

- `BTCUSDT_1d.csv`: Binance spot BTCUSDT daily klines for 2024
- `ETHUSDT_1d.csv`: Binance spot ETHUSDT daily klines for 2024
- `BTCUSDT_1h.csv`: optional hourly history when you regenerate with `--interval 1h`
- `ETHUSDT_1h.csv`: optional hourly history when you regenerate with `--interval 1h`

CSV format:

```csv
date,open,high,low,close,volume
2024-01-01,42283.58000000,44184.10000000,42180.77000000,44179.55000000,27174.29903000
```

Source:

- Binance public data: `https://data.binance.vision/data/spot/monthly/klines`

Regenerate data:

```bash
python3 scripts/download_binance_klines.py --symbols BTCUSDT ETHUSDT --intervals 1d 1h --years-back 3
```

The script writes one normalized CSV per symbol and interval, for example `BTCUSDT_1d.csv` and `BTCUSDT_1h.csv`.
