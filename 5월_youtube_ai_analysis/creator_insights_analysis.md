# Creator Insights AI 채팅 시스템 — 기술 분석 문서

---

## 서비스 개요

**Creator Insights**는 광고주와 마케터가 유튜브 크리에이터를 자연어로 탐색하고 분석할 수 있는 B2B SaaS 플랫폼이다. 사용자가 조건을 말로 설명하면 AI가 내부 DB에서 적합한 채널을 자동으로 찾아준다.

- 주요 사용자: 광고 에이전시, 브랜드 마케터
- 핵심 가치: 유튜버 탐색 과정을 AI로 자동화
- 인터페이스: 한국어 기반 채팅 UI

---

## 기술 스택

| 영역 | 기술 |
|------|------|
| Backend | Django REST Framework (Python) |
| Frontend | Next.js + Jotai (상태관리) |
| AI | OpenAI API (GPT 계열 모델) |
| Database | PostgreSQL |
| 인증 | JWT |
| 캐싱 | Redis (Django cache framework) |

---

## 사용자 흐름

1. 로그인 (JWT 인증 + 프리미엄 등급 확인)
2. 채팅창에 자연어로 입력 — 예: "뷰티 채널인데 구독자 10만~50만, 광고 이력 있는 곳 찾아줘"
3. AI가 의도를 분류하고 필터를 자동 생성
4. 조건에 맞는 채널 목록을 테이블로 표시
5. 대화로 조건을 다듬거나 채널 정보 추가 질문
6. CSV로 내보내기

### 티켓(사용량) 시스템

| 등급 | 월 사용 | 일 사용 |
|------|---------|---------|
| Basic | 10회 | 20회 |
| Team | 90회 | 50회 |
| Partner | 무제한 | 80회 |

---

## AI 처리 구조

사용자 메시지가 들어오면 두 번의 AI 호출이 일어난다.

### 1단계: 라우터 — 의도 분류

파일: `backend/creators_insights/systems/router-system-improved.txt`

| 라우트 | 동작 | 예시 |
|--------|------|------|
| list_up | 조건 기반 채널 탐색 | "뷰티 채널 중 구독자 50만 이상" |
| similar_list_up | 유사 채널 추천 | "숏박스 같은 채널 찾아줘" |
| filters_adjust | 기존 조건 조정 | "너무 많아, 줄여줘" |
| channel_info | 단일 채널 분석 | "침착맨 채널 광고 효율 어때?" |
| channel_compare | 두 채널 비교 | "A랑 B 비교해줘" |
| explain_result | 결과 이유 설명 | "왜 이 채널이 나왔어?" |
| ad_evaluation | 광고 적합성 평가 | "이 채널이랑 광고 괜찮을까?" |
| small_talk | 그 외 / 불가능 요청 | "날씨 어때?" |

### 2단계: 필터 생성 — 자연어 → DB 쿼리

파일: `backend/creators_insights/systems/filters-generate-system-optimized.txt`

자연어 입력을 받아 JSON 필터로 변환한다.

**입력 예시:**
> "뷰티 채널, 구독자 10~50만, 참여도 좋은 곳"

**생성 필터:**
```json
{
  "category": ["뷰티 & 메이크업"],
  "subscribers": [100000, 500000],
  "engagement_rate": [2.18, 1000000],
  "channel_keyword_exclude": ["기업", "공식", "브랜드", "키즈"]
}
```

> 기업·공식·브랜드·키즈 채널은 기본으로 자동 제외된다. 사용자가 명시하면 포함 가능.

---

## 필터 전체 목록

### 규모 및 성과 지표

| 필터 키 | 설명 | 형식 |
|---------|------|------|
| subscribers | 구독자 수 | [최소, 최대] |
| average_views | 평균 조회수 | [최소, 최대] |
| average_views_ads | 광고 영상 평균 조회수 | [최소, 최대] |
| average_views_last_10 | 최근 10개 영상 평균 조회수 | [최소, 최대] |
| engagement_rate | 참여율 (2.18% 이상이면 높음) | [최소, 최대] |
| subs_growth_3_months | 최근 3개월 구독자 성장률 (%) | [최소, 최대] |
| short_ratio | 쇼츠 비율 (%) | [최소, 최대] |
| average_duration | 평균 영상 길이 (초) | [최소, 최대] |

### 시청자 특성

| 필터 키 | 설명 | 형식 |
|---------|------|------|
| age | 시청자 연령대 | ["18_24", "25_34", ...] |
| gender | 시청자 성별 | ["M"] 또는 ["F"] |
| min_demo | 해당 인구통계 최소 비율 (%) | 숫자 |

### 콘텐츠 및 카테고리

| 필터 키 | 설명 | 형식 |
|---------|------|------|
| category | 채널 카테고리 | ["뷰티 & 메이크업", "게임", ...] |
| category_exclude | 제외 카테고리 | 위와 동일 |
| video_category | 영상 유형 | ["먹방", "브이로그", "ASMR", ...] |
| channel_keyword | 포함 키워드 | ["키워드"] |
| channel_keyword_exclude | 제외 키워드 | ["키즈", "기업", ...] |

### 채널 특성 및 이력

| 필터 키 | 설명 | 형식 |
|---------|------|------|
| last_update_diff | 마지막 업로드 후 경과일 | 30, 90, 180 중 선택 |
| registerYouTubeDate | 채널 개설 시점 | "last 1 year" 등 |
| include_industries | 광고한 산업 포함 | ["음식 & 음료", ...] |
| exclude_industries | 광고한 산업 제외 | 위와 동일 |
| trend_count | 인기 급상승 노출 여부 | true / false |
| youtube_shopping | 유튜브 쇼핑 기능 사용 여부 | true / false |

