# Quant Platform Architecture

## 1. Architecture Overview

本项目采用“前后端分离 + 后端内置量化核心”的结构。第一版定位为虚拟货币现货回测平台，课程项目阶段不把量化核心拆成独立服务，避免过早引入服务治理、消息队列和部署复杂度。

```text
User
-> Frontend (Vue3 + Vite + ECharts)
-> Backend (FastAPI)
-> Quant Engine (Python package)
-> Database (MySQL)
```

核心原则：

- Frontend 负责交互、表单、图表和结果展示。
- Backend 负责 API、鉴权、数据库读写和业务流程编排。
- Quant Engine 只负责 K 线数据读取、策略执行、回测撮合和指标分析。
- Database 保存用户、策略、K 线数据和回测记录。

第一版市场范围：

- Asset class: crypto
- Market type: spot
- Symbols: BTCUSDT, ETHUSDT
- Timeframes: 1d first, then 1h
- Position mode: long_only
- Data source: CSV sample data

## 2. Project Structure

```text
quant-platform/
├── frontend/
│   └── src/
├── backend/
│   └── app/
│       ├── api/
│       ├── core/
│       ├── models/
│       ├── schemas/
│       ├── services/
│       └── main.py
├── quant_engine/
│   ├── analyzer/
│   ├── broker/
│   ├── datafeed/
│   └── strategies/
├── data/
│   └── sample/
├── docs/
└── scripts/
```

## 3. Frontend

技术栈：

- Vue3
- Vite
- ECharts
- Axios or Fetch API

页面规划：

- Login Page: 用户登录
- Dashboard Page: 总览、最近回测记录
- Strategy Page: 策略列表、策略参数配置、策略代码编辑
- Backtest Page: 交易标的、K 线周期、时间区间、初始资金、策略选择
- Backtest Result Page: 收益曲线、交易记录、指标展示
- Backtest History Page: 回测记录列表、历史权益曲线和交易明细

前端不直接处理策略回测逻辑，只提交参数、策略代码和回测请求，并展示后端返回结果。策略代码编辑器可以使用 Monaco Editor 或 CodeMirror。

## 4. Backend

技术栈：

- FastAPI
- Pydantic
- SQLAlchemy
- MySQL driver, such as PyMySQL or mysqlclient

模块职责：

- `api/`: HTTP 路由层，负责请求入口和响应格式。
- `core/`: 配置、数据库连接、鉴权工具等基础能力。
- `models/`: SQLAlchemy 数据库模型。
- `schemas/`: Pydantic 请求和响应结构。
- `services/`: 业务逻辑层，连接 API、数据库和 quant_engine。
- `main.py`: FastAPI 应用入口。

API 初版规划：

- `POST /api/auth/login`
- `GET /api/strategies`
- `POST /api/strategies`
- `PUT /api/strategies/{id}`
- `POST /api/backtests`
- `GET /api/backtests`
- `GET /api/backtests/{id}`
- `GET /api/users/me`

第一版 `POST /api/backtests` 请求示例：

```json
{
  "asset_class": "crypto",
  "market_type": "spot",
  "symbol": "BTCUSDT",
  "timeframe": "1d",
  "position_mode": "long_only",
  "strategy": "ma_cross",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "initial_cash": 10000,
  "params": {
    "short_window": 7,
    "long_window": 30
  }
}
```

## 5. Quant Engine

`quant_engine` 是普通 Python 包，由后端服务直接 import 调用。

模块职责：

- `strategies/`: 策略定义，例如均线交叉、动量策略。
- `datafeed/`: K 线数据读取与清洗，初期可以读取 `data/sample` 下的 CSV。
- `broker/`: 虚拟货币现货撮合、现金、持仓、手续费和交易记录。
- `analyzer/`: 收益率、最大回撤、胜率、夏普比率等指标计算。

初期建议只实现一个基础策略和一个 CSV 数据源，优先跑通 BTCUSDT 日线回测闭环。

