# Development Log

## 2026-06-15 Google Gemini AI Recommendation

- Added Google AI Studio Gemini API support using `generateContent` with JSON output.
- Added a three-way provider switch: Gemini, OpenAI, and the local recommendation engine.
- Made Gemini the default provider while preserving explicit fallback messages and local resilience.

## 2026-06-15 OpenAI-backed AI Recommendation

- Added OpenAI Responses API support for backtest recommendation analysis.
- Kept the local recommender as a fallback when no API key is configured or
  the OpenAI request fails.
- Added an explicit AI analysis mode switch so the UI can choose OpenAI or the
  local engine per request.
- Added environment-driven OpenAI model, base URL, and timeout settings.
- Expanded AI analysis output into a structured recommendation panel with
  score, confidence, execution plan, and fit/avoid profiles.

Verification:

```text
Ran 15 tests
OK

vite build
built successfully
```

## 2026-06-15 AI Recommendation Upgrade

- Expanded the backtest AI output from a basic review into a recommendation
  layer with score, confidence, analysis type, readiness stage, fit profile,
  avoid profile, and execution plan.
- Upgraded the AI analysis UI so the recommendation result is shown as a
  structured decision panel instead of a plain summary block.
- Added SQLite schema compatibility and Alembic migration `0003_ai_recommendation_fields`
  for the new persisted AI analysis fields.
- Added test coverage for the recommendation fields and kept the full suite
  green.

Verification:

```text
Ran 15 tests
OK

vite build
built successfully
```

## 2026-06-11 Realtime Chart and Recent Backtest Data

- Replaced the single-day range for every chart interval with timeframe-aware
  windows from one day of 1-minute candles through one year of daily candles.
- Added MA7/MA25 overlays and a recent-candle default zoom to the market chart.
- Added recent backtest data synchronization and a market-data range API.
- Backtests now prefer persisted market data when it fully covers the requested
  range, with deterministic CSV fallback for offline historical examples.
- Added test coverage proving 2026 database candles can drive a backtest.

Verification: 13 backend tests pass and the frontend production build succeeds.

## 2026-06-11 AI and Realtime Market Data

Implemented:

- Added persisted `market_klines` storage with idempotent Binance REST upserts.
- Added authenticated market sync and query APIs for BTCUSDT and ETHUSDT.
- Added a realtime market observation view with manual and timed ingestion.
- Added persisted, user-scoped AI backtest analyses with risk explanations,
  warnings, action recommendations, and MA/RSI parameter suggestions.
- Added an AI analysis view and analysis history.
- Added Alembic migration `0002_market_data_and_ai`.
- Changed backend development startup so an existing environment does not
  require a dependency download on every launch.
- Added isolated market-data and AI-analysis service tests.

Verification:

```text
Ran 11 tests
OK

vite build
built successfully
```

Remaining engineering work:

- Move timed market ingestion into a durable scheduler or worker.
- Add gap, duplicate, and stale-data monitoring.
- Add external model provider evaluation cases and regression checks.
- Rank parameter suggestions with out-of-sample candidate backtests.

## 2026-05-28

Engineering direction changed from a course demo toward a maintainable platform.

Implemented:

- Added `app.core.config` for environment-driven backend settings.
- Updated database engine creation so SQLite-specific connection options are not
  applied to other database engines.
- Added `users` model and a development default user service.
- Added `user_id` ownership to strategies and backtest records.
- Scoped strategy listing/detail/update/delete and backtest listing/detail by
  current user, while keeping built-in strategies globally visible.
- Added `app.core.security.get_current_user_id` as a temporary dependency seam
  for future authentication.
- Added Alembic scaffold and an initial engineering schema migration.
- Added a SQLite-only development compatibility upgrade so existing local
  `quant_platform.db` files can receive `user_id` columns without blocking app
  startup. Production schema changes should still go through Alembic.
- Added `httpx` and `alembic` to backend requirements for API testing and
  migration workflows.
- Added route-layer test coverage for user-scoped strategy visibility.
- Updated README and added this engineering roadmap.

Verification:

```bash
PYTHONPATH="$(pwd):$(pwd)/backend" backend/.venv/bin/python -m unittest discover -s tests -v
```

Result:

```text
Ran 5 tests
OK
```

Known follow-ups:

- Existing local `backend/quant_platform.db` may use the old schema. Rebuild it
  in development or apply an explicit migration path before preserving data.
- Real authentication is not implemented yet; the API still uses the configured
  development default user.
- Backtests still execute synchronously inside the API request.
- Custom strategy execution still needs process isolation before production use.

## 2026-05-28 E2 Auth Iteration

Implemented:

- Added auth settings: `QUANT_PLATFORM_AUTH_SECRET`,
  `QUANT_PLATFORM_ACCESS_TOKEN_TTL_SECONDS`, and
  `QUANT_PLATFORM_ALLOW_DEV_AUTH_FALLBACK`.
- Added PBKDF2 password hashing and verification with constant-time digest
  comparison.
- Added HMAC-signed access tokens with expiry.
- Added `/api/auth/register`, `/api/auth/login`, and `/api/users/me`.
- Reworked current-user resolution so bearer tokens map to active users.
- Kept development fallback to the configured default user for local iteration.
- Added auth service tests for registration, login, duplicate username handling,
  invalid password handling, token user resolution, and disabled fallback.

Verification:

```bash
PYTHONPATH="$(pwd):$(pwd)/backend" backend/.venv/bin/python -m unittest discover -s tests -v
```

Result:

```text
Ran 7 tests
OK
```

Known follow-ups:

- The token format is intentionally small and local. If third-party clients or
  SSO are needed, replace it with a standard JWT library or an identity provider.
- Production deployments must set a strong `QUANT_PLATFORM_AUTH_SECRET` and
  disable development auth fallback.

