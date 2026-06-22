# Step 9 — HTML 정보 구조 & 디자인 설계서

**목적**: `core_materials/site_data.json`을 사람에게 전달하기 위한 HTML의
뷰 구조·내비게이션·디자인 시스템을 확정한다. 프로토타입 제작(Step 10) 진입
전의 설계 도면.

**대상 독자**: 비개발자(기획·PM·임원)부터 개발자(AI 매뉴얼 담당자)까지.
비개발자도 상단만 훑으면 핵심을 이해할 수 있어야 한다.

**표현 방침**: 이모지·장식 문자 사용 금지. 모든 표현은 **HTML/CSS 문법 자체**
— 색, 타이포그래피, 선, 공백, SVG 아이콘 — 로 구현한다.

---

## 0. 3대 원칙 재확인

| 원칙 | 설계 적용 |
|---|---|
| **가시성** | 한 화면 = 한 메시지. 빅넘버 + 색상 코딩. 상단 고정 네비게이션. |
| **직관성** | 한국어 동사 ("연결됨 / 기댐 / 공유됨"), 메타포(태양계·소행성·유령 모델), 전문용어에 툴팁. |
| **신뢰성** | 전제 박스 상단 고정, 모든 수치에 confidence 배지, 근거 원클릭, 한계 페이지 별도. |

---

## 1. 사이트맵 (7개 뷰)

```
홈 (한 장 대시보드)
│
├── 서비스 지도       — 앱 간의 의존 관계
├── 테이블 탐색기     — 517개 테이블 필터·검색
├── 관계 그래프       — 196개 테이블 간 관계 ERD
├── API 엔드포인트    — 636개 × 호출 여부
├── 데이터 품질       — 좀비·고립·비정규화 핫스팟
└── 전제와 한계       — 이 분석이 보장하는/못하는 것
```

상단에 이 7개 탭이 고정. 각 탭은 단어(텍스트) 라벨만 — 아이콘은 선택.
초기 프로토타입은 텍스트만으로 출발한다.

---

## 2. 디자인 시스템

### 2.1 컬러 팔레트

최소주의. 화이트 베이스 + 의미 있는 색만.

```
배경         #FAFAF9   off-white paper
본문         #1F2937   near-black
보조 텍스트  #6B7280   gray-500
악센트 주요  #2563EB   blue-600   링크·CTA
악센트 경고  #F59E0B   amber-500  주의
악센트 위험  #DC2626   red-600    치명·미사용
성공/건강    #16A34A   green-600
중립         #9CA3AF   gray-400   구분되지 않음
구분선·카드  #E5E7EB   gray-200
```

### 2.2 상태 표시 (이모지 대체)

신호등은 8px 원형 dot (CSS `border-radius: 50%`) + 옆에 한국어 라벨.

```
status dot:  8px × 8px · border-radius: 50% · background 색상만 변경
상태라벨:     Pretendard 500 · 13px · 해당 색상

[●] 건강    (green-600)    health = healthy
[●] 주의    (amber-500)    over_developed
[●] 문제    (red-600)      abandoned / UNCALLED / UNUSED
[●] 고립    (gray-400)     isolated / no_api
```

차트의 파이·막대도 이 4색 팔레트 내에서만 사용.

### 2.3 신뢰도 배지 (Confidence)

CSS로 스타일링. 이모지 없음.

```html
<span class="badge badge-high">HIGH</span>   배경 green-50, 텍스트 green-700, border green-200
<span class="badge badge-med">MED</span>     배경 amber-50, 텍스트 amber-700, border amber-200
<span class="badge badge-low">LOW</span>     배경 gray-100, 텍스트 gray-600, 빗금 dashed border
```

배지는 텍스트 13px · 대문자 · padding 2×8px · border-radius 4px.

### 2.4 근거 버튼 (Evidence)

각 카드/수치 우하단에 텍스트 버튼:

```html
<button class="evidence-btn">근거 보기</button>
```

클릭 시 오버레이 패널:
- 소스 CSV 경로 (모노 폰트)
- 해당 행 raw 값
- 추출 스크립트 경로

### 2.5 메타포 가이드 (이모지 제거본)

메타포는 **언어**로만 구사한다. 헤더 아이콘은 SVG 혹은 사용 안 함.

