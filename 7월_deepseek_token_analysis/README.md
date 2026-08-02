# DeepSeek 모델 토큰·비용 분석

인스타 게시물 분류(광고 브랜드 태깅)에 쓰던 **gpt-4o-mini를 DeepSeek(`deepseek-v4-flash`)으로 교체할 수 있는지** 검증하기 위해, 동일 분류 프롬프트로 실제 포스트 100건을 호출해 **prompt cache hit/miss 토큰, 입출력 토큰, 건당·평균 비용(USD)**을 측정한 실험입니다. DB에는 저장하지 않는 임시 테스트 파이프라인으로, 기존 인스타그램 포스트 분류기 백엔드에서 이 스크립트만 분리해 실행했습니다.

- **분야:** 백엔드 / 코드
- **분석 대상:** DeepSeek Chat Completions API (`deepseek-v4-flash`) 호출 결과 usage 필드
- **측정값:** 입력/출력 토큰, prompt cache hit/miss 토큰, reasoning 토큰 여부, 건별·평균·총 비용(USD)

## 측정 방법

1. 기존 DB의 미분석 포스트를 `PostRepository`로 조회 (재사용 목적, `exclude_analyzed=False`로 제약 없이 넉넉하게 조회)
2. gpt-4o-mini에 쓰던 것과 동일한 분류 프롬프트(`top-level-classification.txt`)를 시스템 프롬프트로 사용해 DeepSeek에 그대로 호출
3. `thinking: {"type": "disabled"}`을 `extra_body`로 요청(모델이 실제로 지원하는지는 응답의 `reasoning_content`/`reasoning_tokens` 존재 여부로 직접 확인)
4. 응답 `usage`에서 `prompt_tokens` / `completion_tokens` / `prompt_cache_hit_tokens` / `prompt_cache_miss_tokens`를 추출
5. 1M 토큰당 단가(cache hit input $0.0028 / cache miss input $0.14 / output $0.28 — 코드에 하드코딩된 추정 단가)로 건별 비용을 계산, 100건 평균·합계를 `deepseek_cache_result_v2.json`에 저장

## 측정 결과 요약 (100건, 전건 성공)

| 항목 | 값 |
|---|---|
| 모델 | `deepseek-v4-flash` |
| 성공/실패 | 100 / 0 |
| 평균 입력 토큰 | 2,157.67 |
| 평균 출력 토큰 | 460.6 |
| 평균 전체 토큰 | 2,618.27 |
| 평균 prompt cache **hit** 토큰 | 1,927.68 |
| 평균 prompt cache **miss** 토큰 | 229.99 |
| reasoning 토큰 발생 여부 | 없음 (`reasoning_content_seen_in_any_call: false`) |
| 평균 비용/건 | $0.0001666 |
| 100건 총 비용 | $0.01666 |

같은 시스템 프롬프트를 반복 호출한 덕에 입력 토큰의 **약 89%가 캐시 히트**(1,927.68 / 2,157.67)로 처리되어, 매 건 프롬프트를 새로 채우는 것보다 비용이 크게 줄었다. reasoning 토큰이 관측되지 않아 `thinking` 비활성화 요청이 의도대로 반영된 것으로 보인다.

## 파일

| 파일 | 설명 |
|---|---|
| `deepseek_cache_test.py` | DeepSeek 호출 + 캐시 hit/miss 토큰·비용 측정 스크립트 (DB 미저장, `DEEPSEEK_API_KEY`는 환경변수에서 로드) |
| `deepseek_cache_result_v2.json` | 100건 측정 결과 — 요약 통계 + 건별 원시 레코드 |

> 원본은 인스타그램 포스트 분류기 백엔드 레포 전체 클론에서 나왔지만, 이 레포에는 시크릿(.env)·DB 연동 코드를 포함한 백엔드 전체가 아니라 이 실험에 쓴 스크립트와 결과 JSON만 선별해 포함했습니다.
