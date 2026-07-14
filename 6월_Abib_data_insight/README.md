# Abib 브랜드 데이터 인사이트 리포트

아비브(Abib) 브랜드를 대상으로 **크리에이터 티어 분석**을 담은 간이 리포트 Flask 앱입니다. 유튜브·인스타·제품·올리브영 랭킹 데이터를 가공해 브랜드가 어떤 체급(티어)의 크리에이터를 활용했는지 조회할 수 있게 정리했습니다.

- **분야:** 데이터 분석
- **결과물 형태:** Flask 조회 리포트 앱 + 목업 시안 모음

## 실행

```
pip install flask
python app.py        # → static/abib_data.json 을 읽어 리포트 제공
```
> `static/abib_data.json`(사전 가공 결과)이 포함되어 있어 원천 CSV 없이 바로 실행됩니다. 데이터 갱신 시 `prepare_data.py`로 재생성.

## 구성

| 경로 | 설명 |
|---|---|
| `app.py` | Flask 앱. `static/abib_data.json`을 읽어 티어별 조회 API/리포트 제공 |
| `prepare_data.py` | 원천 CSV → 티어 분석 → `abib_data.json` 생성 |
| `analyze_tier.py` | 크리에이터 티어 분석 로직 |
| `templates/index.html` | 리포트 UI |
| `static/abib_data.json` | 앱 입력 데이터 (가공 완료) |
| `data/` | 아비브 원천 CSV(유튜브·인스타·제품·올리브영) + 대용량 CSV 요약([DATA_SUMMARY.md](data/DATA_SUMMARY.md)) |
| `목업 예시/` | 카드뉴스·만화 리포트 등 리포트 디자인 시안 모음 (HTML + PDF + 페이지 이미지) |
