#!/bin/bash
# Starts the local photo sorter server and opens your browser.
cd "$(dirname "$0")"
PORT="${PORT:-8765}"
URL="http://127.0.0.1:$PORT/"

open_page() {
  if command -v open >/dev/null; then open "$1";
  elif command -v xdg-open >/dev/null; then xdg-open "$1";
  else echo "Open $1 in your web browser."; fi
}

if curl -s -o /dev/null "http://127.0.0.1:$PORT/api/state"; then
  echo "Photo sorter is already running at $URL"
  open_page "$URL"
  exit 0
fi

[ -x .venv/bin/python ] || ./setup.sh || exit 1

(sleep 1; open_page "$URL") &
PORT="$PORT" exec .venv/bin/python scripts/server.py
