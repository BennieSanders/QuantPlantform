#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../frontend"

export NO_PROXY="127.0.0.1,localhost,::1,${NO_PROXY:-}"
export no_proxy="127.0.0.1,localhost,::1,${no_proxy:-}"

if [ ! -d "node_modules" ]; then
  npm install
fi

npm run dev -- --host 127.0.0.1 --port 5173
