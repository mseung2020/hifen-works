"""
FastAPI 서버 — WebSocket으로 ML 엔진 결과를 실시간 전송
  실행: uvicorn backend.server:app --reload --port 8000
"""

import asyncio
import json
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ml.engine_sponsored import SponsoredEngine

app = FastAPI(title="Instagram Ad Filter AI")

# 프론트엔드 정적 파일 서빙
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

# 엔진 인스턴스
engine = SponsoredEngine()

# WebSocket 연결 관리
connected_clients: list[WebSocket] = []


async def broadcast(message: str):
    """모든 연결된 클라이언트에 메시지 전송"""
    disconnected = []
    for ws in connected_clients:
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        connected_clients.remove(ws)


@app.get("/")
async def index():
    return FileResponse(str(FRONTEND_DIR / "index.html"))


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connected_clients.append(ws)

    # 이전 저장 결과가 있으면 먼저 재전송 (재접속 복원)
    previous = None
    save_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "analysis_result.json")
    if os.path.exists(save_path):
        with open(save_path) as f:
            previous = json.load(f)

    if previous and engine.status != "running":
        await ws.send_text(json.dumps({
            "type": "status",
            "status": "restored",
            "progress": 100,
            "detail": f"이전 분석 결과 복원 ({previous.get('saved_at', '')[:19]})",
        }))
        for log_msg in previous.get("log_history", []):
            await ws.send_text(json.dumps(log_msg, ensure_ascii=False, default=str))
    else:
        await ws.send_text(json.dumps({
            "type": "status",
            "status": engine.status,
            "progress": engine.progress,
            "detail": "연결됨. '분석 시작' 버튼을 눌러주세요.",
        }))

    try:
        while True:
            data = await ws.receive_text()
            msg = json.loads(data)

            if msg.get("action") == "start":
                # 새로 분석 시작 (이전 결과 초기화)
                engine.set_broadcast(broadcast)
                engine.results = []
                engine._log_history = []
                asyncio.create_task(engine.run_full_analysis())

    except WebSocketDisconnect:
        connected_clients.remove(ws)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
