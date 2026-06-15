#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RUN_DIR="$ROOT_DIR/.run"
LOG_DIR="$RUN_DIR/logs"
BACKEND_PID_FILE="$RUN_DIR/backend.pid"
FRONTEND_PID_FILE="$RUN_DIR/frontend.pid"

mkdir -p "$LOG_DIR"

port_pid() {
  lsof -tiTCP:"$1" -sTCP:LISTEN 2>/dev/null | head -n 1 || true
}

require_free_port() {
  local port="$1"
  local pid
  pid="$(port_pid "$port")"
  if [ -n "$pid" ]; then
    echo "Port $port is already in use by PID $pid. Run ./scripts/stop_demo.sh first." >&2
    exit 1
  fi
}

wait_for_url() {
  local name="$1"
  local url="$2"
  local attempts=30
  for ((index = 1; index <= attempts; index++)); do
    if curl --noproxy '*' --max-time 2 --silent --fail "$url" >/dev/null; then
      echo "$name is ready: $url"
      return 0
    fi
    sleep 1
  done
  echo "$name did not become ready. Check $LOG_DIR/$name.log" >&2
  return 1
}

require_free_port 8000
require_free_port 5173

if [ ! -d "$ROOT_DIR/backend/.venv" ]; then
  python3 -m venv "$ROOT_DIR/backend/.venv"
fi
if ! "$ROOT_DIR/backend/.venv/bin/python" -c "import fastapi, sqlalchemy, uvicorn, socksio" >/dev/null 2>&1; then
  "$ROOT_DIR/backend/.venv/bin/pip" install -r "$ROOT_DIR/backend/requirements.txt"
fi
if [ ! -d "$ROOT_DIR/frontend/node_modules" ]; then
  npm --prefix "$ROOT_DIR/frontend" install
fi

nohup "$ROOT_DIR/scripts/run_demo_backend.sh" >"$LOG_DIR/backend.log" 2>&1 </dev/null &
echo "$!" >"$BACKEND_PID_FILE"

nohup "$ROOT_DIR/scripts/run_demo_frontend.sh" >"$LOG_DIR/frontend.log" 2>&1 </dev/null &
echo "$!" >"$FRONTEND_PID_FILE"

trap '"$ROOT_DIR/scripts/stop_demo.sh" --quiet' ERR
wait_for_url "backend" "http://127.0.0.1:8000/health"
wait_for_url "frontend" "http://127.0.0.1:5173"
trap - ERR

echo "Demo environment is running."
echo "Frontend: http://127.0.0.1:5173"
echo "Backend:  http://127.0.0.1:8000"
echo "Logs:     $LOG_DIR"