## 6. Database

初版表设计：

### users

- `id`
- `username`
- `password_hash`
- `created_at`

### strategies

- `id`
- `user_id`
- `name`
- `description`
- `strategy_type`
- `code`
- `default_params`
- `status`
- `created_at`

### backtest_records

- `id`
- `user_id`
- `strategy_id`
- `asset_class`
- `market_type`
- `symbol`
- `timeframe`
- `position_mode`
- `start_date`
- `end_date`
- `initial_cash`
- `params`
- `metrics`
- `equity_curve`
- `trades`
- `created_at`

### kline_data

- `id`
- `asset_class`
- `symbol`
- `timeframe`
- `trade_date`
- `open`
- `high`
- `low`
- `close`
- `volume`

课程项目初期可以先用 CSV 演示 K 线数据，数据库表设计保留为后续扩展。后续如果扩展美股，可以继续复用 `asset_class` 和 `symbol` 字段，例如 `asset_class=us_stock`、`symbol=AAPL`。

合约双向回测不进入第一版。后续扩展时可以复用同一套请求结构，把 `market_type` 从 `spot` 扩展为 `futures`，把 `position_mode` 从 `long_only` 扩展为 `long_short`，再增加杠杆、保证金、资金费率和强平相关字段。

## 7. Strategy Code Editor

网页端策略代码编辑是后续核心功能，但不进入最小演示版的第一步。原因是直接执行用户提交的 Python 代码有安全风险，需要做限制和隔离。

推荐路线：

- Phase 1: 内置策略，例如 `ma_cross`，用于跑通回测主链路。
- Phase 2: 网页编辑策略代码，但只允许使用受限模板，例如实现 `generate_signals(klines, params)`。
- Phase 3: 保存用户策略代码到数据库，支持编辑、复制、版本备注和回测。
- Phase 4: 引入执行隔离，例如子进程、超时控制、禁用危险 import、限制文件和网络访问。

第一版策略代码模板可以设计为：

```python
def generate_signals(klines, params):
    short_window = params["short_window"]
    long_window = params["long_window"]
    # return [{"date": "...", "action": "buy", "price": 123.45}]
```

策略代码编辑器要遵守两个边界：

- 用户代码只生成 `buy` / `sell` 信号。
- 资金、持仓、手续费、收益计算仍由平台统一处理。

这样既能体现“用户可编辑策略”，又能保证不同策略的回测结果可比较。

## 8. Backtest Flow

```text
1. User selects crypto symbol, timeframe, date range, strategy, initial cash, and parameters.
2. Frontend sends POST /api/backtests.
3. Backend validates request with Pydantic schema.
4. Backend service calls quant_engine.
5. quant_engine loads crypto K-line data and runs the selected strategy.
6. analyzer calculates metrics and equity curve.
7. Backend saves backtest record into MySQL.
8. Backend returns result to frontend.
9. Frontend renders charts and summary metrics.
```

## 9. Milestones

### Milestone 1: Minimum Demo

- FastAPI starts successfully.
- Vue page can submit a backtest request.
- quant_engine runs one BTCUSDT moving average crossover strategy on CSV data.
- ECharts displays equity curve.

### Milestone 2: Persistence

- SQLite stores strategies and backtest records for the course demo.
- Backtest history is queryable through API and visible on Dashboard/History views.
- Later replace SQLite with MySQL and add users/authentication.

### Milestone 3: Strategy Expansion

- Add multiple built-in strategies.
- Support strategy parameter forms.
- Add web strategy code editor with restricted strategy template.
- Add basic performance metrics.
- Add ETHUSDT and 1h timeframe support.

### Milestone 4: AI Extension

- Add strategy recommendation entry.
- Generate explanation or parameter suggestions from historical backtest results.

### Milestone 5: Market Expansion

- Add crypto futures long/short backtest as an advanced feature.
- Add optional US stock symbols.
- Keep crypto as the primary market in UI and documentation.
