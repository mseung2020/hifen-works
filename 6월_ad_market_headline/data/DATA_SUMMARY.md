# 데이터 요약

이 폴더에는 헤드라인 생성 파이프라인의 **입력 JSON(소용량)은 포함**하고, 원천 광고시장 raw CSV(대용량)는 제외했습니다.

## 포함된 데이터 (`data/`)
| 파일 | 설명 |
|---|---|
| `llm_input_2026-06-01.json`, `_kr.json`, `2026-06-02.json` | LLM에 투입된 일자별 입력 (헤드라인 생성용) |
| `yt_ppl.json`, `insta_ppl.json` | 유튜브·인스타 PPL 집계 |
| `instream_brands.json`, `instream_viral.json` | 인스트림 광고 브랜드·바이럴 집계 |

## 제외된 원천 raw CSV (`최종data/`)
GitHub 용량 문제로 제외. 파이프라인이 이 raw들을 집계해 위 LLM 입력 JSON을 만듭니다.

| 파일 | 크기 | 내용 |
|---|---|---|
| `bumper_video_trend.csv` | 172MB | 범퍼 광고 영상 트렌드 (100MB 초과) |
| `scene.csv` | 42MB | 장면 분석 |
| `on_off.csv` | 39MB | 광고 on/off |
| `ad_analized.csv` | 39MB | 광고 분석 |
| `bumper_ad.csv` | 31MB | 범퍼 광고 |
| `brand_video_trend.csv` | 24MB | 브랜드 영상 트렌드 |
| 그 외 | <2MB | cost_per_day/week, cpm_by_industry, ad_global, brand_bumper_cost_per_day 등 |

> 원천 CSV → `build_llm_input.py`(+ `download_today_queries.sql`)로 일자별 LLM 입력 JSON 생성 → Dify 워크플로우가 헤드라인 10선 생성 → 목업 대시보드에 표시.
