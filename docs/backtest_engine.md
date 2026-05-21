# Backtest Engine Design

The quant engine follows a lightweight backtrader-style architecture. The goal is
to keep the first version small enough for this project while making the core
usable for real strategy execution, paper trading, and later exchange adapters.
The long-term product target is a platform where a user can connect a Binance or
OKX account, backtest a strategy, run it in paper mode, and then deliberately
enable live trading through the same strategy interface.

## Core Components

- `BacktestEngine`: central orchestrator. It owns the event loop and advances one
  K-line at a time.
- `DataFeed`: provides normalized `Kline` objects. CSV is the first
  implementation.
- `Strategy`: reads completed bars and submits orders. It does not mutate cash or
  positions directly.
- `Broker`: accepts orders, executes them, applies fees, and records trades,
  cash, positions, and equity.
- `RiskManager`: validates orders before they enter the broker queue.
- `Analyzer`: calculates performance metrics from broker output.

## Event Order

For each K-line:

1. The broker executes orders submitted on previous bars.
2. The current completed bar is appended to strategy history.
3. The strategy evaluates the completed bar and can submit new orders.
4. The broker marks portfolio value to the current close.

Orders submitted at step 3 are not executed on the same bar. The first possible
execution is the next bar. This avoids same-bar lookahead behavior in normal
backtests.

## Order Lifecycle

The engine records order events separately from trades:

- `SUBMITTED`: the strategy created an order and risk checks accepted it.
- `REJECTED`: the order failed risk checks or could not be executed.
- `FILLED`: the broker executed the order and generated a trade.

Trades are execution records. Order events are audit records. This distinction is
important for paper trading and live trading because a strategy can generate an
order that is rejected before it reaches the exchange or rejected/fails during
execution.

## Current Scope

- Crypto spot
- Long-only trading
- Market orders
- Full-cash buy and full-position sell helpers
- Fee model
- Basic order risk checks
- Order event audit trail
- Moving average crossover strategy
- RSI reversal strategy
- Equity curve, trades, total return, annualized return, max drawdown, Sharpe ratio, win rate

## Extension Path

1. Add formal order status and rejection records.
2. Add position sizing and risk checks before broker submission.
3. Add paper trading broker that reuses the same strategy interface.
4. Add exchange broker adapters for real trading.
5. Add strategy sandboxing before enabling user code execution.

## Custom Strategy Function

The current web strategy editor stores Python code that must define:

```python
def generate_signals(klines, params):
    return []
```

`klines` is the completed bar history available at the current point in the
backtest. The function can return signal dictionaries:

```python
[
    {"date": klines[-1].date, "action": "buy"},
    {"date": klines[-1].date, "action": "sell"},
]
```

Only active strategies can be backtested. The current implementation uses a
restricted execution namespace for the course project. Before any live trading
feature is enabled, custom strategy execution must be moved into a stronger
sandboxed process.
