# -*- coding: utf-8 -*-
"""아비브 대시보드용 데이터 가공: 랭킹 CSV + 유튜브/인스타 CSV -> static/abib_data.json
- 랭킹: 2026 일별 등수(카테고리별)
- 노출지표: 2026 일별 건수 (총/유튜브 무가·유가/인스타 무가·유가)
"""
import csv, json, os, collections

BASE = os.path.dirname(os.path.abspath(__file__))
RANK_CSV = os.path.join(BASE, "아비브_올리브영_일간랭킹.csv")
YT_CSV   = os.path.join(BASE, "아비브 유튜브.csv")
IG_CSV   = os.path.join(BASE, "아비브 인스타.csv")
OUT_DIR  = os.path.join(BASE, "static")
OUT_JSON = os.path.join(OUT_DIR, "abib_data.json")
YEAR = "2026"
METRIC_KEYS = ["total","yt_total","yt_organic","yt_paid","ig_total","ig_organic","ig_paid"]

def is_paid(v):
    return str(v).strip() in ("1", "1.0", "True", "true")

# ---------- 1) 랭킹 시계열 (2026) ----------
rank = collections.defaultdict(lambda: {"product": "", "cats": collections.defaultdict(dict)})
with open(RANK_CSV, encoding="utf-8-sig", newline="") as f:
    for row in csv.DictReader(f):
        if not row["date"].startswith(YEAR):
            continue
        pid = row["product_id"].strip()
        try:
            rk = int(row["rank"])
        except (ValueError, TypeError):
            continue
        rec = rank[pid]; rec["product"] = row["product"].strip()
        rcat = row["rank_category"].strip(); d = row["date"]
        prev = rec["cats"][rcat].get(d)
        rec["cats"][rcat][d] = rk if prev is None else min(prev, rk)

# ---------- 2) 유튜브/인스타 일별 카운트 (2026) ----------
def count_daily(path, date_col, ids_col):
    daily = collections.defaultdict(lambda: collections.defaultdict(lambda: {"t":0,"p":0,"o":0}))
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            dt = (row.get(date_col) or "").strip()
            if not dt.startswith(YEAR):
                continue
            ids = (row.get(ids_col) or "").strip()
            if not ids or ids == "NULL":
                continue
            day = dt[:10]
            paid = is_paid(row.get("product_ppl"))
            for pid in {x.strip() for x in ids.split(",") if x.strip()}:
                cell = daily[pid][day]
                cell["t"] += 1
                cell["p" if paid else "o"] += 1
    return daily

yt_daily = count_daily(YT_CSV, "publishDate", "featured_product_ids")
ig_daily = count_daily(IG_CSV, "publish_date", "abib_product_ids")

# ---------- 3) 병합 (랭킹 보유 제품 기준) ----------
products = []
for pid, rec in rank.items():
    best = min(min(dd.values()) for dd in rec["cats"].values())
    timeseries = {cat: [{"x": d, "y": rk} for d, rk in sorted(dd.items())]
                  for cat, dd in rec["cats"].items()}

    yd, idd = yt_daily.get(pid, {}), ig_daily.get(pid, {})
    days = sorted(set(yd) | set(idd))
    per_day = {}
    for d in days:
        y = yd.get(d, {"t":0,"p":0,"o":0}); i = idd.get(d, {"t":0,"p":0,"o":0})
        per_day[d] = {
            "total": y["t"]+i["t"],
            "yt_total": y["t"], "yt_organic": y["o"], "yt_paid": y["p"],
            "ig_total": i["t"], "ig_organic": i["o"], "ig_paid": i["p"],
        }
    metrics_daily = {k: [{"x": d, "y": per_day[d][k]} for d in days if per_day[d][k] > 0]
                     for k in METRIC_KEYS}
    metrics_sum = {k: sum(per_day[d][k] for d in days) for k in METRIC_KEYS}

    products.append({
        "product_id": pid, "product": rec["product"], "best_rank": best,
        "timeseries": timeseries, "metrics": metrics_sum, "metrics_daily": metrics_daily,
    })

products.sort(key=lambda p: (p["best_rank"], p["product"]))

# 전역 날짜 범위 (모든 제품 공통 x축용)
all_dates = []
for p in products:
    for arr in p["timeseries"].values():
        all_dates += [pt["x"] for pt in arr]
    for arr in p["metrics_daily"].values():
        all_dates += [pt["x"] for pt in arr]
rng = {"min": min(all_dates), "max": max(all_dates)} if all_dates \
      else {"min": YEAR + "-01-01", "max": YEAR + "-06-30"}

os.makedirs(OUT_DIR, exist_ok=True)
with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump({"products": products, "range": rng}, f, ensure_ascii=False)

# ---------- 진단 ----------
print(f"랭킹(2026) 보유 제품: {len(products)}  | 전역 범위: {rng['min']} ~ {rng['max']}")
p0 = products[0]; md = p0["metrics_daily"]
print(f"예시 1위: {p0['product'][:26]} | 합계 {p0['metrics']}")
print(f"  total 일별 포인트 수: {len(md['total'])}  (예: {md['total'][:3]})")
print(f"  rank '전체' 포인트 수: {len(p0['timeseries'].get('전체',[]))}")
print(f"-> 저장: {OUT_JSON}")
