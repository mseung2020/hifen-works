import uuid
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import brand_catalog
from .cost_pipeline_bridge import get_base_config, build_run_config, db, cost_calc, aggregate, xlsx_export

RUNS_DIR = Path(__file__).resolve().parent.parent / "runs"
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(title="브랜드 PPL 예상지출 서비스")


class BrandIn(BaseModel):
    db_name: str
    display_name: str


class BucketIn(BaseModel):
    min: int
    max: int
    adjustment: float
    instagram: dict
    youtube: dict


class GenerateRequest(BaseModel):
    label: Optional[str] = None
    start_date: str          # "2026-07-01 00:00:00"
    end_date: str             # "2026-08-01 00:00:00"
    brands: List[BrandIn]
    buckets: List[BucketIn]
    exclude_keywords: Optional[List[List[str]]] = None


@app.get("/api/defaults")
def get_defaults():
    cfg = get_base_config()
    return {
        "start_date": cfg.start_date,
        "end_date": cfg.end_date,
        "exclude_keywords": cfg.exclude_keywords,
        "buckets": [
            {"min": b.min, "max": b.max, "adjustment": b.adjustment,
             "instagram": b.instagram, "youtube": b.youtube}
            for b in cfg.buckets
        ],
        "brands": [{"db_name": b.db_name, "display_name": b.display_name} for b in cfg.brands],
    }


@app.get("/api/brand-catalog")
def get_brand_catalog():
    brands = brand_catalog.list_brands()
    topics = sorted({b["topic"] for b in brands})
    return {"topics": topics, "brands": brands}


@app.post("/api/generate")
def generate(req: GenerateRequest):
    if not req.brands:
        raise HTTPException(400, "브랜드를 하나 이상 선택하세요.")
    if not req.buckets:
        raise HTTPException(400, "단가 구간(buckets)이 비어 있습니다.")

    run_id = f"{req.label or 'run'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    out_dir = RUNS_DIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    base = get_base_config()
    cfg = build_run_config(
        run_id=run_id,
        start_date=req.start_date,
        end_date=req.end_date,
        brands=[b.model_dump() for b in req.brands],
        buckets=[b.model_dump() for b in req.buckets],
        exclude_keywords=req.exclude_keywords if req.exclude_keywords is not None else base.exclude_keywords,
        output_dir=RUNS_DIR,
    )

    # 이번 실행에 쓴 설정을 기록 (config.yaml 은 건드리지 않음)
    (out_dir / "request.json").write_text(req.model_dump_json(indent=2), encoding="utf-8")

    brand_cost_csv = out_dir / "brand_cost.csv"
    brand_user_csv = out_dir / "brand_user.csv"
    brand_user_cost_csv = out_dir / "brand_user_cost.csv"
    summary_csv = out_dir / "brand_ppl_summary.csv"
    xlsx_path = out_dir / f"브랜드별_예상지출_{run_id}.xlsx"

    try:
        conn = db.connect(cfg.db)
        try:
            db.fetch_brand_cost(conn, cfg, brand_cost_csv)
            db.fetch_brand_user(conn, cfg, brand_user_csv)
        finally:
            conn.close()

        cost_calc.add_estimated_cost(brand_user_csv, brand_user_cost_csv, cfg)
        aggregate.build_summary(brand_cost_csv, brand_user_cost_csv, summary_csv, cfg)
        xlsx_export.build_xlsx(summary_csv, xlsx_path)
    except Exception as e:
        shutil.rmtree(out_dir, ignore_errors=True)
        raise HTTPException(500, f"생성 실패: {e}")

    import csv
    with open(summary_csv, newline="", encoding="utf-8") as f:
        summary_rows = list(csv.DictReader(f))

    files = {
        "brand_cost_csv": brand_cost_csv.name,
        "brand_user_csv": brand_user_csv.name,
        "brand_user_cost_csv": brand_user_cost_csv.name,
        "summary_csv": summary_csv.name,
        "xlsx": xlsx_path.name,
    }
    return {
        "run_id": run_id,
        "summary": summary_rows,
        "download_base": f"/api/runs/{run_id}/download",
        "files": files,
    }


@app.get("/api/runs/{run_id}/download/{filename}")
def download(run_id: str, filename: str):
    if "/" in filename or "\\" in filename or ".." in filename or "/" in run_id or ".." in run_id:
        raise HTTPException(400, "잘못된 경로입니다.")
    path = (RUNS_DIR / run_id / filename).resolve()
    if RUNS_DIR.resolve() not in path.parents or not path.is_file():
        raise HTTPException(404, "파일을 찾을 수 없습니다.")
    return FileResponse(path, filename=filename)


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