| 개념 | 메타포 표현 (언어) |
|---|---|
| 정규화 클러스터 | "항성과 행성 구조" — 중심 테이블과 위성 테이블 |
| 고립 테이블 | "떠도는 소행성" / "관계 그래프 밖의 스탠드얼론" |
| 서비스 의존 | "기댐 관계" — A가 B에게 얼마나 기대는지 |
| 좀비 모델 | "유령 모델" — 코드엔 있고 DB엔 없는 설계 잔해 |
| 허브 테이블 | "중심 허브" — 많은 서비스가 공유 |
| 미사용 엔드포인트 | "먼지 쌓인 문" — 만들었지만 아무도 여는 사람 없음 |

보고서 스타일이지 장식 스타일이 아님. 헤드라인은 `h2` 태그만으로 구성.

### 2.6 타이포그래피

```
h1      Pretendard 700 · 32px · line 1.3
h2      Pretendard 600 · 22px · margin-top 40px
h3      Pretendard 600 · 17px
body    Pretendard 400 · 15px · line 1.7
small   Pretendard 400 · 13px · color gray-500
number  Pretendard 700 · 56px · font-feature-settings 'tnum'
mono    JetBrains Mono 400 · 14px (테이블명·경로·URL)
```

줄 길이 최대 66자. 긴 표는 스크롤 대신 페이지네이션.

### 2.7 핵심 컴포넌트

모두 순수 HTML/CSS + 최소 JS.

- **BigNumberCard**: 큰 숫자 + 라벨 + 상태 dot
- **StatBar**: 가로 분할 바 (USED 257 / UNUSED 260 시각화)
- **TableChip**: 테이블명 chip. 클릭 시 상세 모달
- **AppChip**: 앱명 chip. 클릭 시 서비스 지도 하이라이트
- **ConfidenceBadge**: 위 2.3
- **EvidencePopover**: 근거 보기 오버레이
- **Tooltip**: 전문용어에 점선 underline + hover 시 작은 팝업

엣지 굵기·선 종류는 **CSS/SVG 속성으로 표현**:
- HIGH confidence → 실선 2px
- MED confidence → 실선 1px
- LOW confidence → 점선 1px (`stroke-dasharray`)

---

## 3. 뷰별 상세 스펙

### 3.1 홈 — 한 장 대시보드

**한 줄 메시지**: 이 서비스의 전체 모습을 30초에 훑는다.

**필수 요소 (위→아래 순)**:

1. **전제 박스** (sticky top, 얇은 파란 테두리 + 배경 blue-50)
   - "이 분석은 백엔드 하나, 프론트 하나, 스키마 하나로 이루어진 세계를
     가정합니다. 스냅샷 2026-04-22."
2. **빅넘버 4장** (4열 grid)
   - `517` 테이블 · 하단에 USED 257 / UNUSED 260 StatBar
   - `636` API 엔드포인트 · CALLED 453 / UNCALLED 183 StatBar
   - `28` 서비스(앱) · 건강 분포 미니 바 (건강 14, 주의 7, 방치 4, 고립 3)
   - `196 + 122` 관계 엣지 (테이블 + 서비스)
3. **서비스 건강 3열 블록**: 각 열은 건강/주의/방치 앱 chip 목록
4. **헤드라인 인사이트 3줄 카드**
   - "141개 테이블이 `users_ugwanggi` 중심으로 하나의 거대 클러스터"
   - "전체 엔드포인트의 29%가 프론트에서 호출되지 않음 (주로 aichat)"
   - "유령 모델 2건 발견 (상세는 데이터 품질 뷰)"
5. **뷰 카드 그리드**: 6개 뷰 미리보기 카드 (제목·한 줄·주요 수치)

**데이터 바인딩**: `meta`, `apps[*].health`, `diagnostics`, 상위 서비스 edges.

---

### 3.2 서비스 지도

**한 줄 메시지**: 어떤 서비스가 누구에게 기대고 있는가.

**메인 시각화**: force-directed 그래프 (D3)
- 노드 = 앱 28개
- 노드 크기 = owned_tables 수
- 노드 색 = health 4색 (위 팔레트)
- 엣지 = service_edges 122개
- 엣지 굵기 = weight
- 엣지 색 = 소스 종류 (IMPORTS blue-600 · SHARED_TABLE amber-500 · CRON purple-600, 복수 소스는 실선+점선 혼합)

**인터랙션**:
- 노드 호버: 앱 카드 팝업 (owned·consumed 수치)
- 노드 클릭: 우측 패널에 앱 상세 (엔드포인트 통계, in/out 의존 목록)
- 엣지 클릭: 근거 모달 (import 샘플 3개, 공유 테이블 목록, cron 힌트)

**좌측 범례**: 노드 크기·색 · 엣지 색 의미. 항상 고정.

