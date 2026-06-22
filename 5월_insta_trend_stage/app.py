from flask import Flask, render_template, jsonify
import requests
import json
import os
from datetime import date
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# 내부 API 엔드포인트·토큰은 환경변수로 주입 (레포에는 비밀값 미포함)
API_URL = os.environ.get("TREND_API_URL", "http://localhost:8000/instagram-dm-send-analysis/cluster-cumulative-daily-stats")
TOKEN = os.environ.get("TREND_API_TOKEN", "")

CATEGORIES = [
    "맛집/푸드",
    "뷰티(메이크업/헤어)",
    "엔터/아이돌/연예",
    "운동/피트니스",
    "육아/키즈",
    "카페/핫플",
    "패션/룩",
]

CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")
os.makedirs(CACHE_DIR, exist_ok=True)


def cache_path(category_name):
    today = date.today().isoformat()
    safe_name = category_name.replace("/", "_").replace("(", "_").replace(")", "_")
    return os.path.join(CACHE_DIR, f"{safe_name}_{today}.json")


def fetch_cluster(cluster_id):
    headers = {"Authorization": f"Bearer {TOKEN}"}
    try:
        resp = requests.post(
            API_URL,
            json={"cluster_id": cluster_id},
            headers=headers,
            timeout=15,
        )
        return resp.json()
    except Exception as e:
        return {"error": str(e), "cluster_id": cluster_id}


@app.route("/")
def index():
    return render_template("index.html", categories=CATEGORIES)


@app.route("/api/category/<path:category_name>")
def get_category_data(category_name):
    path = cache_path(category_name)

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return jsonify(json.load(f))

    cluster_ids = [f"{category_name}_{i}" for i in range(1, 31)]
    with ThreadPoolExecutor(max_workers=15) as executor:
        results = list(executor.map(fetch_cluster, cluster_ids))

    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False)

    return jsonify(results)


@app.route("/api/clear-cache", methods=["POST"])
def clear_cache():
    removed = 0
    for fname in os.listdir(CACHE_DIR):
        if fname.endswith(".json"):
            os.remove(os.path.join(CACHE_DIR, fname))
            removed += 1
    return jsonify({"removed": removed})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
