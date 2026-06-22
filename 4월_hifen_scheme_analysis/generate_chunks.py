"""
site_data.json → Dify Knowledge Base 업로드용 마크다운 청크 생성기
산출물:
  chunks/tables.md     - 테이블 517개
  chunks/endpoints.md  - 엔드포인트 636개
  chunks/apps.md       - 앱 28개 요약
  chunks/edges.md      - 테이블·서비스 관계 그래프
"""

import json
import os
from pathlib import Path

SRC = Path(__file__).parent / "core_materials" / "site_data.pretty.json"
OUT = Path(__file__).parent / "chunks"
OUT.mkdir(exist_ok=True)

with open(SRC, encoding="utf-8") as f:
    data = json.load(f)

# ── 1. 테이블 청크 ──────────────────────────────────────────
lines = ["# 하이픈 테이블 목록\n"]
for name, t in data["tables"].items():
    cols = t.get("columns", [])
    col_lines = []
    for c in cols:
        key_tag = f" [{c['key']}]" if c.get("key") else ""
        comment = f" — {c['comment']}" if c.get("comment") else ""
        col_lines.append(f"  - `{c['name']}` ({c['type']}){key_tag}{comment}")

    lines.append(f"## {name}")
    lines.append(f"- **사용여부**: {t.get('usage', '')} / {t.get('boosted_usage', '')}")
    lines.append(f"- **신뢰도**: {t.get('confidence', '')} | **서브카테고리**: {t.get('subcategory', '')}")
    lines.append(f"- **도메인 접두사**: {t.get('domain_prefix', '')}")
    if t.get("description"):
        lines.append(f"- **설명**: {t['description']}")
    if t.get("note"):
        lines.append(f"- **노트**: {t['note']}")
    lines.append(f"- **직접 참조 수**: {t.get('direct_hits', 0)} | **간접**: {t.get('indirect_hits', 0)} | **언급**: {t.get('mention_hits', 0)}")
    if col_lines:
        lines.append("- **컬럼**:")
        lines.extend(col_lines)
    lines.append("")

(OUT / "tables.md").write_text("\n".join(lines), encoding="utf-8")
print(f"tables.md 생성 완료 — {len(data['tables'])}개 테이블")

# ── 2. 엔드포인트 청크 ─────────────────────────────────────
lines = ["# 하이픈 엔드포인트 목록\n"]
for ep in data["endpoints"]:
    methods = ", ".join(ep.get("http_methods", []))
    tables = ", ".join(f"`{t}`" for t in ep.get("tables_touched", []))
    evidence = ", ".join(ep.get("evidence_files", [])[:3])

    lines.append(f"## [{methods}] {ep.get('url_path', '')}")
    lines.append(f"- **앱**: {ep.get('app', '')}")
    lines.append(f"- **사용여부**: {ep.get('usage', '')} | **신뢰도**: {ep.get('confidence', '')}")
    lines.append(f"- **View**: {ep.get('view_ref', '')} ({ep.get('view_kind', '')}) — `{ep.get('view_file', '')}`")
    if tables:
        lines.append(f"- **연관 테이블**: {tables}")
    if ep.get("frontend_hits"):
        lines.append(f"- **프론트엔드 호출 수**: {ep['frontend_hits']}")
    if evidence:
        lines.append(f"- **근거 파일**: {evidence}")
    lines.append("")

(OUT / "endpoints.md").write_text("\n".join(lines), encoding="utf-8")
print(f"endpoints.md 생성 완료 — {len(data['endpoints'])}개 엔드포인트")

# ── 3. 앱 요약 청크 ────────────────────────────────────────
lines = ["# 하이픈 앱(서비스) 요약\n"]
for app_name, app in data["apps"].items():
    owned = ", ".join(f"`{t}`" for t in app.get("owned_tables", [])[:20])
    consumed = ", ".join(f"`{t}`" for t in app.get("consumed_tables", [])[:20])
    deps = [f"{d['to_app']}(weight={d['weight']}, {'+'.join(d['sources'])})"
            for d in app.get("outbound_deps", [])]

    lines.append(f"## {app_name}")
    lines.append(f"- **엔드포인트**: 전체 {app.get('endpoints_total', 0)} / 호출됨 {app.get('endpoints_called', 0)} / 미호출 {app.get('endpoints_uncalled', 0)}")
    lines.append(f"- **소유 테이블 수**: {app.get('owned_count', 0)} | **사용 테이블 수**: {app.get('consumed_count', 0)}")
    if owned:
        lines.append(f"- **소유 테이블**: {owned}")
    if consumed:
        lines.append(f"- **사용 테이블**: {consumed}")
    if deps:
        lines.append(f"- **의존 앱**: {', '.join(deps)}")
    lines.append("")

(OUT / "apps.md").write_text("\n".join(lines), encoding="utf-8")
print(f"apps.md 생성 완료 — {len(data['apps'])}개 앱")

# ── 4. 관계 그래프 청크 ────────────────────────────────────
edges = data.get("edges", {})
lines = ["# 하이픈 관계 그래프\n", "## 테이블 간 관계 (FK / 공유키)\n"]
for e in edges.get("table_edges", []):
    lines.append(
        f"- `{e['table_a']}` ↔ `{e['table_b']}` | "
        f"방향: {e.get('direction', '')} | "
        f"컬럼: {e.get('column_a_to_b', '')} | "
        f"타입: {e.get('relation_type', '')} | "
        f"신뢰도: {e.get('confidence', '')} | "
        f"근거: {e.get('evidence', '')}"
    )

lines.append("\n## 서비스 간 의존 관계\n")
for e in edges.get("service_edges", []):
    sources = "+".join(e.get("sources", []))
    lines.append(
        f"- `{e['from_app']}` → `{e['to_app']}` | "
        f"weight={e.get('weight', '')} | {sources}"
    )

(OUT / "edges.md").write_text("\n".join(lines), encoding="utf-8")
print(f"edges.md 생성 완료")

# ── 완료 요약 ──────────────────────────────────────────────
total_kb = sum((OUT / f).stat().st_size for f in ["tables.md", "endpoints.md", "apps.md", "edges.md"]) / 1024
print(f"\n전체 {total_kb:.0f} KB → chunks/ 폴더 확인")
print("Dify Knowledge Base에 파일 4개를 순서대로 업로드하세요.")
