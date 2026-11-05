#!/usr/bin/env zsh

PORT="${1:-8000}"
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

cd "$ROOT_DIR"

echo "Checking port $PORT..."
PIDS=$(lsof -ti tcp:$PORT 2>/dev/null || true)

if [ -n "$PIDS" ]; then
  echo "Killing process(es) on port $PORT: $PIDS"
  echo "$PIDS" | xargs -r kill -9
  sleep 1
else
  echo "No process is currently using port $PORT."
fi

if [ -f ".venv/bin/activate" ]; then
  echo "Starting service with virtual environment..."
  source .venv/bin/activate
  exec python main.py
else
  echo "Virtual environment not found. Starting with system Python..."
  exec python main.py
fi
