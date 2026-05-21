# Sample K-Line Data

This directory stores local CSV data for the first demo backtest.

Current files:

- `BTCUSDT_1d.csv`: Binance spot BTCUSDT daily klines for 2024
- `ETHUSDT_1d.csv`: Binance spot ETHUSDT daily klines for 2024

CSV format:

```csv
date,open,high,low,close,volume
2024-01-01,42283.58000000,44184.10000000,42180.77000000,44179.55000000,27174.29903000
```

Source:

- Binance public data: `https://data.binance.vision/data/spot/monthly/klines`

Regenerate data:

```bash
python3 scripts/download_binance_klines.py --symbol BTCUSDT --interval 1d --start 2024-01 --end 2024-12
python3 scripts/download_binance_klines.py --symbol ETHUSDT --interval 1d --start 2024-01 --end 2024-12
```
