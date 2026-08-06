#!/usr/bin/env bash
# 한 줄 실행용 래퍼: venv 준비 + 의존성 설치 + 파이프라인 실행
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install --quiet -r requirements.txt

python run.py "$@"
