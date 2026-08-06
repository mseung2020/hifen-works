#!/usr/bin/env bash
# 로컬 웹 서비스 실행: http://127.0.0.1:8008
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install --quiet -r requirements.txt

echo "브라우저에서 http://127.0.0.1:8008 열기"
uvicorn app.main:app --host 127.0.0.1 --port 8008
