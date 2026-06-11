#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../backend"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
export PYTHONPATH="$(pwd)/..:${PYTHONPATH:-}"
export NO_PROXY="127.0.0.1,localhost,::1,${NO_PROXY:-}"
export no_proxy="127.0.0.1,localhost,::1,${no_proxy:-}"
if ! python -c "import fastapi, sqlalchemy, uvicorn" >/dev/null 2>&1; then
  pip install -r requirements.txt
fi
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
