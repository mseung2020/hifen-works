# hifen-works

김명승 × 하이픈 작업 포트폴리오. 각 폴더는 하나의 작업 프로젝트이며, 폴더별 README로 내용을 설명합니다.

## 목차

### AI / 프롬프트
- [3월_insta_ranker_prompt](3월_insta_ranker_prompt/) — 검색 필터 조합으로 크리에이터 랭킹 리스트 타이틀·설명글을 자동 생성하는 DIFY 프롬프트
- [4월_insta_label_prompt](4월_insta_label_prompt/) — 인스타 계정을 6개 Layer로 점수화하고 오디언스까지 추정하는 라벨링 프롬프트
- [4월_youtube_comment_prompt](4월_youtube_comment_prompt/) — 유튜브 댓글로 시청자 성별·연령 분석을 검증하고 이상치를 재분배하는 프롬프트
- [5월_insta_trend_prompt](5월_insta_trend_prompt/) — 트렌드 클러스터를 추출해 광고주 인사이트·트렌드 스토리를 생성하는 Dify 워크플로우 (자기검증 + Python 사실검증)
- [6월_insta_challenge_prompt](6월_insta_challenge_prompt/) — 릴스 오리지널 오디오 후보 풀에서 챌린지성 콘텐츠 10개를 선별·랭킹·작명하는 프롬프트

### 백엔드 / 코드
- [3월_coupon_analysis](3월_coupon_analysis/) — 하이픈 백엔드의 쿠폰 코드를 분석해 퍼센티지 할인 도입 개편안과 코드 수정 가이드를 작성
- [4월_claude_code_analysis](4월_claude_code_analysis/) — Claude Code 소스코드·내부 지침을 분석해 AI 설계 원리와 챗봇 기획 인사이트를 정리한 보고서
- [4월_hifen_scheme_analysis](4월_hifen_scheme_analysis/) — 하이픈 백엔드·프론트 레포 전체의 DB 스키마·API 사용 현황을 분석해 만든 개발자용 지식백과 HTML
- [6월_hifen_user_guide](6월_hifen_user_guide/) — 하이픈 40개 레포와 UI 화면을 분석해 기능별 사용자 흐름을 담은 유저 가이드 HTML

### 데이터 분석
- [3월_insta_drop_filter](3월_insta_drop_filter/) — 인스타 광고성 게시물을 걸러내는 최적 필터 조건을 recall/drop rate로 탐색하는 FastAPI 대시보드
- [3월_insta_creator_similar](3월_insta_creator_similar/) — 크리에이터 라벨(유형·주인공·유도행동·분야·무드)을 비교해 유사도를 검증하는 Flask 웹앱
- [4월_insta_clustering](4월_insta_clustering/) — 인스타 트렌드 클러스터를 4분면 버블차트로 시각화하는 Flask 웹앱
- [4월_marketer_dashboard](4월_marketer_dashboard/) — 브랜드별 경쟁사·크리에이터·올리브영 데이터를 모은 마케터 컨설팅 대시보드 (Flask + Chart.js)
- [5월_insta_trend_stage](5월_insta_trend_stage/) — 트렌드 키워드가 생애주기 어느 단계인지 일별 누적 그래프로 진단하는 Flask 대시보드
- [5월_insta_language_analysis](5월_insta_language_analysis/) — 경쟁 브랜드 광고 캡션의 표현 패턴 점유율·언어 공백을 비교하는 프로토타입
- [6월_ad_market_headline](6월_ad_market_headline/) — 광고시장 일일 사건을 헤드라인 10선 카드 피드로 정리하는 마케터 데일리 대시보드
- [6월_LG_data_insight](6월_LG_data_insight/) — 광고·올리브영·크리에이터 데이터를 회귀·상관·시계열로 분석해 만화·카드뉴스 리포트로 마감한 인사이트 프로젝트
- [6월_Abib_data_insight](6월_Abib_data_insight/) — 아비브 브랜드의 크리에이터 티어 분석을 담은 Flask 간이 리포트 앱

### 라벨링
- [3월_youtube_insta_label](3월_youtube_insta_label/) — 유광기 어드민에서 유튜브·인스타 콘텐츠의 광고 브랜드를 태깅하는 라벨링 업무 + 보고서
