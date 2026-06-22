# 하이픈 유저 가이드

하이픈 서비스의 **GitHub 레포 40개를 직접 들여다보고** 유저 UI 화면을 캡처해서, 어떤 기능이 어떤 흐름으로 동작하는지 한 문서로 풀어낸 결과물입니다. 회원가입·로그인부터 구독 변경/해지, 크레딧 충전, 멤버 관리, 쿠폰 적용까지 사용자 여정을 화면과 함께 설명합니다.

- **분야:** 백엔드 / 코드
- **분석 규모:** 하이픈 전체 레포 40개 + 유저 UI 화면 캡처
- **구성:** 기능별·흐름별 유저 가이드 + 개발자용 API 가이드

## 결과물

| 파일 | 설명 |
|---|---|
| [`hifen_user_guide_standalone.html`](hifen_user_guide_standalone.html) | **메인 유저 가이드** — UI 캡처 42장을 base64로 인라인한 자체 완결형 단일 HTML. 브라우저로 바로 열람 (외부 의존 없음) |
| [`hifen_api_guide.html`](hifen_api_guide.html) | 개발자용 API 가이드 (CDN highlight.js로 코드 하이라이팅) |
| `build_standalone.py` | 유저 가이드 HTML + 화면 캡처들을 하나의 standalone HTML로 묶는 빌드 스크립트 |

> 분석 대상이었던 하이픈 40개 레포는 외부 비공개 자산이므로 레포에 포함하지 않습니다. 원본 화면 캡처는 standalone HTML 안에 모두 인라인되어 있습니다.
