"""brand_cost.csv(집계) + brand_user_cost.csv(개별 비용) → brand_ppl_summary.csv."""
import csv
from collections import defaultdict
from pathlib import Path

from .config import Config

SUMMARY_HEADER = [
    "brand", "인스타 광고 수", "유튜브 광고 수",
    "인스타 조회수", "유튜브 조회수", "인스타 비용", "유튜브 비용",
]


def build_summary(brand_cost_csv: Path, brand_user_cost_csv: Path, summary_csv: Path, cfg: Config):
    cost = defaultdict(int)
    with open(brand_user_cost_csv, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            c = row["예상비용(원)"]
            if c:
                cost[(row["brand"], row["platform"])] += int(c)

    stats = defaultdict(lambda: {"count": 0, "views": 0})
    with open(brand_cost_csv, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            stats[(row["brand"], row["platform"])] = {
                "count": int(row["ppl_count"]),
                "views": int(row["total_views"]),
            }

    rows_out = [SUMMARY_HEADER]
    for brand in cfg.brands:
        ig = stats.get((brand.db_name, "Instagram"), {"count": 0, "views": 0})
        yt = stats.get((brand.db_name, "YouTube"), {"count": 0, "views": 0})
        ig_cost = cost.get((brand.db_name, "Instagram"), 0)
        yt_cost = cost.get((brand.db_name, "YouTube"), 0)
        rows_out.append([
            brand.display_name, ig["count"], yt["count"],
            ig["views"], yt["views"], ig_cost, yt_cost,
        ])

    summary_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_csv, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows_out)
