# 광고 라이브러리 브랜드 분류 필터

메타(Facebook/Instagram) **광고 라이브러리 데이터에서 브랜드를 식별·분류**하는 규칙과 검증 로직 작업입니다. 광고 라이브러리 36,145행의 `branded_page_name`·`page_title`을 브랜드/유저 테이블과 매칭해, 어떤 광고가 어떤 브랜드/크리에이터의 것인지 분류하고 그 정확도를 검증했습니다.

- **분야:** 데이터 분석
- **결과물 형태:** 카드뉴스형 HTML 보고 + 분석/설계 문서 + 분류·검증 파이프라인 코드
- **매칭 기준:** `branded_page_name` → 브랜드 테이블(brand_name_kr → en → related_brands), `page_title` → 유저 테이블(user_id → username), 공백 제거 후 정확 일치

## 결과물

| 파일 | 설명 |
|---|---|
| [`브랜드매칭_보고_카드뉴스.html`](브랜드매칭_보고_카드뉴스.html) | **매칭 결과 보고 (카드뉴스형, 자체 완결형)** |
| `분석결과.md` | 매칭 포착률·검증 결과 상세 (branded_page_name 25.9% 포착 등) |
| `파이프라인_설계.md` | 분류·매칭 파이프라인 설계 문서 |

## 코드 (분류·검증 파이프라인)
- `classify.py` / `classify2.py` / `classify_detail.py` — 브랜드 분류
- `analyze.py` — 매칭 분석
- `validate_library.py` / `validate_extra.py` — 검증
- `truthtable.py` — truth table 기반 검증
- `insert_temp_metaad_brand_match.sql` — 임시 매칭 테이블 적재 SQL

## 데이터 (`data/`)
검증 결과·집계 등 소용량 산출물만 포함(2MB 미만). 대용량 원천 데이터는 제외:

| 제외 파일 | 규모 |
|---|---|
| `only_brand.csv` | 415,199행 (161MB) — 광고 라이브러리 원본 |
| `users.csv` / `users_extra.csv` | 256만 행 (87MB) / (112MB) — 유저 매칭 테이블 |
| `라이브러리_*.csv`, `union_library*.csv`, `brand_full.csv` 등 | 각 13~15MB — 매칭 중간/결과 셋 |

> 원천: 메타 광고 라이브러리(only_brand) + 브랜드/유저 테이블 → `analyze.py`/`classify*.py`로 매칭·분류 → 검증(truth table·segment) → 카드뉴스 보고. 대용량 CSV는 GitHub 용량 제한으로 제외했습니다.
