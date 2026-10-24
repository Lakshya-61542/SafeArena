#!/usr/bin/env sh
# macOS / Linux equivalent of run_windows.bat
cd "$(dirname "$0")" || exit 1
[ -d .venv ] || python3 -m venv .venv
.venv/bin/python -m pip install --quiet -r requirements.txt
[ -f .env ] || cp .env.example .env
exec .venv/bin/python run_local.py
