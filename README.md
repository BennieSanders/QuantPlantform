# Quant Platform

一个基于 Vue3 + FastAPI + Python 的工程化量化回测平台。当前重点是虚拟货币现货回测、智能回测分析、实时行情采集与观察、策略管理、数据归属、迁移和测试底座。期货双向和美股不在当前范围内。

## 项目目标
实现一个可长期演进的量化交易平台，支持：
- 用户体系与权限边界
- 虚拟货币交易标的选择，例如 BTCUSDT、ETHUSDT
- K 线周期选择，例如 1d、1h
- 策略选择
- 网页端策略代码编辑
- 回测执行
- 回测结果展示
- 智能回测分析、风险判断和参数建议
- 实时 K 线拉取、持久化和行情观察
- 后续强化策略沙箱、独立任务队列和生产部署

## 技术架构
- Frontend: Vue3 + Vite + ECharts
- Backend: FastAPI
- Quant Engine: Python package
- Database: SQLite for local development, MySQL/PostgreSQL for production target

## 项目结构
- `frontend/`: 前端页面与图表展示
- `backend/`: FastAPI 后端服务
- `quant_engine/`: 策略、数据、回测和分析核心
- `docs/`: 项目文档
- `scripts/`: 启动脚本、初始化脚本
- `data/`: 示例行情数据

## 工程化开发闭环

当前阶段先保留可运行链路，同时把平台底座工程化：

```text
Frontend crypto backtest form
-> Backend Backtest API
-> Quant Engine
-> Backend response
-> Frontend ECharts result
```

当前工程化阶段安排：

- Config: 用 `QUANT_PLATFORM_*` 环境变量管理数据库、CORS、数据目录和默认系统用户。
- Database: 本地开发仍可用 SQLite，正式 schema 通过 Alembic 维护。
- Ownership: 策略和回测记录已带 `user_id`，当前使用开发默认用户，后续接入真实登录。
- Tests: 保留量化引擎稳定性测试，新增路由层用户隔离测试。
- Docs: 维护工程化路线和开发日志，避免只靠代码提交记录传递上下文。

当前市场范围：

- Market: Crypto spot
- Symbols: BTCUSDT, ETHUSDT
- Timeframes: 1d first, then 1h
- Direction: long only
- Future extension: crypto futures long/short
- Data source: Binance REST + SQLite K-line storage, with CSV fallback
- Built-in strategies: moving average crossover and RSI reversal

## 当前进度

