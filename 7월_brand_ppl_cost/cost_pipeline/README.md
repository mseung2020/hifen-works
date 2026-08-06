# cost_pipeline

브랜드 PPL 비용 리포트를 한 줄 명령으로 만드는 파이프라인.

DB 조회(brand_cost / brand_user_cost) → 비용 산정.md 로직으로 예상비용 계산 →
브랜드별 요약(brand_ppl_summary.csv) → 엑셀 리포트(브랜드별_예상지출_*.xlsx) 까지 자동 실행.

## 사용법

```bash
./run.sh
```

최초 실행 시 `.venv`를 만들고 `requirements.txt`를 설치한 뒤 파이프라인을 돌립니다.
결과물은 `output/{period.label}/` 아래에 생성됩니다:

- `brand_cost.csv` — 브랜드×플랫폼별 PPL 수 / 조회수 (DB raw)
- `brand_user.csv` — 게시물/영상 단위 raw 데이터 (팔로워/구독자/채널코스트 포함)
- `brand_user_cost.csv` — 위 파일에 예상비용(원) 컬럼 추가
- `brand_ppl_summary.csv` — 브랜드별 최종 요약
- `브랜드별_예상지출_{label}.xlsx` — 최종 엑셀 리포트

이미 DB에서 받아둔 raw csv로 비용 계산 로직만 다시 돌리고 싶으면:

```bash
./run.sh --skip-db
```

## 설정 바꾸기 (`config.yaml`)

이 파일 하나만 고치면 됩니다.

- `period` — 수집 기간(`start_date`/`end_date`)과 출력 폴더명(`label`)
- `brands` — 집계할 브랜드 목록. `db_name`은 DB에 저장된 실제 문자열(WHERE IN 매칭용),
  `display_name`은 리포트에 표시할 이름. **두 SQL 쿼리가 항상 이 리스트 하나만 참조**하므로
  브랜드명이 쿼리마다 다르게 적혀서 데이터가 누락되는 사고(예: '콜게이트' vs '콜게이트 코리아')가
  구조적으로 안 생깁니다.
- `pricing.buckets` — `비용 산정.md`의 팔로워/구독자 구간별 단가(만원)와 조정비율(절감율).
  구간을 추가/삭제하거나 단가·조정비율을 바꾸면 다음 실행부터 바로 반영됩니다.

## DB 접속 정보 (`.env`)

`DB_HOST`, `DB_USER`, `DB_PW`, `DB_NAME`, `DB_PORT`를 채워 넣으세요. `.env`는 `.gitignore`에
들어 있어 커밋되지 않습니다. `.env.example`을 참고해서 새 환경에서 복사해 쓰면 됩니다.

## 폴더 구조

```
cost_pipeline/
├── config.yaml          # 기간 / 브랜드 / 단가 / 조정비율 설정
├── .env                 # DB 접속 정보 (git에 안 올라감)
├── run.py / run.sh       # 진입점
├── sql/                  # brand_list를 config에서 채워 넣는 SQL 템플릿
├── src/
│   ├── config.py         # config.yaml + .env 로딩
│   ├── db.py             # DB 접속, SQL 렌더링, CSV 저장
│   ├── cost_calc.py       # 비용 산정.md 보간 + 조정비율 로직
│   ├── aggregate.py       # brand_ppl_summary.csv 생성
│   ├── xlsx_export.py     # 엑셀 리포트 생성 (브랜드 수에 따라 레이아웃 자동 생성)
│   └── pipeline.py        # 위 단계들을 순서대로 실행
└── output/{label}/        # 실행 결과물
```

## 다음 달 리포트를 새로 뽑고 싶다면

`config.yaml`의 `period`만 바꾸고 `./run.sh` 한 번이면 됩니다.