## 2026-05-28 Frontend Auth Iteration

Implemented:

- Added frontend auth API helpers for register, login, current user, token
  storage, and logout.
- Added automatic `Authorization: Bearer <token>` headers for protected API
  calls.
- Added an Account view in `App.vue` for current user details, registration,
  login, and logout.
- Improved frontend API error parsing so FastAPI `detail` messages display
  cleanly in the UI.
- Kept development fallback compatible: if no token is stored and the backend
  allows fallback, `/api/users/me` resolves to the configured development user.

Verification:

```bash
npm run build
```

Result:

```text
✓ built
```

## 2026-05-28 Async Backtest Jobs

Implemented:

- Added `BacktestJob` model and `backtest_jobs` schema to the Alembic baseline.
- Added `BacktestJobResponse`.
- Added in-process threaded backtest job runner.
- Added `POST /api/backtests/jobs` to enqueue a job.
- Added `GET /api/backtests/jobs` and `GET /api/backtests/jobs/{job_id}` for
  job listing and polling.
- Kept synchronous `POST /api/backtests` for compatibility.
- Added job service test coverage for queued -> succeeded flow, result record
  linking, and user isolation.

Current tradeoff:

- The first async implementation uses a process-local `ThreadPoolExecutor`.
  This gives the API a non-blocking job contract without requiring Redis,
  Celery, or separate worker deployment yet. It is not sufficient for
  multi-process production deployments because queued futures are not durable
  across process restarts.

Verification:

```bash
PYTHONPATH="$(pwd):$(pwd)/backend" backend/.venv/bin/python -m unittest discover -s tests -v
```

Result:

```text
Ran 8 tests
OK
```

## 2026-05-28 Frontend Async Backtest Flow

Implemented:

- Added frontend API helpers for creating and polling backtest jobs.
- Changed the Backtest view submission flow from direct synchronous backtest
  execution to `POST /api/backtests/jobs`.
- Added polling for `/api/backtests/jobs/{job_id}`.
- Automatically loads the final backtest record through `result_backtest_id`
  when the job succeeds.
- Displays current job status in the backtest control panel.
- Kept the synchronous API helper available for compatibility.

Verification:

```bash
npm run build
```

Result:

```text
✓ built
```

## 2026-05-28 Backtest Job Reliability

Implemented:

- Added `retry_of_job_id`, `attempt`, and `cancel_requested` fields to backtest
  jobs.
- Added `POST /api/backtests/jobs/{job_id}/cancel`.
- Added `POST /api/backtests/jobs/{job_id}/retry`.
- Added startup recovery for jobs left in `queued` or `running` state before the
  current process started.
- Added tests for cancelling queued jobs, retrying cancelled jobs, rejecting
  retry for non-terminal jobs, and recovering interrupted jobs.

Current semantics:

- Queued jobs can be cancelled before execution.
- Running jobs record a cancellation request, but the in-process thread cannot
  forcibly interrupt arbitrary Python execution. A running job moves to
  `cancelled` only when it reaches a safe post-execution checkpoint.
- Retrying creates a new job and preserves the original job record.
- Startup recovery marks interrupted `queued` or `running` jobs as `failed`.

Verification:

```bash
PYTHONPATH="$(pwd):$(pwd)/backend" backend/.venv/bin/python -m unittest discover -s tests -v
```

Result:

```text
Ran 9 tests
OK
```

## 2026-05-28 Frontend Job Management

Implemented:

- Added frontend API helpers for job cancellation and retry.
- Added `JobHistoryView.vue`.
- Added a `任务中心` navigation entry.
- Added recent job loading after authentication and after backtest submission.
- Added job actions for refresh, cancel, retry, and opening completed backtest
  results.
- Fixed the custom strategy template indentation in `App.vue`.

Verification:

```bash
npm run build
```

Result:

```text
✓ built
```

## 2026-05-28 Frontend View Split

Implemented:

- Extracted `DashboardView.vue`.
- Extracted `HistoryView.vue`.
- Extracted `BacktestView.vue`.
- Extracted `StrategyManagerView.vue`.
- Kept `App.vue` responsible for app-level state, API orchestration, chart
  instance lifecycle, and navigation state.
- Added explicit chart-ready events from view components so chart DOM ownership
  stays inside the view and ECharts instance ownership stays in `App.vue`.

Impact:

- `frontend/src/App.vue` was reduced further from 785 lines to 591 lines.
- The frontend now has clear component boundaries for account, dashboard,
  backtest, history, strategy management, trade table, chart options, and
  formatting.

Verification:

```bash
npm run build
```

Result:

```text
✓ built
```

Known follow-ups:

- `localStorage` token storage is adequate for local engineering iteration, but
  production deployment should revisit token storage, HTTPS-only operation,
  expiry handling, and refresh/session strategy.
- Continue splitting backtest, history, and strategy views into dedicated
  components before adding more UI features.

## 2026-05-28 Frontend Component Split

Implemented:

- Extracted account UI into `frontend/src/components/AccountView.vue`.
- Extracted trade records into `frontend/src/components/TradeTable.vue`.
- Extracted display formatting helpers into `frontend/src/utils/formatters.js`.
- Extracted ECharts option builders into `frontend/src/utils/chartOptions.js`.
- Replaced full ECharts import with on-demand chart/component registration.
- Added Vite manual chunking for ECharts and adjusted the warning threshold to
  match the remaining chart vendor chunk.

Impact:

- `frontend/src/App.vue` was reduced from 1117 lines to 785 lines.
- Main frontend app chunk dropped to about 91 kB minified; ECharts is isolated in
  its own vendor chunk.

Verification:

```bash
npm run build
```

Result:

```text
✓ built
```
