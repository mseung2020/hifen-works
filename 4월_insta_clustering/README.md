# 인스타 클러스터링 — 4분면 버블차트

인플루언서/포스트 라벨 데이터를 **클러스터링**하고, 클러스터별 성과 지표를 **4분면 버블차트**로 시각화하는 Flask 웹앱입니다. 어떤 트렌드 클러스터가 포스트는 많은데 반응이 적은지(혹은 그 반대인지)를 한눈에 보여줍니다. 이 폴더는 대규모 클러스터링 프로젝트의 **최종 결과물("실제 클러스터")**입니다.

- **분야:** 데이터 분석
- **결과물 형태:** Flask 웹앱 (Docker 배포 가능, 4분면 버블차트)
- **시각화:** 클러스터별 포스트 점유율 × DM/반응 효율을 좌표·버블 크기로 매핑

## 실행

```
pip install -r requirements.txt
python quadrant_cluster_app.py
```
또는 Docker:
```
docker build -t quadrant-cluster . && docker run -p 7860:7860 quadrant-cluster
```
> 앱이 사용하는 `real data_all2.csv`(클러스터 집계 데이터)가 포함되어 있어 별도 데이터 준비 없이 바로 실행됩니다.

## 구성

| 파일 | 설명 |
|---|---|
| `quadrant_cluster_app.py` | Flask 서버. `real data_all2.csv`를 로드해 클러스터 좌표·버블 데이터를 API로 제공 |
| `templates/quadrant.html` | 4분면 버블차트 UI |
| `config/stopwords.json`, `synonyms.json` | 키워드 정제용 불용어·동의어 사전 |
| `real data_all2.csv` | **앱 입력 데이터** (클러스터 단위 집계, 2,410행) — 포함 |
| `Dockerfile`, `requirements.txt` | 배포 설정 |
| `data/` | 원천 raw 데이터(959MB) 요약 + 샘플 ([DATA_SUMMARY.md](data/DATA_SUMMARY.md)) |

> 본 프로젝트는 다양한 클러스터링 버전(리스트형, 4분면 테스트, 불용어 제거 등)을 거쳤으며, 이 폴더는 그중 최종본만 담았습니다. 포스트 단위 원본(959MB)은 GitHub 용량 제한으로 제외하고 요약했습니다.