> 사용 불가 필터: budget, CPM, 지역, 언어, brand_safety 등 — 요청 시 AI가 거절함.

---

## 필터 검증 파이프라인

필터 생성 후 DB 쿼리 전에 5단계 검증과 자동 완화를 거친다.

```
생성된 필터
  ↓ 1. _sanitize_filters()          : min > max 역전 등 기본 오류 수정
  ↓ 2. _remove_invalid_filters()    : 허용되지 않는 필드 제거
  ↓ 3. _fix_null_values_in_filters(): null 값 정규화
  ↓ 4. _ensure_register_date_valid(): 날짜 형식 검증
  ↓ 5. DB 쿼리 실행 → 결과 0건이면
  ↓ 6. relax_filters() 자동 호출    : 조건 완화 후 재시도 (최대 3회)
```

파일: `backend/creators_insights/filter_pipeline.py` (1,254줄)

---

## 주요 파일 구조

### Backend

| 파일 | 역할 | 규모 |
|------|------|------|
| creators_insights/views.py | 메인 API 엔드포인트 | 1,686줄 |
| creators_insights/filter_pipeline.py | 필터 검증 및 자동 완화 | 1,254줄 |
| creators_insights/ai_utils.py | OpenAI API 래퍼 | — |
| creators_insights/constants.py | 허용값 상수 전체 정의 | — |
| creators_insights/systems/ | AI 시스템 프롬프트 (.txt) | 15개+ |

### Frontend

| 파일 | 역할 |
|------|------|
| pages/creator-insights/index.jsx | 메인 페이지 |
| components/creator-insights/chat/chatPanel.jsx | 채팅 UI (456줄) |
| components/creator-insights/table/creatorTablePanel.jsx | 결과 테이블 |
| service/creator-insights.js | API 클라이언트 |

### AI 시스템 프롬프트 파일

| 파일 | 역할 | 크기 |
|------|------|------|
| router-system-improved.txt | 의도 분류 | 143줄 |
| filters-generate-system-optimized.txt | 필터 생성 | 159줄 |
| filters-adjust-system-optimized.txt | 필터 조정 | 130줄 |
| channel-insight-system.txt | 단일 채널 분석 | — |
| channel-compare-system.txt | 채널 비교 | — |
| explain-result-system.txt | 결과 이유 설명 | — |
| small-talk-system.txt | 불가 요청 처리 | — |

---

## API 엔드포인트

| Method | Path | 역할 | 티켓 차감 |
|--------|------|------|-----------|
| POST | /creators-insights/ai-chat | 메인 AI 채팅 | O |
| POST | /creators-insights/channel-list | 필터 기반 채널 목록 | X |
| POST | /creators-insights/preview | 미리보기 (10개) | X |
| GET | /creators-insights/ticket-left | 잔여 티켓 확인 | X |
| POST | /creators-insights/recommend-question | 추천 질문 생성 | X |
| GET | /creators-insights/check | 헬스체크 | X |

---

## 프론트엔드 상태 관리

Jotai(Atoms) 기반으로 채팅 세션 상태를 관리한다.

| 상태 | 역할 |
|------|------|
| aiChatLogState | 화면에 표시되는 대화 기록 |
| aiChatConversationState | AI에 보내는 최근 6턴 대화 (컨텍스트용) |
| aiChatCurrentFiltersState | 현재 적용된 필터 JSON |
| aiChatConversationContextState | 대화 맥락 요약 문자열 |
| aiChatViewState | "chat" 또는 "list" — 결과 표시 모드 결정 |
| ticketModalState | 티켓 소진 시 모달 표시 여부 |

---

## 결과 화면에 표시되는 데이터

### 채널 목록 테이블 컬럼

| 컬럼 | 설명 |
|------|------|
| subscribers | 구독자 수 |
| keywords | 연관 키워드 |
| average_duration | 평균 영상 길이 |
| avg_views | 평균 조회수 |
| ad_avg_views | 광고 평균 조회수 |
| views_subscribers_ratio | 조회수 / 구독자 비율 |
| ad_views_subscribers_ratio | 광고 조회수 / 구독자 비율 |
| ad_last_update_diff | 마지막 광고 날짜 |

### 채널 분석 (channel_info 라우트)
- 최근 브랜드 협업 이력
- 광고 효율 지표
- 브랜드 로고 및 최근 협찬 제품

### 채널 비교 (channel_compare 라우트)
- 두 채널 나란히 핵심 지표 비교
- AI 인사이트 요약

---

## 설계 특징 및 핵심 결정사항

### 시스템 프롬프트를 .txt 파일로 분리 관리
AI 동작을 코드가 아닌 텍스트 파일로 정의하여 재배포 없이 수정 가능. 15개 이상의 프롬프트 파일이 라우트별로 분리되어 있음.

### 필터 자동 완화 (relax_filters)
검색 결과가 0건일 경우 시스템이 자동으로 조건을 완화하고 최대 3회 재시도. 사용자에게 "결과 없음" 대신 조정된 결과를 제공.

### 멀티턴 대화 컨텍스트 유지
최근 6턴의 대화 기록과 컨텍스트 요약 문자열을 함께 AI에 전달하여 대화 흐름이 유지됨.

### 티켓 기반 사용량 제어
등급별 월/일 사용량 제한으로 수익화 구조 내장. Partner 등급은 무제한으로 대형 고객 대응 가능.

### 기본 제외 필터
기업·공식·브랜드·키즈 채널을 자동으로 제외해 개인 크리에이터 중심 결과 제공. 사용자가 명시하면 해제 가능.

---

## 캐싱 전략

| 대상 | TTL |
|------|-----|
| AI 필터 생성 결과 | 600초 |
| 채널 데이터 | 600초 |
| 필터 카운트 | 60초 |
| 브랜드 정보 | 300초 |