- FastAPI 后端已具备 `/health`、`/api/backtests` 和 `/api/strategies` 接口。
- 已新增统一配置层 `app.core.config`，支持环境变量驱动数据库、CORS 和样例数据目录。
- 已新增 Alembic 迁移骨架，后续数据库 schema 演进不再依赖 `create_all()`。
- 已新增 `users` 模型、注册/登录接口和签名访问 token；策略和回测记录已绑定 `user_id`。
- 演示启动默认关闭匿名回退，必须注册或登录后才能访问功能页面。
- 已准备 Binance 公开数据源的 BTCUSDT、ETHUSDT 2024 年日线 CSV。
- 已提供批量下载脚本，可回填 BTC/ETH 的 1d 和 1h 历史 K 线到 `data/sample/`。
- `quant_engine.datafeed` 已支持读取本地 K 线 CSV。
- `quant_engine.strategies` 已支持均线交叉和 RSI 反转两个内置策略。
- `quant_engine` 已支持现货只做多回测，包含交易记录、权益曲线、总收益率、年化收益率、最大回撤、夏普比率、胜率等指标。
- `POST /api/backtests` 已接入真实回测结果，并保存回测记录。
- `POST /api/backtests/jobs` 已支持创建异步回测任务，任务状态可通过 `/api/backtests/jobs/{id}` 查询。
- 异步任务已支持取消、失败/取消后重试，以及服务启动时恢复中断任务状态。
- `GET /api/backtests` 和 `GET /api/backtests/{id}` 已支持查询最近回测和详情。
- `/api/strategies` 已支持策略 CRUD，并通过 SQLite 持久化到 `backend/quant_platform.db`；自定义策略保存前会校验 `generate_signals(klines, params)`。
- 前端已具备侧栏式平台布局，包含 Dashboard、回测中心、回测历史、任务中心、策略管理和账户视图；Dashboard 和回测详情都能渲染 K 线图、成交量和交易标记，回测中心可根据策略默认参数动态生成参数表单。
- 前端回测中心已改为异步任务模式：提交后创建 job，轮询状态，成功后自动加载结果记录。
- 任务中心支持查看最近任务、取消 queued/running 任务、重试 failed/cancelled 任务，并可打开成功任务的回测结果。
- 前端已新增账户视图，支持注册、登录、保存 access token、退出，并在后续 API 请求中自动携带 Authorization。
- 策略管理已支持从内置策略复制为自定义策略模板，再编辑和保存。
- `tests/` 已覆盖 MA/RSI 内置策略稳定结果、自定义策略校验、回测记录持久化服务和路由层用户隔离。
- 已新增 `market_klines` 持久化模型和 `/api/market/sync`、`/api/market/klines` 接口，可从 Binance 拉取 BTC/ETH 的 1m、5m、15m、1h、1d K 线并增量更新。
- 前端已新增实时行情观察页，支持手动同步和每 10 秒自动拉取、入库、刷新行情图；按周期自动使用合理窗口（1m/1天、5m/3天、15m/7天、1h/30天、1d/1年），并显示 MA7、MA25。
- 回测服务会首先使用数据库中的近期行情，覆盖不足时再回退到样例 CSV；回测页面会同步并显示当前标的和周期的可用日期范围。
- 已新增回测分析记录和 `/api/ai/backtests/{id}/analyze` 接口，输出风险等级、综合评分、置信度、适配场景、风险提示、行动建议和建议参数，并保存分析历史。
- AI 分析页支持 `Google Gemini` / `OpenAI` / `本地引擎` 切换；当前默认调用 Gemini API，如果没有配置密钥或调用失败，会回退到可离线复现的 `local-quant-recommender-v2`。

## 环境变量

```bash
export QUANT_PLATFORM_ENV=development
export QUANT_PLATFORM_DATABASE_URL=sqlite:///backend/quant_platform.db
export QUANT_PLATFORM_SAMPLE_DATA_DIR=data/sample
export QUANT_PLATFORM_CORS_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
export QUANT_PLATFORM_SYSTEM_USER_ID=dev-user
export QUANT_PLATFORM_SYSTEM_USERNAME=developer
export QUANT_PLATFORM_AUTH_SECRET=change-me
export QUANT_PLATFORM_ACCESS_TOKEN_TTL_SECONDS=86400
export QUANT_PLATFORM_ALLOW_DEV_AUTH_FALLBACK=true
export QUANT_PLATFORM_MARKET_DATA_BASE_URL=https://api.binance.com
export QUANT_PLATFORM_MARKET_DATA_FALLBACK_URLS=https://data-api.binance.vision
export QUANT_PLATFORM_MARKET_DATA_TIMEOUT_SECONDS=20
# 如果现场网络访问 Binance 超时，可在 backend/.env.local 配本机代理，例如：
# export HTTP_PROXY=http://127.0.0.1:7898
# export HTTPS_PROXY=http://127.0.0.1:7898
# export ALL_PROXY=socks5://127.0.0.1:7898
export QUANT_PLATFORM_OPENAI_API_KEY=sk-...
export QUANT_PLATFORM_OPENAI_MODEL=gpt-5.5
export QUANT_PLATFORM_OPENAI_BASE_URL=https://api.openai.com/v1
export QUANT_PLATFORM_OPENAI_TIMEOUT_SECONDS=30
export QUANT_PLATFORM_GEMINI_API_KEY=your-google-ai-studio-key
export QUANT_PLATFORM_GEMINI_MODEL=gemini-2.5-flash
export QUANT_PLATFORM_GEMINI_FALLBACK_MODELS=gemini-3.1-flash-lite,gemini-3.5-flash
export QUANT_PLATFORM_GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta
export QUANT_PLATFORM_GEMINI_TIMEOUT_SECONDS=30
```

