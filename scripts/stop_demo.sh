#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RUN_DIR="$ROOT_DIR/.run"
QUIET="${1:-}"

stop_process() {
  local name="$1"
  local pid_file="$2"
  if [ ! -f "$pid_file" ]; then
    [ "$QUIET" = "--quiet" ] || echo "$name is not managed by the demo runner."
    return
  fi

  local pid
  pid="$(cat "$pid_file")"
  if kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null || true
    for _ in {1..20}; do
      kill -0 "$pid" 2>/dev/null || break
      sleep 0.25
    done
    if kill -0 "$pid" 2>/dev/null; then
      kill -9 "$pid" 2>/dev/null || true
    fi
  fi
  rm -f "$pid_file"
  [ "$QUIET" = "--quiet" ] || echo "$name stopped."
}

stop_process "Backend" "$RUN_DIR/backend.pid"
stop_process "Frontend" "$RUN_DIR/frontend.pid"
