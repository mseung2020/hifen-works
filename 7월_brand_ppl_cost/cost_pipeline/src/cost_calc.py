"""비용 산정.md 로직: 팔로워/구독자 구간 보간 + 조정비율 → 예상비용(원)."""
import csv
from pathlib import Path

from .config import Config


def _find_bucket(buckets, value: int):
    for b in buckets:
        if value < b.max:
            return b
    return buckets[-1]  # 최상위 구간 초과 → 최상위 구간에 clamp


def compute_cost(value, content_type: str, kind: str, cfg: Config):
    """value: 인스타 followers 또는 유튜브 subscribers. kind: 'instagram' | 'youtube'."""
    if value is None:
        return None

    bucket = _find_bucket(cfg.buckets, max(value, cfg.buckets[0].min))
    pos = (value - bucket.min) / (bucket.max - bucket.min)
    pos = max(0.0, min(1.0, pos))

    if kind == "instagram":
        base = bucket.instagram["feed"] if content_type == "피드" else bucket.instagram["reel"]
    else:
        base = bucket.youtube["shorts"] if content_type == "쇼츠" else bucket.youtube["ppl"]

    interpolated_10k = base[0] + pos * (base[1] - base[0])
    cost_10k = interpolated_10k * bucket.adjustment
    return round(cost_10k * 10000)


def add_estimated_cost(brand_user_csv: Path, brand_user_cost_csv: Path, cfg: Config):
    with open(brand_user_csv, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    header = rows[0]
    header_out = header + ["예상비용(원)"]
    idx = {name: i for i, name in enumerate(header)}

    out_rows = [header_out]
    for row in rows[1:]:
        if not row:
            continue
        platform = row[idx["platform"]]
        content_type = row[idx["content_type"]]

        if platform == "Instagram":
            followers_raw = row[idx["followers"]]
            followers = None if followers_raw in ("NULL", "") else int(followers_raw)
            cost = compute_cost(followers, content_type, "instagram", cfg)
        else:
            channel_cost_raw = row[idx["channel_cost"]]
            if channel_cost_raw not in ("NULL", ""):
                cost = int(channel_cost_raw)
            else:
                subs_raw = row[idx["subscribers"]]
                subs = None if subs_raw in ("NULL", "") else int(subs_raw)
                cost = compute_cost(subs, content_type, "youtube", cfg)

        out_rows.append(row + [str(cost) if cost is not None else ""])

    brand_user_cost_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(brand_user_cost_csv, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(out_rows)
