# 유튜브 크리에이터 AI 분석 (Creator Insights)

광고주·마케터가 **자연어로 유튜브 크리에이터를 탐색**하는 Creator Insights B2B SaaS 플랫폼의 코드·시스템 구조를, 개발자와 서비스 기획자 모두가 읽을 수 있게 정리한 기술 분석 문서입니다.

- **분야:** AI / 프롬프트 (코드·시스템 분석)
- **분석 대상:** Creator Insights (Django REST + Next.js + OpenAI + PostgreSQL + JWT + Redis)
- **도움:** Claude Sonnet 4.6

## 핵심 내용
- **2단계 AI 구조:** 자연어 입력 → ① 라우터(의도 8종 분류) → ② 필터 생성(자연어 → DB 쿼리 JSON) → 채널 리스트업
- **필터 검증 파이프라인:** 생성된 필터를 5단계 검증 + 결과 0건 시 `relax_filters()` 자동 완화(최대 3회 재시도)
- **시스템 프롬프트 파일 분리:** AI 동작을 코드가 아닌 15개+ `.txt` 프롬프트로 관리 → 재배포 없이 수정
- **티켓 사용량 시스템:** 등급(Basic/Team/Partner)별 월·일 사용 제한으로 수익화 구조 내장
- **멀티턴 컨텍스트:** 최근 6턴 + 컨텍스트 요약을 함께 전달

## 파일

| 파일 | 설명 |
|---|---|
| `creator_insights_analysis.md` | 전체 기술 분석 문서 (스택·AI 처리 구조·필터 목록·API·상태관리·설계 결정) |
| `creator_insights_overview.html` | 분석 내용을 정리한 개요 HTML |
| `creator_insights_diagram.html` | 시스템 구조 다이어그램 |
| `쉬운 설명.png`, `시스템 파이프라인.png` | 한눈에 보는 요약·파이프라인 이미지 |

> 분석 대상이었던 Creator Insights 원본 소스 코드는 하이픈의 비공개 자산이므로 레포에 포함하지 않습니다.
