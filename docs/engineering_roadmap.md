# Engineering Roadmap

This project is moving from a course-style demo into an engineering-oriented
quant platform. The guiding rule is to strengthen platform boundaries before
adding more trading features.

## Current Baseline

- Frontend: Vue3, Vite, ECharts.
- Backend: FastAPI, SQLAlchemy, Pydantic.
- Quant engine: local Python package for CSV-backed spot backtests.
- Database: SQLite in local development, Alembic baseline added for managed
  schema evolution.
- Ownership: strategies and backtest records now carry `user_id`. The current
  API uses a development default user until real authentication is added.

## E1: Platform Foundation

Status: course-demo complete; production hardening remains.

- Centralize backend settings under `app.core.config`.
- Replace hardcoded database and data paths with `QUANT_PLATFORM_*`
  environment variables.
- Add Alembic baseline migration.
- Add `users` table and `user_id` ownership columns.
- Keep local development configurable while the demo runner requires authentication.
- Expand tests from engine-only checks to include route-layer behavior.

Exit criteria:

- A fresh database can be created from migrations.
- Strategy and backtest APIs consistently scope non-built-in records by user.
- Tests run in isolated temporary databases.

## E2: Authentication and Authorization

Status: course-demo complete.

- Add password hashing and login endpoint.
- Add JWT or server-side session authentication.
- Replace the development user dependency with authenticated user resolution.
- Bind strategies, backtests, API keys, and future jobs to authenticated users.
- Add API tests for ownership isolation and unauthorized access.

Current implementation:

- Added user registration and login endpoints.
- Added PBKDF2 password hashing.
- Added HMAC-signed access tokens using standard library crypto primitives.
- Added `/api/users/me`.
- Added frontend account view, token persistence, and Authorization headers.
- The recommended demo runner sets `QUANT_PLATFORM_ALLOW_DEV_AUTH_FALLBACK=false`.

## E3: Async Backtest Jobs

Status: in progress.

- Add job states: `queued`, `running`, `succeeded`, `failed`, `cancelled`. Done.
- Add polling endpoint for job status and result. Done.
- Persist runtime errors. Done.
- Keep synchronous `POST /api/backtests` for backward compatibility while adding
  `/api/backtests/jobs`.
- Current worker is an in-process thread pool. Later replace it with an external
  queue and standalone worker process.
- Frontend backtest submission now uses the job API and polls job status. Done.
- Frontend task center can list jobs, cancel, retry, and open completed results.
  Done.

Remaining work:

- Add cancellation semantics. Done for queued jobs; running jobs use best-effort
  cancellation request semantics.
- Add retry policy. Done for failed/cancelled jobs.
- Add startup recovery for interrupted queued/running jobs. Done.
- Add worker heartbeat and stale-job recovery.
- Move execution to a separate worker process or service.
- Wire frontend backtest submission to the job API.

## E4: Strategy Execution Sandbox

- Run custom Python strategies outside the API process.
- Add execution timeout and memory limits.
- Block filesystem and network access for custom code.
- Capture stdout, stderr, and structured strategy errors.
- Define a stable signal contract and validate generated signals.

## E5: Market Data Layer

- Keep CSV as the deterministic backtest data source. Done.
- Add database-backed K-line storage. Done for `market_klines`.
- Add Binance REST ingestion with idempotent upsert. Done.
- Add authenticated market read and sync APIs. Done.
- Add a frontend observation view with manual and timed ingestion. Done.
- Introduce a broader `DataSource` abstraction shared by backtest and realtime flows.
- Move timed ingestion from the browser session into a durable scheduler/worker.
- Add data quality checks for gaps, duplicates, ranges, and schema drift.

## E5.1: AI Backtest Analysis

- Persist analysis results per user and backtest. Done.
- Generate explainable risk levels, strengths, warnings, and next actions. Done.
- Generate strategy-specific parameter suggestions. Done for MA and RSI.
- Add frontend analysis generation and history views. Done.
- Keep a provider field and stable response contract. Done.
- Google Gemini and OpenAI provider integrations are implemented; provider evaluation and regression fixtures remain.
- Add parameter candidate backtests and rank suggestions using out-of-sample results.

## E6: Production Readiness

- Add structured logging and request IDs.
- Add API pagination and stable error envelopes.
- Add Docker or deployment manifests.
- Add CI for backend tests and frontend build.
- Add frontend component tests or end-to-end smoke tests.

## Frontend Modularization

Status: in progress.

- Account and trade table UI are extracted into components.
- Dashboard, backtest, history, and strategy manager views are extracted into
  components.
- Formatting helpers and chart option builders are extracted into utility
  modules.
- ECharts is imported through on-demand core modules and isolated into a vendor
  chunk.
- Remaining work: add frontend unit/component tests and consider moving chart
  instance lifecycle into reusable chart components.
