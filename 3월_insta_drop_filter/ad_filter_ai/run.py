"""
실행 스크립트 — 한 번에 서버 시작
  python run.py
  → http://localhost:8000 접속
"""

import uvicorn
import sys, os

# 패키지 경로 설정
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.server import app

if __name__ == "__main__":
    print()
    print("=" * 50)
    print("  Instagram Ad Filter AI Dashboard")
    print("  http://localhost:8000 에서 확인하세요")
    print("=" * 50)
    print()
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
