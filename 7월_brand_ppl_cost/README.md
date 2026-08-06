# 브랜드별 PPL 예상 지출 산정

팔로워·구독자 구간별 단가와 조정비율 기준표(`비용 산정.md`)를 바탕으로, 브랜드별 유튜브·인스타 PPL 예상 비용을 산정하는 작업입니다. DB 조회 → 비용 계산 → 브랜드별 요약 → 엑셀 리포트 생성까지 한 번에 처리하는 파이프라인을 구축했고, 이를 감싼 웹 서비스도 함께 만들었습니다.

- **분야:** 데이터 분석
- **결과물 형태:** CLI 자동화 파이프라인(`cost_pipeline/`) + 이를 감싼 FastAPI 웹 서비스(`expense_service/`)
- **단가 기준:** 팔로워/구독자 4개 구간(1~10만, 10~30만, 30~50만, 50만~100만 이상)별 유튜브 PPL/쇼츠, 인스타 피드/릴스 단가 + 구간별 조정(절감)비율 — [`비용 산정.md`](비용%20산정.md)

## 파이프라인 (`cost_pipeline/`)

`./run.sh` 한 줄로 DB 조회부터 엑셀 리포트까지 끝냅니다.

```
DB 조회(brand_cost / brand_user_cost)
  → 비용 산정.md 로직으로 예상비용 계산
  → 브랜드별 요약(brand_ppl_summary.csv)
  → 엑셀 리포트(브랜드별_예상지출_*.xlsx)
```

- `config.yaml` 하나만 고치면 기간(`period`)·브랜드 목록(`brands`)·단가표(`pricing.buckets`)가 전부 바뀝니다. 두 SQL 쿼리가 이 브랜드 목록 하나만 참조하므로 브랜드명이 쿼리마다 다르게 적혀서 데이터가 누락되는 사고가 구조적으로 안 생깁니다.
- `sql/*.sql.tmpl` — brand_list를 config에서 채워 넣는 SQL 템플릿
- `src/config.py`(설정 로딩) → `db.py`(DB 접속·조회) → `cost_calc.py`(비용 산정.md 보간+조정비율) → `aggregate.py`(브랜드별 집계) → `xlsx_export.py`(엑셀 생성) → `pipeline.py`(순서 실행)
- DB 접속 정보는 `.env`(레포에 미포함, 실제 운영 DB 크레덴셜)로 관리하고 `.env.example`을 참고해서 새 환경에서 채워 넣습니다.
- `output/2026-07/` — 2026년 7월 기준 실제 실행 결과 예시 (`brand_cost.csv`, `brand_user.csv`, `brand_user_cost.csv`, `brand_ppl_summary.csv`, `브랜드별_예상지출_2026-07.xlsx`)

자세한 사용법은 [`cost_pipeline/README.md`](cost_pipeline/README.md) 참고.

## 웹 서비스 (`expense_service/`)

`cost_pipeline`을 그대로 재사용하는 FastAPI 웹 서비스입니다. `cost_pipeline_bridge.py`가 `cost_pipeline/src`의 DB 접속·비용계산·집계·엑셀생성 로직을 그대로 import해서 쓰고, `config.yaml` 파일 자체는 건드리지 않은 채 기간·브랜드·단가 구간을 요청(request)마다 다르게 갈아끼웁니다.

- `GET /api/defaults` — config.yaml 기본값(기간·브랜드·단가 구간) 반환
- `GET /api/brand-catalog` — 선택 가능한 브랜드 목록/토픽 반환
- `POST /api/generate` — 기간·브랜드·단가 구간을 받아 파이프라인 전체를 실행하고 요약·다운로드 링크 반환
- `GET /api/runs/{run_id}/download/{filename}` — 실행 결과 파일 다운로드 (경로 조작 방지 검증 포함)
- `static/` — 기간·브랜드·단가를 입력하고 결과를 확인하는 웹 UI (`index.html`/`app.js`/`style.css`)

즉 마케터가 CLI 없이도 웹에서 기간·브랜드·단가만 골라 바로 예상지출 엑셀을 받을 수 있는 구조입니다.

## 제외한 것

- `cost_pipeline`이 만들어지기 전, 같은 목적을 수동 반복 작업으로 처리했던 스크래치 파일들(`query_a.csv`, `brand cost.csv`, `brand_cost_july.csv/.sql`, `브랜드별 예상지출*.xlsx` 등 루트의 CSV/SQL/엑셀) — 파이프라인 구축 이전 시행착오라 최종본이 아님
- `cost_pipeline/.env`, `expense_service/.venv`, `__pycache__` — 실제 운영 DB 크레덴셜·가상환경
- `expense_service/runs/` — 테스트 실행 흔적(584KB), 실제 산출물이 아님
