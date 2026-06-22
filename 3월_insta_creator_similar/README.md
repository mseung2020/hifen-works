# 인스타 크리에이터 유사도 분석

기준 크리에이터와 비교 대상 크리에이터의 **라벨 데이터(대표유형·주인공·유도행동·분야·무드)를 비교해 유사도를 검증**하는 Flask 웹앱입니다. 두 계정이 마케팅 관점에서 얼마나 비슷한지를 5개 필드 매칭으로 0~5점으로 보여줍니다.

- **분야:** 데이터 분석
- **결과물 형태:** Flask 서버 + 웹 UI
- **데이터:** 크리에이터 라벨 분석 (645,018명, 유저당 복수 라벨)

## 실행

```
pip install flask flask-cors pandas
python app.py            # → http://localhost:5050
```
> 실행하려면 `total_creator_analysis.csv`(231MB, 아래 참조)가 같은 폴더에 있어야 합니다.

## 구성

| 파일 | 설명 |
|---|---|
| `app.py` | Flask 서버. CSV를 유저별로 인덱싱하고 `/api/compare`(유사도 비교), `/api/search_user`(유저 검색) 제공 |
| `similar_compare.html` | 기준 1명 ↔ 비교 대상 N명을 나란히 비교하는 메인 화면 |
| `similar_single.html` | 단일 비교 화면 |
| `index.html` | 진입 페이지 |

## 비교 로직
기준/비교 대상의 5개 필드(`format, persona, behavior, topic, mood`) 각각에 대해 값 집합의 **교집합이 있으면 매칭**으로 보고, 매칭된 필드 수(0~5)를 유사도 점수로 산출합니다. 각 필드의 공통 값·기준 값·비교 값도 함께 표시합니다.

## 데이터
참조 데이터 `total_creator_analysis.csv`(231MB)는 GitHub 100MB 제한을 넘어 제외했습니다. 스키마·규모·라벨 분포·샘플은 [`data/DATA_SUMMARY.md`](data/DATA_SUMMARY.md)에 요약해 두었습니다.
