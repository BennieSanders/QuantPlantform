#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR/backend"
source .venv/bin/activate

if [ -f ".env.local" ]; then
  set -a
  source .env.local
  set +a
fi
if [ -f ".env" ]; then
  set -a
  source .env
  set +a
fi

export PYTHONPATH="$ROOT_DIR:${PYTHONPATH:-}"
export NO_PROXY="127.0.0.1,localhost,::1,${NO_PROXY:-}"
export no_proxy="127.0.0.1,localhost,::1,${no_proxy:-}"
export QUANT_PLATFORM_ALLOW_DEV_AUTH_FALLBACK="${QUANT_PLATFORM_ALLOW_DEV_AUTH_FALLBACK:-false}"

exec uvicorn app.main:app --host 127.0.0.1 --port 8000
