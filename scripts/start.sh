#!/bin/sh
# Start the backend (port 8000) and the frontend (port 5173), then open the app in the browser.
# Usage: sh scripts/start.sh      Stop with Ctrl-C.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PATH="$HOME/.local/bin:$HOME/.local/node/bin:$PATH"
cd "$ROOT/backend" && uv run uvicorn app.main:app --port 8000 &
BACK=$!
trap 'kill $BACK 2>/dev/null' EXIT INT TERM
sleep 2
( sleep 3; open "http://localhost:5173" 2>/dev/null || true ) &
cd "$ROOT/frontend" && npm run dev -- --port 5173
