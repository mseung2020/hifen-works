from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
from collections import defaultdict

app = Flask(__name__)
CORS(app)

CSV_PATH = "total_creator_analysis.csv"

# CSV 로드 및 유저별 데이터 인덱싱
print("CSV 로딩 중...")
df = pd.read_csv(CSV_PATH, dtype=str).fillna("")
print(f"총 {len(df)}행 로드 완료, 유저 수: {df['user_id'].nunique()}")

FIELDS = ["format", "persona", "behavior", "topic", "mood"]
FIELD_LABELS = {
    "format": "대표유형",
    "persona": "주인공",
    "behavior": "유도행동",
    "topic": "분야/주제",
    "mood": "무드/톤",
}


def get_user_field_sets(user_id: str):
    rows = df[df["user_id"] == user_id]
    if rows.empty:
        return None
    return {field: set(rows[field].unique()) - {""} for field in FIELDS}


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/similar_compare")
def similar_compare_page():
    return send_from_directory(".", "similar_compare.html")


@app.route("/similar_single")
def similar_single_page():
    return send_from_directory(".", "similar_single.html")


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(".", filename)


@app.route("/api/compare", methods=["POST"])
def compare():
    data = request.json
    ref_id = (data.get("ref_id") or "").strip()
    compare_ids = [x.strip() for x in (data.get("compare_ids") or "").split(",") if x.strip()]

    if not ref_id:
        return jsonify({"error": "기준 대상 ID를 입력해주세요."}), 400
    if not compare_ids:
        return jsonify({"error": "비교 대상 ID를 입력해주세요."}), 400

    ref_sets = get_user_field_sets(ref_id)
    if ref_sets is None:
        return jsonify({"error": f"기준 대상 '{ref_id}'를 찾을 수 없습니다."}), 404

    results = []
    for cmp_id in compare_ids:
        cmp_sets = get_user_field_sets(cmp_id)
        if cmp_sets is None:
            results.append({"id": cmp_id, "found": False})
            continue

        field_results = {}
        matched_count = 0
        for field in FIELDS:
            intersection = ref_sets[field] & cmp_sets[field]
            matched = len(intersection) > 0
            if matched:
                matched_count += 1
            field_results[field] = {
                "label": FIELD_LABELS[field],
                "matched": matched,
                "ref_values": sorted(ref_sets[field]),
                "cmp_values": sorted(cmp_sets[field]),
                "common": sorted(intersection),
            }

        results.append({
            "id": cmp_id,
            "found": True,
            "score": matched_count,
            "total": len(FIELDS),
            "fields": field_results,
        })

    ref_info = {field: sorted(ref_sets[field]) for field in FIELDS}
    return jsonify({"ref_id": ref_id, "ref_info": ref_info, "results": results})


@app.route("/api/search_user", methods=["GET"])
def search_user():
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify([])
    matches = df[df["user_id"].str.contains(q, case=False, na=False)]["user_id"].unique().tolist()
    return jsonify(matches[:20])


if __name__ == "__main__":
    app.run(debug=True, port=5050)
