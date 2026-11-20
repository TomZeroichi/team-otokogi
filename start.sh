#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
python3 -m pip install -r requirements.txt
export DATA_DIR="$(pwd)/data"
export COOKIE_SECURE=0
exec python3 -m uvicorn app:app --host 0.0.0.0 --port 8000
