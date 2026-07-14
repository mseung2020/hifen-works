# -*- coding: utf-8 -*-
"""아비브 제품 랭킹/광고 대시보드 (Flask)
실행:
    pip install flask
    python3 prepare_data.py      # static/abib_data.json 생성 (최초 1회 또는 데이터 갱신 시)
    python3 app.py               # http://127.0.0.1:5001
"""
import json, os
from flask import Flask, jsonify, render_template, abort

app = Flask(__name__)
DATA_PATH = os.path.join(app.static_folder, "abib_data.json")

def load_data():
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/meta")
def meta():
    return jsonify({"range": load_data().get("range", {})})

@app.route("/api/products")
def products():
    data = load_data()
    return jsonify([
        {"product_id": p["product_id"], "product": p["product"], "best_rank": p["best_rank"]}
        for p in data["products"]
    ])

@app.route("/api/product/<pid>")
def product(pid):
    data = load_data()
    for p in data["products"]:
        if p["product_id"] == pid:
            return jsonify(p)
    abort(404)

if __name__ == "__main__":
    app.run(debug=True, port=5001)
