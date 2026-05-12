#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cleanup() {
  jobs -p | xargs -r kill
}

trap cleanup EXIT INT TERM

cd "$ROOT_DIR/apps/backend"
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &

cd "$ROOT_DIR"
npm --prefix apps/frontend run dev &

wait
