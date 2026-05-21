# Quant Platform

一个基于 Vue3 + FastAPI + Python 的虚拟货币量化回测平台课程项目。

## 项目目标
实现一个基础量化交易平台，支持：
- 用户登录
- 虚拟货币交易标的选择，例如 BTCUSDT、ETHUSDT
- K 线周期选择，例如 1d、1h
- 策略选择
- 网页端策略代码编辑
- 回测执行
- 回测结果展示
- 后续扩展美股标的
- 后续扩展 AI 策略推荐

## 技术架构
- Frontend: Vue3 + Vite + ECharts
- Backend: FastAPI
- Quant Engine: Python package
- Database: MySQL

## 项目结构
- `frontend/`: 前端页面与图表展示
- `backend/`: FastAPI 后端服务
- `quant_engine/`: 策略、数据、回测和分析核心
- `docs/`: 项目文档
- `scripts/`: 启动脚本、初始化脚本
- `data/`: 示例行情数据

## 推荐开发闭环

第一阶段先完成最小可运行链路：

```text
Frontend crypto backtest form
-> Backend Backtest API
-> Quant Engine
-> Backend response
-> Frontend ECharts result
```

第一版范围先固定为：

- Market: Crypto spot
- Symbols: BTCUSDT, ETHUSDT
- Timeframes: 1d first, then 1h
- Direction: long only
- Future extension: crypto futures long/short
- Data source: CSV sample data
- First strategy: moving average crossover

这样可以尽早形成课程展示效果，再逐步补充登录、数据库持久化、策略代码编辑器、合约双向回测、美股扩展和 AI 推荐。

## 当前进度

- FastAPI 后端已具备 `/health`、`/api/backtests` 和 `/api/strategies` 接口。
- 已准备 Binance 公开数据源的 BTCUSDT、ETHUSDT 2024 年日线 CSV。
- `quant_engine.datafeed` 已支持读取本地 K 线 CSV。
- `quant_engine.strategies` 已支持均线交叉信号生成。
- `quant_engine` 已支持现货只做多回测，包含交易记录、权益曲线、总收益率、年化收益率、最大回撤、夏普比率、胜率等指标。
- `POST /api/backtests` 已接入真实回测结果，并保存回测记录。
- `GET /api/backtests` 和 `GET /api/backtests/{id}` 已支持查询最近回测和详情。
- `/api/strategies` 已支持策略 CRUD，并通过 SQLite 持久化到 `backend/quant_platform.db`。
- 前端已具备侧栏式平台布局，包含 Dashboard、回测中心、回测历史、策略管理四个视图；Dashboard 可展示最近回测记录。
- `tests/` 已覆盖量化内核稳定结果和回测记录持久化服务。

检查 CSV 读取：

```bash
python3 scripts/check_csv_feed.py
```

检查均线交叉策略信号：

```bash
python3 scripts/check_ma_cross.py
```

检查完整回测：

```bash
python3 scripts/check_backtest.py
```

运行自动化测试：

```bash
PYTHONPATH="$(pwd):$(pwd)/backend" backend/.venv/bin/python -m unittest discover -s tests -v
```

启动后端：

```bash
./scripts/dev_backend.sh
```

启动前端：

```bash
./scripts/dev_frontend.sh
```

访问前端：

```text
http://127.0.0.1:5173
```
