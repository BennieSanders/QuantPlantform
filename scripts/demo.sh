#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

cleanup() {
  "$ROOT_DIR/scripts/stop_demo.sh" --quiet || true
}

trap cleanup EXIT INT TERM
"$ROOT_DIR/scripts/start_demo.sh"

echo "Press Ctrl+C to stop the demo environment."
while true; do
  backend_pid="$(cat "$ROOT_DIR/.run/backend.pid" 2>/dev/null || true)"
  frontend_pid="$(cat "$ROOT_DIR/.run/frontend.pid" 2>/dev/null || true)"
  if [ -z "$backend_pid" ] || [ -z "$frontend_pid" ]; then
    echo "A managed service PID file is missing." >&2
    exit 1
  fi
  if ! kill -0 "$backend_pid" 2>/dev/null || ! kill -0 "$frontend_pid" 2>/dev/null; then
    echo "A demo service stopped unexpectedly. Check .run/logs/." >&2
    exit 1
  fi
  sleep 2
done
