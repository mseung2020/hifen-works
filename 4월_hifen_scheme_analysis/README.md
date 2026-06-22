# 하이픈 지식백과 (DB·API 스키마 분석)

하이픈 서비스의 **백엔드 API 레포와 프론트엔드 레포를 모두 복제**하고, 전체 DB 테이블 스키마·API 엔드포인트·프론트엔드 호출을 서로 연관지어 분석한 뒤, 개발자용 **지식백과 HTML 문서**로 정리한 작업입니다. "어떤 테이블이 어떤 앱·엔드포인트에서 실제로 쓰이는지", "쓰이지 않는 좀비 테이블/엔드포인트는 무엇인지"를 한눈에 볼 수 있게 만들었습니다.

- **분야:** 백엔드 / 코드
- **분석 규모:** 스키마 테이블 517개(사용 257 / 미사용 260), 엔드포인트 636개(호출 453 / 미호출 183), 테이블 관계 196개
- **분석 대상:** `ugwanggiAPI`(백엔드), `ugwanggiNext`(프론트엔드)

## 결과물

[`하이픈지식백과.html`](하이픈지식백과.html) — 자체 완결형 단일 HTML 문서 (데이터 인라인, d3.js 시각화). 브라우저로 바로 열람 가능. 테이블 사용 현황, 앱↔테이블 매핑, 서비스 간 관계 그래프, 정규화/비정규화 핫스팟, 좀비 테이블·미호출 엔드포인트 진단 등을 담음.

## 분석 데이터 (`core_materials/`)
분석 결과를 구조화한 CSV·JSON 모음 (HTML에 인라인된 `site_data.json`의 원본):

| 파일 | 내용 |
|---|---|
| `hifen_scheme.csv` | 전체 DB 스키마 |
| `api_endpoints.csv` / `endpoint_usage.csv` | API 엔드포인트 + 호출 여부 |
| `app_to_tables.csv` / `table_to_apps_boosted.csv` | 앱↔테이블 매핑 |
| `table_edges_unified.csv` / `service_edges.csv` | 테이블·서비스 간 관계 그래프 |
| `denormalization_hotspots.csv` / `normalization_clusters.csv` | 정규화 분석 |
| `isolated_tables.csv` / `domain_vs_fk_gap.csv` | 고립 테이블·도메인 갭 진단 |
| `site_data.json` | 위 분석을 통합한 사이트 데이터 |

## 방법론 (`intermediate/`)
분석 파이프라인을 직접 구현한 스크립트와 중간 리포트:
- **추출:** `extract_endpoints.py`, `extract_relations.py`, `extract_joins.py`, `extract_service_edges.py`
- **분석:** `analyze_normalization.py`, `analyze_name_clusters.py`, `audit_core.py`, `boost_pass.py`
- **라벨링:** `label_tables.py`, `refine_labels.py`, `finalize_labels.py`, `map_apps_tables.py`
- **빌드:** `build_site_data.py`, `build_html.py`
- **리포트(.md):** 엔드포인트·관계·서비스·정규화·미사용 엔드포인트 분석 + 정보구조(IA) 설계

## 기타
- `비평.md`, `비평2.md` — 완성된 지식백과 문서에 대한 자기 비평/개선 검토

> 분석 대상이었던 원본 백엔드·프론트엔드 레포는 외부 비공개 자산이며 시크릿(인증 키·토큰)을 포함하므로 레포에 포함하지 않습니다.
