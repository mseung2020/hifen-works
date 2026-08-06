"""DB 접속 및 SQL 템플릿 렌더링 → CSV 저장."""
import csv
from pathlib import Path

import pymysql

from .config import Config, ROOT_DIR


def connect(db_cfg):
    return pymysql.connect(
        host=db_cfg.host,
        port=db_cfg.port,
        user=db_cfg.user,
        password=db_cfg.password,
        database=db_cfg.name,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.SSCursor,  # 대용량 row-level 쿼리 대비 스트리밍 커서
    )


def render_sql(template_name: str, cfg: Config, column_prefix: str = "") -> str:
    template_path = ROOT_DIR / "sql" / template_name
    template = template_path.read_text(encoding="utf-8")
    return template.format(
        start_date=cfg.start_date,
        end_date=cfg.end_date,
        start_date_ymd=cfg.start_date_ymd(),
        end_date_ymd=cfg.end_date_ymd(),
        brand_list=cfg.brand_list_sql(),
        exclude_clause=cfg.exclude_clause(column_prefix),
    )


def run_query_to_csv(conn, sql: str, csv_path: Path) -> int:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with conn.cursor() as cur:
        cur.execute(sql)
        columns = [d[0] for d in cur.description]
        row_count = 0
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            for row in cur:
                writer.writerow(["NULL" if v is None else v for v in row])
                row_count += 1
    return row_count


def fetch_brand_cost(conn, cfg: Config, csv_path: Path) -> int:
    sql = render_sql("brand_cost.sql.tmpl", cfg, column_prefix="")
    return run_query_to_csv(conn, sql, csv_path)


def fetch_brand_user(conn, cfg: Config, csv_path: Path) -> int:
    sql = render_sql("brand_user_cost.sql.tmpl", cfg, column_prefix="vt.")
    return run_query_to_csv(conn, sql, csv_path)
