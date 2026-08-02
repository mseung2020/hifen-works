# 크리에이터 세일즈 리포트 생성 Dify 워크플로우

크리에이터 프로필·성과 데이터(팔로워, 오디언스, 콘텐츠 성과, 협찬 이력 등)를 입력하면, **광고주 설득용 "크리에이터 세일즈 리포트"를 스토리라인 카드뉴스 형식의 HTML로 자동 생성**하는 Dify 워크플로우입니다. 대시보드식 나열이 아니라 표지→AI 강조 포인트→근거 데이터→마무리 제안으로 이어지는 "한 편의 주장"을 만드는 것이 핵심입니다.

- **분야:** AI / 프롬프트
- **입력:** 크리에이터 리포트 API(`/creators/{user_id}/report`)가 반환하는 JSON — 프로필, 정체성 라벨, 오디언스, 벤치마크, 콘텐츠 성과, 협찬/PPL 이력 등
- **출력:** 6개 LLM 텍스트 슬롯 + 결정적 Code 노드가 조립한 최종 카드뉴스 HTML

## 워크플로우 구조 (6-node 병렬)

```
Start → HTTP Request(리포트 API 호출)
      → [lead_headline / identity_claim / ai_highlights / audience_persona / content_read / closing] (LLM, 병렬 6개)
      → Code 노드(assemble): JSON + 6개 텍스트 → 최종 HTML
      → End
```

6개 LLM 노드가 모두 HTTP Request의 JSON에만 의존하기 때문에 서로 의존관계 없이 **병렬 실행**된다. 표·막대그래프·게이지 같은 "숫자 근거"는 결정적 Code 노드가 그리고, LLM은 각 슬롯에서 "시각적으로 특별한 자리"의 서술(프로즈)만 채운다.

## 슬롯별 "근거 : 자유" 비율 (핵심 로직)

슬롯마다 데이터 근거에 얼마나 묶이는지를 다르게 설계해, 리포트 전체가 숫자 재낭독이 아니라 해석으로 읽히게 한다.

| 슬롯 | 위치 | 성격 | 출력 형식 |
|---|---|---|---|
| `lead_headline` | 표지 헤드라인 | 자유 60 : 근거 40 | 한 줄 18~34자, `*강조구*` 마커 1개 허용 |
| `identity_claim` | 정체성 패널 | 자유 55 : 근거 45 | `CLAIM: …` / `BODY: …` 2줄 |
| `ai_highlights` ★ | AI PICK 3장(컬러 카드) | **자유 90 : 근거 10** | `HIGLIGHT: 제목 \| 본문 \| 한줄임팩트` × 3, 크리에이터마다 다른 3가지를 LLM이 직접 선정 |
| `audience_persona` | 오디언스 패널 | 자유 80 : 근거 20 | 1문단 3~4문장 |
| `content_read` | 성과 패널 | 근거 60 : 자유 40 | 협찬 vs 오가닉 해석 1~2문장 |
| `closing` | 마무리 패널 | 종합 | 2~3문장 + 캠페인 포맷 제안 |

공통 원칙: 숫자 재낭독 금지, 데이터 없는 사실 날조 금지, 마크다운 문법 금지(렌더러가 없어 기호가 그대로 노출됨 — 단 `*강조구*`만 Code가 형광펜 span으로 치환), "유기농" 대신 "오가닉/비협찬" 표기 통일.

Code 노드는 `creator_report_template_storyline.html`의 마커(`{{profile.username}}`, `{{INSIGHT:lead_headline}}`, `<!-- REPEAT: ... -->`, `<!-- OPTIONAL_BLOCK: ... -->`)를 리포트 JSON + 6개 LLM 텍스트로 치환해 최종 HTML을 조립한다.

## 버전 히스토리 메모

- 이 폴더는 **storyline v3(2단 구성)** 세대 산출물만 담았다. 이전 세대(9-node 대시보드형 워크플로우, `report_prompt.md` 등)는 구버전으로 제외.
- `rendered_storyline_full.html`은 최신 코드(`build_storyline_workflow.py`, `creator_report_storyline_workflow.yml`)와 같은 시점에 생성된 최종 렌더이며, 회귀 테스트가 "실 데이터 픽스처"로 지정한 `fixtures/jinjin.json`(실제 인스타 계정 데이터) 기반이다. `fixtures/seonho.json`도 같은 시기에 별도로 검증한 실제 계정 데이터 샘플이라 형식 참고용으로 함께 포함했다 — 다만 이 seonho 데이터로 렌더링된 결과물은 한 세대 이전(v2, growth-demo) 버전이었고 최신 v3 디자인으로는 재검증되지 않았다.

## 파일

| 경로 | 설명 |
|---|---|
| `creator_report_storyline_workflow.yml` | Dify에 임포트하는 최종 워크플로우 (Start → HTTP → 6개 LLM 병렬 → Code 조립 → End) |
| `insight_prompts_storyline.md` | 6개 슬롯의 성격·근거:자유 비율·출력 형식을 정리한 사람이 읽는 스펙 문서 |
| `build_storyline_workflow.py` | 위 YML을 생성하는 스크립트. 6개 슬롯의 **프롬프트 원문이 상수로 임베드**되어 있어 실제 지침 전문을 확인할 수 있는 핵심 참고 자료 |
| `creator_report_template_storyline.html` | Code 노드가 채우는 마커 템플릿 (`{{...}}`, `REPEAT`, `OPTIONAL_BLOCK`) |
| `rendered_storyline_full.html` | 최종 렌더링 결과물 예시 (실제 크리에이터 데이터 기반) |
| `fixtures/seonho.json` | 테스트에 쓴 실제 크리에이터 계정 데이터 샘플 (입력 JSON 형식 예시) |
