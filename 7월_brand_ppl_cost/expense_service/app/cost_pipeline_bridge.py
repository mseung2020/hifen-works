"""cost_pipeline/src 를 그대로 재사용하기 위한 연결 모듈.

cost_pipeline 은 원래 CLI(config.yaml 고정) 용으로 만든 패키지인데, 여기서는 그 안의
DB 접속 / SQL 렌더링 / 비용 계산 / 요약 / xlsx 생성 로직을 그대로 가져다 쓰고,
기간·브랜드·단가만 요청(request)마다 다르게 갈아끼운다. config.yaml 자체는 건드리지 않는다.
"""
import sys
from dataclasses import replace
from pathlib import Path

COST_PIPELINE_DIR = Path(__file__).resolve().parent.parent.parent / "cost_pipeline"
if str(COST_PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(COST_PIPELINE_DIR))

from src.config import load_config, Config, Brand, PriceBucket  # noqa: E402
from src import db, cost_calc, aggregate, xlsx_export  # noqa: E402

_base_config_cache = None


def get_base_config() -> Config:
    """DB 접속정보 + config.yaml 의 기본값(default 단가표, 기본 브랜드 리스트)을 읽어온다.
    요청마다 다시 파일을 읽지 않도록 캐시."""
    global _base_config_cache
    if _base_config_cache is None:
        _base_config_cache = load_config(str(COST_PIPELINE_DIR / "config.yaml"))
    return _base_config_cache


def build_run_config(*, run_id: str, start_date: str, end_date: str,
                      brands: list, buckets: list, exclude_keywords: list,
                      output_dir: Path) -> Config:
    """요청(request) 값으로 이번 실행 전용 Config 를 만든다. config.yaml 은 전혀 수정하지 않는다."""
    base = get_base_config()
    return replace(
        base,
        period_label=run_id,
        start_date=start_date,
        end_date=end_date,
        output_dir=output_dir,
        brands=[Brand(db_name=b["db_name"], display_name=b["display_name"]) for b in brands],
        buckets=[
            PriceBucket(
                min=b["min"], max=b["max"], adjustment=b["adjustment"],
                instagram=b["instagram"], youtube=b["youtube"],
            )
            for b in buckets
        ],
        exclude_keywords=exclude_keywords,
    )
