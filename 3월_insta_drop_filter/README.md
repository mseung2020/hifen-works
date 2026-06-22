# 인스타 광고성 게시물 필터링 (드랍 필터)

인스타그램 크롤링 데이터에서 **광고성 게시물을 걸러내는 최적 필터 조건**을 찾는 데이터 분석 작업입니다. 조회수·좋아요·댓글·팔로워 구간별로 **리콜(광고 보존율)과 드랍율**을 계산해, 광고를 거의 놓치지 않으면서(recall ≥ 0.95) 비광고를 최대한 걸러내는 임계값 조합을 탐색합니다.

- **분야:** 데이터 분석
- **결과물 형태:** FastAPI 웹 대시보드 (실시간 분석 + 결과 시각화)
- **핵심 지표:** Recall(광고 보존율), Drop rate(전체 드랍율)

## 결과물: `ad_filter_ai/` (웹 대시보드)

```
python ad_filter_ai/run.py   →   http://localhost:8000
```
- `backend/server.py` — FastAPI + WebSocket 서버. 캐시된 `analysis_result.json`을 로드해 **원본 데이터 없이도 이전 분석 결과를 바로 표시**. 재분석은 WebSocket으로 트리거
- `frontend/index.html` — 결과 대시보드 UI (TOP 조건, recall/drop rate, 생성 SQL 표시)
- `ml/` — 분석 엔진 3종:
  - `engine.py` — 단일 조건(OR) + 복합 가중 점수 기반 필터 탐색
  - `engine_reel_split.py` — 릴스/일반 게시물 분리 최적화
  - `engine_sponsored.py` — sponsored 플래그 + 지표 결합 (기본 엔진)
- `analysis_result.json` — 사전 계산된 분석 결과 (대시보드가 기동 시 표시하는 캐시)

## 데이터

| 파일 | 상태 |
|---|---|
| `data/ad_insta_id.csv` | 포함 (2MB) — 광고로 라벨된 post_id 목록 (recall 계산 기준) |
| `data/total_insta_id_slim.sample.csv` | 포함 — 전체 크롤링 데이터 앞 99행 샘플 (형식 확인용) |
| `data/DATA_SUMMARY.md` | 포함 — 제외된 원본 데이터의 스키마·규모(16.5M행)·분포 통계 요약 |
| 전체 크롤링 CSV (855MB 등) | **제외** — GitHub 100MB 제한 초과 |

원본 데이터가 너무 커서 함께 올릴 수 없으므로, 스키마·규모·통계·샘플을 [`data/DATA_SUMMARY.md`](data/DATA_SUMMARY.md)에 요약해 두었습니다. 대시보드 열람은 캐시된 `analysis_result.json`만으로 가능하며, 재분석을 실행하려면 전체 크롤링 CSV가 필요합니다.

> 참고: 이 대시보드는 초기 CLI 분석 스크립트(단일 조건 / 릴스 분리 / 커스텀 기준 등)들을 `ml/engine*.py`로 정리·발전시킨 최종본입니다.
