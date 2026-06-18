# Quant Platform Architecture

## 1. Architecture Overview

本项目采用“前后端分离 + 后端内置量化核心”的结构。当前课程结项版本已经形成用户认证、实时行情、策略回测、任务管理和大模型分析闭环；策略沙箱和独立任务队列保留为后续工程化方向。

```text
User
-> Frontend (Vue3 + Vite + ECharts)
-> Backend (FastAPI)
-> Quant Engine (Python package)
-> Database (SQLite local, MySQL/PostgreSQL production target)
-> External Providers (Binance REST, Google Gemini, optional OpenAI)
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
- Data source: Binance REST + SQLite storage, with CSV fallback

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
- Alembic
- MySQL/PostgreSQL driver for production deployment

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

当前实现已引入用户注册、登录、签名 token 和 `/api/users/me`。策略、回测记录和 AI 分析带 `user_id`。结项演示启动默认关闭无 token 回退。

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

- `strategies/`: 策略定义，例如均线交叉、RSI 反转、动量策略。
- `datafeed/`: K 线数据读取与清洗，初期可以读取 `data/sample` 下的 CSV。
- `broker/`: 虚拟货币现货撮合、现金、持仓、手续费和交易记录。
- `analyzer/`: 收益率、最大回撤、胜率、夏普比率等指标计算。

当前已实现均线交叉和 RSI 反转两个基础策略。回测优先使用数据库中已同步的近期行情，覆盖不足时回退到 CSV 样例数据，兼顾实时性与离线可复现性。

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

### market_klines

- `id`
- `asset_class`
- `symbol`
- `timeframe`
- `open_time`
- `close_time`
- `open`
- `high`
- `low`
- `close`
- `volume`

当前 Binance K 线已通过增量同步写入 SQLite，并带有断档、缺失数量和新鲜度检查。CSV 保留为历史回测和断网演示的确定性回退数据源。

合约双向回测不进入第一版。后续扩展时可以复用同一套请求结构，把 `market_type` 从 `spot` 扩展为 `futures`，把 `position_mode` 从 `long_only` 扩展为 `long_short`，再增加杠杆、保证金、资金费率和强平相关字段。

## 7. Strategy Code Editor

网页端策略代码编辑已进入课程演示版：用户可以创建、编辑、删除自定义策略，也可以从内置策略复制出自定义策略模板。当前实现会在保存前编译校验 `generate_signals(klines, params)` 是否存在，并在回测失败时返回明确错误信息。

直接执行用户提交的 Python 代码仍有安全风险。当前版本只适合作为本地课程演示，正式开放给用户前必须引入更强隔离。

后续路线：

- Phase 1: 内置策略，例如 `ma_cross`，用于跑通回测主链路。
- Phase 2: 网页编辑策略代码，但只允许使用受限模板，例如实现 `generate_signals(klines, params)`。当前已完成基础版。
- Phase 3: 保存用户策略代码到数据库，支持编辑、复制、版本备注和回测。当前已完成保存、编辑、复制和回测，版本备注待补。
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
7. Backend saves backtest record into the configured database.
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

- SQLite stores strategies and backtest records for local development.
- Backtest history is queryable through API and visible on Dashboard/History views.
- Alembic owns schema evolution.
- Strategy and backtest records carry `user_id` ownership.
- Later replace the development default user with real authentication.

### Milestone 3: Strategy Expansion

- Add multiple built-in strategies. Current demo includes MA crossover and RSI reversal.
- Support strategy parameter forms. Current frontend builds parameter inputs from strategy default params.
- Add web strategy code editor with restricted strategy template.
- Add basic performance metrics.
- Add ETHUSDT and 1h timeframe support.

### Milestone 4: AI Extension

- AI analysis entry and persisted analysis history. Done.
- Structured risk, strengths, warnings, execution plan, and parameter suggestions. Done.
- Google Gemini API integration with explicit OpenAI and local-engine switching. Done.
- Next: evaluate suggested parameters through automated out-of-sample candidate backtests.

### Milestone 5: Market Expansion

- Current product scope remains crypto spot. Futures long/short and US stocks are intentionally deferred.
- Real-time crypto K-line ingestion, storage, and observation are the active market-data priority.
