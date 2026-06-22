# 데이터 요약

웹앱이 참조하는 `total_creator_analysis.csv`는 231MB(GitHub 100MB 초과)라 제외하고, 스키마·규모·라벨 분포·샘플로 요약합니다.

- **포함:** `total_creator_analysis.sample.csv` — 앞 99행 샘플 (형식 확인용)
- **제외 원본:** `total_creator_analysis.csv` (231MB)
  - **규모:** 2,142,909행 / 고유 유저 645,018명 (유저 1명당 복수 라벨 행)
  - **컬럼:** `user_id, format, target_country, persona, behavior, topic, mood`
  - 유사도 비교에 쓰이는 5개 필드: `format, persona, behavior, topic, mood`

## 라벨 분포 (상위 값)

| 필드 | distinct | 주요 값 |
|---|---|---|
| format (대표유형) | 6 | 눈호강/무드형, 꿀팁/리뷰형, 공감/일상형, 루틴/스킬형, 예능/리액션형 |
| persona (주인공) | 10 | 인물(운영자 본인), 장소/공간, 제품/아이템, 가족/아이, 음식, 반려동물 … |
| behavior (유도행동) | 5 | 팔로우 유도, 방문/예약 유도, 구매/문의 유도, 저장 유도, 공유 유도 |
| topic (분야/주제) | 15 | 여행/휴양, 뷰티, 아트/창작, 카페/핫플, 맛집/푸드, 리빙/인테리어 … |
| mood (무드/톤) | 12 | 내추럴/따뜻, 화사/밝음, 미니멀/클린, 러블리/큐트, 감성/서정 … |
| target_country | 17 | (국가 코드) |

> 유사도 비교는 두 크리에이터의 위 5개 필드 값 집합(set)의 교집합 매칭 개수로 0~5점을 매깁니다.
