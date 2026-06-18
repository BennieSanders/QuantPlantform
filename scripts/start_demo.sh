#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RUN_DIR="$ROOT_DIR/.run"
LOG_DIR="$RUN_DIR/logs"
BACKEND_PID_FILE="$RUN_DIR/backend.pid"
FRONTEND_PID_FILE="$RUN_DIR/frontend.pid"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
RESTART=false

for arg in "$@"; do
  case "$arg" in
    --restart)
      RESTART=true
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      exit 2
      ;;
  esac
done

mkdir -p "$LOG_DIR"

port_pid() {
  lsof -tiTCP:"$1" -sTCP:LISTEN 2>/dev/null | head -n 1 || true
}

require_free_port() {
  local port="$1"
  local pid
  pid="$(port_pid "$port")"
  if [ -n "$pid" ]; then
    echo "Port $port is already in use by PID $pid. Run ./scripts/stop_demo.sh first, or use ./scripts/start_demo.sh --restart." >&2
    exit 1
  fi
}

free_port_for_restart() {
  local port="$1"
  local pids
  pids="$(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)"
  if [ -z "$pids" ]; then
    return
  fi
  echo "Stopping existing process on port $port: $pids"
  kill $pids 2>/dev/null || true
  for _ in {1..20}; do
    if [ -z "$(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)" ]; then
      return
    fi
    sleep 0.25
  done
  pids="$(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)"
  if [ -n "$pids" ]; then
    kill -9 $pids 2>/dev/null || true
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

if [ "$RESTART" = true ]; then
  "$ROOT_DIR/scripts/stop_demo.sh" --quiet || true
  free_port_for_restart "$BACKEND_PORT"
  free_port_for_restart "$FRONTEND_PORT"
fi

require_free_port "$BACKEND_PORT"
require_free_port "$FRONTEND_PORT"

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
wait_for_url "backend" "http://127.0.0.1:$BACKEND_PORT/health"
wait_for_url "frontend" "http://127.0.0.1:$FRONTEND_PORT"
trap - ERR

echo "Demo environment is running."
echo "Frontend: http://127.0.0.1:$FRONTEND_PORT"
echo "Backend:  http://127.0.0.1:$BACKEND_PORT"
echo "Logs:     $LOG_DIR"
