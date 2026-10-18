#!/bin/sh
set -eu

cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required. Install it, then run ./start.sh again." >&2
  exit 1
fi
if ! command -v npm >/dev/null 2>&1; then
  echo "Node.js and npm are required. Install them, then run ./start.sh again." >&2
  exit 1
fi

if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
fi

if ! ./.venv/bin/python -c \
  'import fastapi, uvicorn, langchain, langchain_mistralai, tavily, bs4, requests, dotenv, rich' \
  >/dev/null 2>&1; then
  echo "Installing Python dependencies..."
  ./.venv/bin/python -m pip install -r requirements.txt
fi

if [ ! -d frontend/node_modules ]; then
  echo "Installing frontend dependencies..."
  npm --prefix frontend ci
fi

if [ ! -f .env ]; then
  echo "Warning: .env is missing. Add MISTRAL_API_KEY and TAVILY_API_KEY to run research." >&2
fi

./.venv/bin/python -m uvicorn webapp:app --reload --host 127.0.0.1 --port 8000 &
api_pid=$!
trap 'kill "$api_pid" 2>/dev/null || true' EXIT INT TERM

npm --prefix frontend run dev -- --host 0.0.0.0