**상단 필터**: Health 토글 · 소스 종류 토글 · 검색창.

**데이터 바인딩**: `apps`, `edges.service_edges`.

---

### 3.3 테이블 탐색기

**한 줄 메시지**: 517개 테이블을 필터·검색으로 골라 자세히 본다.

**레이아웃**: 좌측 필터 패널 + 우측 테이블 카드 그리드

**좌측 필터**:
- 사용 여부: USED / UNUSED
- 도메인 (이름 prefix): ugwanggi · instagram · YT_bumper · oliveyoung · tiktok · brand · …
- 소유 앱: 28개 체크박스
- 서브카테고리: TRULY_UNUSED / ARCHIVE_SUFFIX / NOT_A_DB_REF / NO_MODEL / MULTI_OWNER
- 고립 여부 토글
- 검색창: 이름 incremental search

**우측 카드**:
- 테이블명 (모노) + 상태 dot
- 소유 앱 chip
- 주요 수치: 컬럼 N · 들어오는 FK M · 나가는 FK K · 소비 앱 수
- 카드 클릭 → 상세 모달

**테이블 상세 모달** (공통 컴포넌트 — 3.4에서도 재사용):
- 헤더: 이름 · 상태 · 서브카테고리 · 신뢰도 배지
- 컬럼 표: 이름 / 타입 / Null / Key / 기본값 / 설명
- 소속 클러스터 요약 + 허브 테이블 링크
- 들어오는 FK 리스트
- 나가는 FK 리스트
- 공유 컬럼(허브 키) 카드
- 이 테이블을 건드리는 엔드포인트 리스트
- 버튼: 관계 그래프에서 보기 / 근거 보기 / 소유 앱 보기

**데이터 바인딩**: `tables`, `clusters`, `edges.table_edges`, `endpoints`.

---

### 3.4 관계 그래프

**한 줄 메시지**: 테이블들이 서로 어떻게 엮여 있는가.

**메인 시각화**: force-directed 그래프
- 노드 = 257 USED 테이블
- 기본 뷰: 141-테이블 거대 클러스터 중심 배치, 나머지 위성 클러스터·고립 테이블이 주변
- 노드 색 = 도메인 prefix (자동 팔레트, 범례 별도)
- 노드 크기 = 들어오는 FK 수
- 엣지 선: HIGH = 실선 2px / MED = 점선 1px
- 고립 테이블: 주변부에 grid로 정렬 ("소행성 벨트" 섹션)

**인터랙션**:
- 클러스터 줌: "C001 확대 / 전체"
- 필터: 도메인 색 / USED만 · isolated 포함 / HIGH만 · MED 포함
- 노드 클릭: 우측 패널에 테이블 상세 카드 (3.3 모달 재사용)
- 엣지 클릭: 관계 상세 (컬럼·모델 파일·confidence 근거)

**상단 고정 배지**:
- "196 관계 중 188 HIGH (개발자 의도) · 8 MED (raw SQL 관찰)"
- 유령 모델 2건, 자기참조 1건 링크 (데이터 품질 뷰로 이동)

**데이터 바인딩**: `tables`, `edges.table_edges`, `clusters`, `diagnostics.self_loops`.

---

### 3.5 API 엔드포인트

**한 줄 메시지**: 636개 API 중 누가 살아있고 누가 먼지 쌓였는가.

**상단 대시보드 스트립**:
- CALLED 453 (71%) · UNCALLED 183 (29%)
- 앱별 미사용률 랭킹 수평 막대
- 메소드 분포 파이 (4색 팔레트)

**메인 뷰: 앱 × 엔드포인트 매트릭스**
- 세로축 = 28개 앱
- 각 행 = 해당 앱의 엔드포인트들이 작은 정사각 칸으로 표현 (점묘형)
- 칸 색: 건강(CALLED) / 문제(UNCALLED)
- 앱 행 펼치면 엔드포인트 리스트 테이블
  - HTTP 메소드 chip · URL (모노) · 뷰 레퍼런스 · tables_touched chip · usage · confidence · 근거

**엔드포인트 상세 drawer**:
- URL · 메소드 · 뷰 파일 링크
- 건드리는 테이블 chip들 (클릭 시 테이블 모달)
- usage 판정 근거: 매치 타입(exact/prefix) + 프론트 호출 파일 경로

**"주목할 엔드포인트" 섹션**:
- 5개 이상 테이블을 건드리는 복합 오케스트레이션 Top 10
- 0개 테이블 터치 103건 (헬스체크·프록시 후보)
- UNCALLED인데 테이블 여러 개 건드리는 고비용 잔해 Top 10

