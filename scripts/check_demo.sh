#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DATABASE="$ROOT_DIR/backend/quant_platform.db"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
BACKEND_URL="${BACKEND_URL:-http://127.0.0.1:$BACKEND_PORT}"
FRONTEND_URL="${FRONTEND_URL:-http://127.0.0.1:$FRONTEND_PORT}"

check_url() {
  local label="$1"
  local url="$2"
  if curl --noproxy '*' --max-time 3 --silent --fail "$url" >/dev/null; then
    printf '[OK]   %s\n' "$label"
  else
    printf '[FAIL] %s (%s)\n' "$label" "$url" >&2
    return 1
  fi
}

check_url "Backend health" "$BACKEND_URL/health"
check_url "Frontend page" "$FRONTEND_URL"

if [ -f "$DATABASE" ]; then
  printf '[OK]   Database exists\n'
  printf '       Backtests: %s\n' "$(sqlite3 "$DATABASE" 'select count(*) from backtest_records;')"
  printf '       AI analyses: %s\n' "$(sqlite3 "$DATABASE" 'select count(*) from ai_analyses;')"
  printf '       K-lines: %s\n' "$(sqlite3 "$DATABASE" 'select count(*) from market_klines;')"
  printf '       Latest K-line: %s\n' "$(sqlite3 "$DATABASE" 'select coalesce(max(open_time), "none") from market_klines;')"
else
  printf '[FAIL] Database is missing: %s\n' "$DATABASE" >&2
  exit 1
fi

if [ -f "$ROOT_DIR/backend/.env.local" ] && rg -q '^(GEMINI_API_KEY|QUANT_PLATFORM_GEMINI_API_KEY)=.+' "$ROOT_DIR/backend/.env.local"; then
  printf '[OK]   Gemini API key is configured locally\n'
else
  printf '[WARN] Gemini API key is not configured; AI will use the local fallback\n'
fi

printf 'Demo readiness checks passed.\n'
