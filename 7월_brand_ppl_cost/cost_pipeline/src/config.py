"""config.yaml + .env 를 읽어 파이프라인 전체에서 쓰는 설정 객체로 만든다."""
import os
from pathlib import Path
from dataclasses import dataclass

import yaml
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent


@dataclass
class DBConfig:
    host: str
    port: int
    user: str
    password: str
    name: str


@dataclass
class Brand:
    db_name: str
    display_name: str


@dataclass
class PriceBucket:
    min: int
    max: int
    adjustment: float
    instagram: dict  # {"feed": [lo, hi], "reel": [lo, hi]}
    youtube: dict     # {"ppl": [lo, hi], "shorts": [lo, hi]}


@dataclass
class Config:
    db: DBConfig
    period_label: str
    start_date: str
    end_date: str
    output_dir: Path
    brands: list
    exclude_keywords: list
    buckets: list

    def brand_list_sql(self) -> str:
        """SQL IN (...) 절에 넣을 브랜드명 리스트 (단일 소스 → 두 쿼리가 항상 같은 값을 씀)."""
        names = [b.db_name.replace("'", "''") for b in self.brands]
        return ", ".join(f"'{n}'" for n in names)

    def start_date_ymd(self) -> str:
        return self.start_date.split(" ")[0]

    def end_date_ymd(self) -> str:
        return self.end_date.split(" ")[0]

    def exclude_clause(self, column_prefix: str = "") -> str:
        """video_description 기반 제외 조건. column_prefix 예: 'vt.' """
        col = f"{column_prefix}video_description"
        parts = []
        for keywords in self.exclude_keywords:
            conds = " AND ".join(f"{col} LIKE '%{kw}%'" for kw in keywords)
            parts.append(f"({conds})")
        return " OR ".join(parts) if parts else "1=0"


def load_config(config_path: str = None) -> Config:
    load_dotenv(ROOT_DIR / ".env")

    config_path = Path(config_path) if config_path else ROOT_DIR / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    db = DBConfig(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", 3306)),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PW"],
        name=os.environ["DB_NAME"],
    )

    brands = [Brand(**b) for b in raw["brands"]]
    buckets = [PriceBucket(**b) for b in raw["pricing"]["buckets"]]
    buckets.sort(key=lambda b: b.min)

    return Config(
        db=db,
        period_label=raw["period"]["label"],
        start_date=raw["period"]["start_date"],
        end_date=raw["period"]["end_date"],
        output_dir=ROOT_DIR / raw.get("output_dir", "output"),
        brands=brands,
        exclude_keywords=raw.get("exclude_description_keywords", []),
        buckets=buckets,
    )
