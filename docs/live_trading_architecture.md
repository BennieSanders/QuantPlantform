# Live Trading Architecture

The finished platform should let a user connect an exchange account, backtest a
strategy, run it in paper trading, and finally enable live trading from the same
strategy interface. The architecture must treat live trading as a controlled
extension of the quant engine, not as a separate shortcut from the web UI to an
exchange API.

## Target Flow

```text
User account
-> encrypted exchange credentials
-> strategy configuration
-> backtest
-> paper trading
-> risk approval
-> live trading engine
-> exchange broker adapter
-> exchange order/trade updates
-> local audit records
```

## Trading Modes

- `backtest`: historical K-lines, simulated broker, deterministic results.
- `paper`: realtime market data, simulated broker, no real exchange orders.
- `live`: realtime market data, exchange broker, real orders and balances.

The same `Strategy` interface should work in all three modes. The selected
broker changes by mode.

## Broker Boundary

Strategies must never call Binance, OKX, or any other exchange API directly.
They can only call the broker interface:

- `buy(quantity)`
- `sell(quantity)`
- `buy_all()`
- `sell_all()`
- `submit_order(order)`

The broker owns:

- balance checks
- exchange filters, lot sizes, min notional, and price precision
- fee handling
- order submission
- order status reconciliation
- trade fill records
- position and equity snapshots

## Live Trading Requirements

Before enabling live trading, the platform needs:

- encrypted API key storage
- read-only credential test before trading permission is accepted
- per-account exchange adapter configuration
- strategy-level risk limits
- account-level daily loss and max position limits
- order idempotency keys
- order status sync loop
- emergency stop per strategy and per account
- audit log for every generated signal, risk decision, order, fill, and error

## Exchange Adapter Plan

The codebase now has an `ExchangeBroker` base shape for future adapters. Concrete
adapters should be added later as isolated modules:

```text
quant_engine/broker/
  binance.py
  okx.py
```

Each adapter must translate the internal `Order` model into exchange-specific
requests and translate exchange responses back into local order, trade, cash,
position, and equity records.

## Safety Rule

Backtest success must not automatically enable live trading. The platform should
require an explicit user action to move from backtest to paper, and another
explicit action to move from paper to live.