**데이터 바인딩**: `endpoints`, `apps`.

---

### 3.6 데이터 품질

**한 줄 메시지**: 이 시스템에 남아있는 기술 부채와 설계 이상 징후.

**섹션 6개 (카드형)**:

1. **유령 모델 2건** — Django 코드엔 있지만 DB엔 없는 테이블
   - 각 카드: 모델명 · 선언 파일 · 선언된 테이블명 · "이 모델 호출 시 런타임 에러" 경고
2. **모델 없는 테이블 (NO_MODEL) 10건** — raw SQL로만 접근
3. **비정규화 핫스팟 18건** — 공유 컬럼을 가진 테이블들이 FK로 묶이지 않음
4. **도메인 갭** — 이름상 같은 도메인인데 FK 커버리지가 낮음 (ugwanggi 0.7%, github 0%)
5. **자기참조 1건** — `ugwanggi_tracked_ad_comment.parent_id` (대댓글 구조, 정상)
6. **MULTI_OWNER 2건** — 두 앱이 같은 테이블을 함께 소유 (instagram / instagram_admin 중복)

각 섹션에 "왜 중요한가" 한 줄 + "다음 조치 힌트".

**데이터 바인딩**: `diagnostics`, `clusters.denormalization_hotspots`, `clusters.domain_gaps`.

---

### 3.7 전제와 한계

**한 줄 메시지**: 이 분석이 확실히 말하는 것과 말하지 못하는 것.

**섹션**:

1. **무엇을 가정하는가 (Closed-world)**
   - 이 세계는 백엔드 + 프론트 + 스키마 셋뿐
   - 모바일앱·제휴API·외부 배치는 존재하지 않음
2. **각 스텝별 신뢰도**
   - Step 1~7 신뢰도 % + 한 줄 근거
3. **의도적으로 단순화한 것**
   - 동적 테이블명 전수 탐색 불가 (샘플 0건 확인)
   - raw SQL 복합 서브쿼리 JOIN은 일부 누락 가능
4. **수동 검수 권장 항목**
   - AMBIGUOUS 2건: `ages`, `genders`
   - LOW confidence 엔드포인트 3건
5. **스냅샷 시점**
   - 분석일 2026-04-22
   - 이후 코드·DB 변경은 반영되지 않음. 재생성 방법(스크립트 재실행) 안내.

**데이터 바인딩**: 하드코딩 + `meta`.

---

## 4. 네비게이션 & 상태 관리

- URL 해시로 상태 보존: `#/tables?used=true&domain=instagram`
- 테이블 상세 모달: `#/tables/instagram_user`
- 서비스 지도 선택: `#/services?focus=aichat`
- 앱 chip·테이블 chip은 어디서든 클릭 → 해당 뷰로 점프

---

## 5. 데이터 바인딩 요약

| 뷰 | 읽는 JSON 슬라이스 |
|---|---|
| 홈 | meta · apps[*].health · diagnostics (요약) |
| 서비스 지도 | apps · edges.service_edges |
| 테이블 탐색기 | tables · clusters · endpoints (역참조) |
| 관계 그래프 | tables · edges.table_edges · clusters · diagnostics.self_loops |
| API 엔드포인트 | endpoints · apps |
| 데이터 품질 | diagnostics · clusters.denormalization_hotspots · clusters.domain_gaps |
| 전제와 한계 | meta + 하드코딩 |

단일 `site_data.json` 로드로 전체 뷰 운용. SPA 느낌이지만 네트워크 요청은
처음 한 번뿐.

---

## 6. 기술 스택

가벼운 단일 HTML 파일 타겟.

- Vanilla JS + ES modules (빌드 없이 바로 실행)
- Chart.js (막대·파이) · d3-force (그래프) · CSS grid (레이아웃)
- Pretendard · JetBrains Mono webfont (CDN)
- 의존성 CDN 3~4개만. `index.html` + `site_data.json` + `assets/` 수준.

파일 더블클릭 → 브라우저에서 즉시 동작 = 목표.

---

## 7. 제작 순서 (Step 10)

1. 기본 레이아웃 · 네비게이션 · 디자인 토큰 (CSS 변수)
2. 홈 (가장 중요한 첫 인상)
3. 테이블 탐색기 + 테이블 상세 모달 (공통 컴포넌트 확립)
4. 서비스 지도
5. 관계 그래프
6. API 엔드포인트
7. 데이터 품질
8. 전제와 한계
9. 전체 검수 · 인쇄 테스트 · 최종 다듬기