实时行情接口：

```bash
curl -X POST http://127.0.0.1:8000/api/market/sync \
  -H "Content-Type: application/json" \
  -d '{"symbol":"BTCUSDT","timeframe":"1m","limit":200}'

curl "http://127.0.0.1:8000/api/market/klines?symbol=BTCUSDT&timeframe=1m&limit=200"
```

AI 分析接口：

```bash
curl -X POST http://127.0.0.1:8000/api/ai/backtests/<backtest_id>/analyze \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"mode":"gemini"}'
curl http://127.0.0.1:8000/api/ai/backtests/<backtest_id>/analyses
```

认证接口：

```bash
curl -X POST http://127.0.0.1:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"correct-password"}'

curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"correct-password"}'

curl http://127.0.0.1:8000/api/users/me \
  -H "Authorization: Bearer <access_token>"
```

前端账户视图会把登录成功后的 token 保存到浏览器 `localStorage`。生产部署时建议进一步评估 token 存储策略、HTTPS、过期处理和刷新机制。

异步回测任务：

```bash
curl -X POST http://127.0.0.1:8000/api/backtests/jobs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "symbol":"BTCUSDT",
    "timeframe":"1d",
    "strategy_id":"ma-cross-default",
    "start_date":"2024-01-01",
    "end_date":"2024-12-31",
    "initial_cash":10000,
    "params":{"short_window":7,"long_window":30}
  }'

curl http://127.0.0.1:8000/api/backtests/jobs/<job_id> \
  -H "Authorization: Bearer <access_token>"

curl -X POST http://127.0.0.1:8000/api/backtests/jobs/<job_id>/cancel \
  -H "Authorization: Bearer <access_token>"

curl -X POST http://127.0.0.1:8000/api/backtests/jobs/<job_id>/retry \
  -H "Authorization: Bearer <access_token>"
```

当前异步执行器是进程内线程池，适合本地开发和单实例部署验证。生产化阶段应替换为外部队列和独立 worker。

## 数据库迁移

本地首次创建工程化 schema：

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
```

如果本地已有旧版 `backend/quant_platform.db`，开发启动时会对 SQLite 自动补齐当前必需的 `user_id` 列。生产环境不要依赖这个兼容逻辑，必须用正式迁移流程处理。

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

检查 RSI 反转回测：

```bash
python3 scripts/check_rsi_backtest.py
```

批量回填市场数据：

```bash
python3 scripts/download_binance_klines.py --symbols BTCUSDT ETHUSDT --intervals 1d 1h --years-back 3
```

运行自动化测试：

```bash
PYTHONPATH="$(pwd):$(pwd)/backend" backend/.venv/bin/python -m unittest discover -s tests -v
```

结项演示启动方式：

```bash
./scripts/demo.sh
```

该命令会先停止旧的演示进程，再启动后端 `8000` 和前端 `5173`，保持终端运行，按 `Ctrl+C` 自动停止。另开终端可执行自检：

```bash
./scripts/check_demo.sh
```

录屏前可使用后台一键重启方式：

```bash
./scripts/restart_demo.sh
```

该命令无论之前是否启动过，都会先释放 `8000/5173` 端口并重新启动，再执行自检。默认前端地址是：

```text
http://127.0.0.1:5173
```

如果确实需要使用 `5174`，可以显式指定：

```bash
FRONTEND_PORT=5174 ./scripts/restart_demo.sh
```

后台停止方式：

```bash
./scripts/stop_demo.sh
```

开发时仍可分别运行 `./scripts/dev_backend.sh` 和 `./scripts/dev_frontend.sh`。

默认访问前端：

```text
http://127.0.0.1:5173
```

完整演示顺序、断网预案和检查清单见 `docs/demo_runbook.md`。
