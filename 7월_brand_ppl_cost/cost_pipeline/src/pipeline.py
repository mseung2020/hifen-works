"""전체 파이프라인: DB 조회 → raw CSV → 비용 계산 → 요약 → xlsx."""
import sys
from pathlib import Path

from . import db
from . import cost_calc
from . import aggregate
from . import xlsx_export
from .config import load_config


def run(config_path: str = None, skip_db: bool = False):
    cfg = load_config(config_path)
    out_dir = cfg.output_dir / cfg.period_label
    out_dir.mkdir(parents=True, exist_ok=True)

    brand_cost_csv = out_dir / "brand_cost.csv"
    brand_user_csv = out_dir / "brand_user.csv"
    brand_user_cost_csv = out_dir / "brand_user_cost.csv"
    summary_csv = out_dir / "brand_ppl_summary.csv"
    xlsx_path = out_dir / f"브랜드별_예상지출_{cfg.period_label}.xlsx"

    if skip_db:
        print(f"[1/4] DB 조회 스킵 (기존 raw csv 재사용: {out_dir})")
        if not brand_cost_csv.exists() or not brand_user_csv.exists():
            print("  -> raw csv가 없습니다. --skip-db 없이 다시 실행하세요.", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"[1/4] DB 조회 중... ({cfg.period_label}: {cfg.start_date} ~ {cfg.end_date})")
        conn = db.connect(cfg.db)
        try:
            n1 = db.fetch_brand_cost(conn, cfg, brand_cost_csv)
            print(f"  -> brand_cost.csv ({n1} rows)")
            n2 = db.fetch_brand_user(conn, cfg, brand_user_csv)
            print(f"  -> brand_user.csv ({n2} rows)")
        finally:
            conn.close()

    print("[2/4] 비용 산정.md 로직으로 예상비용 계산 중...")
    cost_calc.add_estimated_cost(brand_user_csv, brand_user_cost_csv, cfg)
    print(f"  -> brand_user_cost.csv")

    print("[3/4] 브랜드별 요약 생성 중...")
    aggregate.build_summary(brand_cost_csv, brand_user_cost_csv, summary_csv, cfg)
    print(f"  -> brand_ppl_summary.csv")

    print("[4/4] 엑셀 리포트 생성 중...")
    xlsx_export.build_xlsx(summary_csv, xlsx_path)
    print(f"  -> {xlsx_path}")

    print(f"\n완료: {out_dir}")


if __name__ == "__main__":
    run()
