#!/bin/bash
# One-time setup: installs dependencies into an isolated virtual environment and fetches lightweight face models.
set -e
cd "$(dirname "$0")"

PY="${PYTHON:-python3}"
command -v "$PY" >/dev/null 2>&1 || {
  echo "Error: Python 3 was not found. Please install Python 3.10+."
  exit 1
}

if [ ! -d ".venv" ]; then
  echo "Creating isolated virtual environment..."
  "$PY" -m venv .venv
fi

echo "Installing required dependencies..."
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt

echo "Ensuring face recognition models are ready..."
.venv/bin/python models/download_models.py

echo "Setup completed successfully."
echo "To start: ./start.sh (or double-click 'Open Photo Sorter.command')"
