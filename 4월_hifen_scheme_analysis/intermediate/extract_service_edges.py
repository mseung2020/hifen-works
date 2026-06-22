"""
Step 7: Inter-app (service) relationship graph.

Sources combined:
  1) IMPORTS   — cross-app Python imports (from <app>.<module> import ...).
                 Very strong signal of code-level coupling.
  2) SHARED_TABLE — app A owns table T, app B consumes T (reads/writes/joins).
                 From table_to_apps_boosted.csv.
  3) CRON      — cron.py in app A touches tables/models owned by app B.

Output:
  - core_materials/service_edges.csv   (edge list, app A -> app B with sources + weight)
  - core_materials/service_summary.csv (per-app rollup: tables, endpoints, inbound/outbound degree)
  - intermediate/services_report.md
"""
from __future__ import annotations
import ast, csv, os, re, sys
from collections import defaultdict, Counter

ROOT = "/Users/rachel/Documents/김명승 작업실/ugwanggiAPI-main"
BRANCH = os.path.join(ROOT, "ugwanggiAPI-main")
CORE = os.path.join(ROOT, "core_materials")
INTER = os.path.join(ROOT, "intermediate")
T2A = os.path.join(CORE, "table_to_apps_boosted.csv")
A2T = os.path.join(CORE, "app_to_tables.csv")
ENDPOINTS = os.path.join(CORE, "api_endpoints.csv")
USAGE = os.path.join(CORE, "endpoint_usage.csv")
FINAL = os.path.join(CORE, "hifen_scheme_table_usage_final_boosted.csv")

OUT_EDGES = os.path.join(CORE, "service_edges.csv")
OUT_SUMMARY = os.path.join(CORE, "service_summary.csv")
OUT_REPORT = os.path.join(INTER, "services_report.md")

APPS = [
    'admin','ads','aichat','aitools','amore','archive','brand','creators_insights',
    'express','instagram','instagram_admin','keywords','kpi','monitoring',
    'oliveyoung','partner','partner_admin','partner_instagram','preview','search',
    'subscribe','survey','tiktok','trends','ugwanggiAPI','user','youtube','youtube_shopping',
]
APP_SET = set(APPS)

# Raw edge accumulator
edges: dict[tuple[str, str], dict] = defaultdict(
    lambda: {'IMPORTS': 0, 'SHARED_TABLE': 0, 'CRON': 0,
             'import_samples': [], 'shared_tables': [], 'cron_samples': []}
)

# ------------------------------------------------------------------
# 1) IMPORTS: cross-app Python imports
# ------------------------------------------------------------------
# For every .py under each app, parse AST for  ImportFrom / Import nodes
# whose module starts with another app name.
def scan_imports_for_app(app: str) -> list[tuple[str, str, str]]:
    """Return list of (target_app, imported_thing, file_path)."""
    results = []
    app_dir = os.path.join(BRANCH, app)
    if not os.path.isdir(app_dir): return results
    for dp, dns, fns in os.walk(app_dir):
        dns[:] = [d for d in dns if d not in ('__pycache__', 'migrations')]
        for fn in fns:
            if not fn.endswith('.py'): continue
            p = os.path.join(dp, fn)
            try:
                tree = ast.parse(open(p, encoding='utf-8', errors='ignore').read(), p)
            except Exception: continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    mod = node.module or ''
                    head = mod.split('.', 1)[0]
                    if head in APP_SET and head != app:
                        for alias in node.names:
                            results.append((head, f"{mod}.{alias.name}", p))
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        head = (alias.name or '').split('.', 1)[0]
                        if head in APP_SET and head != app:
                            results.append((head, alias.name, p))
    return results

for app in APPS:
    for target, imported, fp in scan_imports_for_app(app):
        slot = edges[(app, target)]
        slot['IMPORTS'] += 1
        if len(slot['import_samples']) < 3:
            sample = f"{os.path.relpath(fp, BRANCH)}::{imported}"
            if sample not in slot['import_samples']:
                slot['import_samples'].append(sample)

