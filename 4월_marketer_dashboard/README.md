# 마케터 맞춤 컨설팅 대시보드

샘플 뷰티 브랜드를 대상으로 만든 **마케터용 컨설팅 대시보드**입니다. DB의 여러 테이블에서 데이터를 모아 경쟁사 분석, 크리에이터 분석, 올리브영 순위·평점, 오디언스(데모그래픽) 등을 한 화면에서 보여줍니다. `data/` 하위에 브랜드 폴더를 추가하면 자동으로 브랜드가 목록에 잡히는 구조입니다.

- **분야:** 데이터 분석
- **결과물 형태:** Flask + Chart.js 웹 대시보드
- **수록 브랜드(샘플):** LG생활건강, 아누아, 릴리바이레드, 넘버즈인, 토리든

## 실행

```
pip install -r requirements.txt
# (선택) 관리자 로그인 자격증명 설정
export DASHBOARD_ADMIN_ID=admin DASHBOARD_ADMIN_PW=원하는비밀번호 DASHBOARD_SECRET_KEY=임의문자열
python app.py        # → http://localhost:5000
```
> `data/` 하위 브랜드 폴더가 모두 포함되어 있어 바로 실행됩니다. 자세한 배포 방법은 [`실행방법.md`](실행방법.md) 참고.

## 구성

| 경로 | 설명 |
|---|---|
| `app.py` | Flask 서버. `data/` 하위 폴더(각 `config.json` 보유)를 스캔해 브랜드 자동 탐지, 브랜드별 대시보드 라우팅 |
| `templates/` | `index.html`(대시보드), `admin.html`(관리), `login.html` |
| `static/` | 정적 자산 (Chart.js 등) |
| `data/<브랜드>/` | 브랜드별 참조 데이터 — base, 경쟁사 영상, 데모그래픽, 올리브영 점수·상품·순위, 유튜버 정보·통계, config.json, 로고 |
| `queries_*.sql` | 데이터 추출용 SQL (실행용 / 새브랜드 / LG생활건강) |
| `table_scheme` | 참조한 DB 테이블 스키마 |
| `프로젝트_구조도.md`, `실행방법.md` | 구조 설명·실행/배포 가이드 |

## 데이터
브랜드별 참조 데이터(약 44MB)가 모두 포함되어 별도 준비 없이 실행됩니다. 각 브랜드 폴더는 약 10종의 CSV(경쟁사·크리에이터·올리브영·데모그래픽 등)로 구성됩니다.

> 보안: 기존 하드코딩되어 있던 관리자 자격증명·secret key는 환경변수(`DASHBOARD_ADMIN_ID/PW`, `DASHBOARD_SECRET_KEY`)로 분리했습니다. 미설정 시 기본값(`admin`/`changeme`)으로 동작합니다.
