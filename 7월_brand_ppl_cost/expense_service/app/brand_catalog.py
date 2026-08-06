"""brand_logo 테이블에서 브랜드 목록/카테고리(topic)를 읽어 검색용 카탈로그로 제공."""
import pymysql

from .cost_pipeline_bridge import get_base_config


def _connect():
    cfg = get_base_config()
    return pymysql.connect(
        host=cfg.db.host,
        port=cfg.db.port,
        user=cfg.db.user,
        password=cfg.db.password,
        database=cfg.db.name,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


def list_brands():
    sql = """
        SELECT brand_logo_id, brand_name_kr, brand_name_en,
               COALESCE(NULLIF(TRIM(topic), ''), '미분류') AS topic,
               country_code, brand_videos
        FROM brand_logo
        WHERE skip = 0
        ORDER BY topic, brand_name_kr
    """
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()
    finally:
        conn.close()


def list_topics():
    brands = list_brands()
    topics = sorted({b["topic"] for b in brands})
    return topics