# ------------------------------------------------------------------
# 2) SHARED_TABLE: owner app vs consumer apps
# ------------------------------------------------------------------
# From table_to_apps_boosted.csv
with open(T2A, newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        owners = [o for o in r['owner_app'].split('|') if o]
        consumers = [c for c in r['consumer_apps'].split('|') if c]
        for owner in owners:
            for cons in consumers:
                if owner == cons: continue
                slot = edges[(cons, owner)]  # consumer depends on owner's table
                slot['SHARED_TABLE'] += 1
                if len(slot['shared_tables']) < 5:
                    if r['table'] not in slot['shared_tables']:
                        slot['shared_tables'].append(r['table'])

# ------------------------------------------------------------------
# 3) CRON dependencies
# ------------------------------------------------------------------
# For each app, if cron.py exists, it counts any model owned by another app.
# We use the ModelName->db_table map plus the app ownership info to attribute.

# Build ModelName -> owner_app via CSV
table_owner: dict[str, str] = {}
with open(T2A, newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        owners = [o for o in r['owner_app'].split('|') if o]
        if owners:
            table_owner[r['table']] = owners[0]

# Also build ModelName -> db_table (from models.py AST across apps)
def const_str(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None

model_to_table: dict[str, str] = {}
for app in APPS:
    mp = os.path.join(BRANCH, app, 'models.py')
    if not os.path.isfile(mp): continue
    try:
        tree = ast.parse(open(mp, encoding='utf-8', errors='ignore').read())
    except Exception: continue
    for n in ast.walk(tree):
        if isinstance(n, ast.ClassDef):
            for item in n.body:
                if isinstance(item, ast.ClassDef) and item.name == 'Meta':
                    for s in item.body:
                        if isinstance(s, ast.Assign):
                            for tgt in s.targets:
                                if isinstance(tgt, ast.Name) and tgt.id == 'db_table':
                                    v = const_str(s.value)
                                    if v: model_to_table[n.name] = v

MODEL_OBJECTS_RX = re.compile(r'\b([A-Z][A-Za-z0-9_]+)\s*\.\s*objects\b')
RAW_SQL_TBL_RX = re.compile(
    r'\b(?:FROM|JOIN|INSERT\s+INTO|UPDATE|DELETE\s+FROM)\s+`?([A-Za-z_][A-Za-z0-9_]*)`?',
    re.IGNORECASE,
)

for app in APPS:
    cp = os.path.join(BRANCH, app, 'cron.py')
    if not os.path.isfile(cp): continue
    try:
        text = open(cp, encoding='utf-8', errors='ignore').read()
    except Exception: continue
    seen_targets: set[str] = set()
    # ORM refs
    for m in MODEL_OBJECTS_RX.finditer(text):
        cls = m.group(1)
        t = model_to_table.get(cls)
        if not t: continue
        owner = table_owner.get(t)
        if owner and owner != app and owner in APP_SET:
            seen_targets.add((owner, t))
    # Raw SQL refs
    for m in RAW_SQL_TBL_RX.finditer(text):
        t = m.group(1)
        owner = table_owner.get(t)
        if owner and owner != app and owner in APP_SET:
            seen_targets.add((owner, t))
    for owner, t in seen_targets:
        slot = edges[(app, owner)]
        slot['CRON'] += 1
        if len(slot['cron_samples']) < 3:
            sample = f"{app}/cron.py::{t}"
            if sample not in slot['cron_samples']:
                slot['cron_samples'].append(sample)

# ------------------------------------------------------------------
# Compose edges + weight
# ------------------------------------------------------------------
def weight(slot) -> int:
    # IMPORTS is strongest code coupling; SHARED_TABLE is data coupling; CRON is scheduled batch
    return slot['IMPORTS'] * 3 + slot['SHARED_TABLE'] * 2 + slot['CRON'] * 2

edge_rows = []
for (a, b), slot in edges.items():
    if slot['IMPORTS'] == 0 and slot['SHARED_TABLE'] == 0 and slot['CRON'] == 0:
        continue
    sources = []
    if slot['IMPORTS']: sources.append('IMPORTS')
    if slot['SHARED_TABLE']: sources.append('SHARED_TABLE')
    if slot['CRON']: sources.append('CRON')
    edge_rows.append({
        'from_app': a,
        'to_app': b,
        'weight': weight(slot),
        'sources': '|'.join(sources),
        'imports_count': slot['IMPORTS'],
        'shared_tables_count': slot['SHARED_TABLE'],
        'cron_count': slot['CRON'],
        'import_samples': ' | '.join(slot['import_samples']),
        'shared_tables': ' | '.join(slot['shared_tables']),
        'cron_samples': ' | '.join(slot['cron_samples']),
    })
edge_rows.sort(key=lambda r: -r['weight'])

with open(OUT_EDGES, 'w', newline='', encoding='utf-8') as f:
    fn = ['from_app','to_app','weight','sources','imports_count',
          'shared_tables_count','cron_count','import_samples','shared_tables','cron_samples']
    w = csv.DictWriter(f, fieldnames=fn)
    w.writeheader()
    w.writerows(edge_rows)

# ------------------------------------------------------------------
# Per-app summary
# ------------------------------------------------------------------
# Load owned/consumed counts
owned = defaultdict(int); consumed = defaultdict(int)
with open(A2T, newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        owned[r['app']] = int(r['owned_count'])
        consumed[r['app']] = int(r['consumed_count'])

# Endpoint counts
endpoint_total = defaultdict(int)
endpoint_uncalled = defaultdict(int)
with open(ENDPOINTS, newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        endpoint_total[r['app']] += 1
with open(USAGE, newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r['usage'] == 'UNCALLED':
            endpoint_uncalled[r['app']] += 1

inbound = defaultdict(int); outbound = defaultdict(int)
for r in edge_rows:
    outbound[r['from_app']] += 1
    inbound[r['to_app']] += 1

summary_rows = []
for app in sorted(APP_SET):
    summary_rows.append({
        'app': app,
        'owned_tables': owned.get(app, 0),
        'consumed_tables': consumed.get(app, 0),
        'endpoints_total': endpoint_total.get(app, 0),
        'endpoints_uncalled': endpoint_uncalled.get(app, 0),
        'outbound_deps': outbound.get(app, 0),
        'inbound_deps': inbound.get(app, 0),
    })
summary_rows.sort(key=lambda r: -(r['outbound_deps'] + r['inbound_deps']))

with open(OUT_SUMMARY, 'w', newline='', encoding='utf-8') as f:
    fn = ['app','owned_tables','consumed_tables','endpoints_total',
          'endpoints_uncalled','outbound_deps','inbound_deps']
    w = csv.DictWriter(f, fieldnames=fn)
    w.writeheader()
    w.writerows(summary_rows)

# ------------------------------------------------------------------
# Report
# ------------------------------------------------------------------
lines = ["# Step 7 — Inter-app Service Graph\n"]
lines.append(f"**Total directed edges:** {len(edge_rows)}")
lines.append(f"**Apps active in graph:** "
             f"{len(set(r['from_app'] for r in edge_rows) | set(r['to_app'] for r in edge_rows))}\n")
# Source breakdown
src_counter = Counter()
for r in edge_rows:
    for s in r['sources'].split('|'):
        src_counter[s] += 1
lines.append(f"**Edges by source (non-exclusive):** "
             + ", ".join(f"{k}={v}" for k,v in src_counter.most_common()))

# Top edges by weight
lines.append("\n## Top 20 dependency edges (by weight)\n")
lines.append("| from | to | weight | sources | imports | shared_tables | cron |")
lines.append("|---|---|---|---|---|---|---|")
for r in edge_rows[:20]:
    lines.append(f"| {r['from_app']} | {r['to_app']} | {r['weight']} | {r['sources']} | "
                 f"{r['imports_count']} | {r['shared_tables_count']} | {r['cron_count']} |")

# Top hubs (inbound — most depended-upon)
lines.append("\n## Top inbound (most depended-upon) apps\n| app | inbound_deps |\n|---|---|")
inbound_sorted = sorted(APP_SET, key=lambda a: -inbound.get(a, 0))
for a in inbound_sorted[:10]:
    if inbound.get(a, 0) == 0: continue
    lines.append(f"| {a} | {inbound[a]} |")

# Top fan-out
lines.append("\n## Top outbound (most dependent) apps\n| app | outbound_deps |\n|---|---|")
outbound_sorted = sorted(APP_SET, key=lambda a: -outbound.get(a, 0))
for a in outbound_sorted[:10]:
    if outbound.get(a, 0) == 0: continue
    lines.append(f"| {a} | {outbound[a]} |")

with open(OUT_REPORT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print(f"Directed edges: {len(edge_rows)}", file=sys.stderr)
print(f"By source: {dict(src_counter)}", file=sys.stderr)
print(f"Wrote {OUT_EDGES}", file=sys.stderr)
print(f"Wrote {OUT_SUMMARY}", file=sys.stderr)
print(f"Wrote {OUT_REPORT}", file=sys.stderr)
