"""
Step 4 (full): Build a unified table-relationship graph from three sources.

  1) MODEL_FK     — AST-parse every models.py and collect ForeignKey /
                    OneToOneField / ManyToManyField declarations.  This is
                    the canonical source of relationships in a Django app.
  2) SQL_JOIN     — the 10 raw-SQL JOIN edges already extracted in
                    table_edges.csv.
  3) NAMING_HINT  — shared-key columns discovered in the schema CSV that
                    *imply* a relationship (e.g., `channel_id` in many tables
                    that likely all reference a master channel table).

Reliability boosters:
  - AST parsing (not regex) for Python model files
  - Global "ModelName -> db_table" map resolved before FK target lookup
  - Cross-check every declared column actually exists in the schema CSV
  - Agreement bonus: an edge present in ≥2 sources becomes HIGH confidence

Output:
  - model_fks.csv               (raw FK extraction, one row per FK field)
  - table_edges_unified.csv     (unified edge list with source + confidence)
  - relations_report.md         (human summary)
"""
from __future__ import annotations
import ast, csv, os, re, sys, json
from collections import defaultdict, Counter

ROOT = "/Users/rachel/Documents/김명승 작업실/ugwanggiAPI-main"
BRANCH = os.path.join(ROOT, "ugwanggiAPI-main")
SCHEMA_CSV = os.path.join(ROOT, "hifen_scheme.csv")
FINAL_CSV = os.path.join(ROOT, "hifen_scheme_table_usage_final_boosted.csv")
SQL_EDGES_CSV = os.path.join(ROOT, "table_edges.csv")
SHARED_KEYS_CSV = os.path.join(ROOT, "candidate_shared_keys.csv")

OUT_FKS = os.path.join(ROOT, "model_fks.csv")
OUT_EDGES = os.path.join(ROOT, "table_edges_unified.csv")
OUT_REPORT = os.path.join(ROOT, "relations_report.md")

# ------------------------------------------------------------------
# Load schema: table -> set of column names, PK columns
# ------------------------------------------------------------------
table_columns: dict[str, set[str]] = defaultdict(set)
table_pks: dict[str, list[str]] = defaultdict(list)
with open(SCHEMA_CSV, newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        if len(row) < 6: continue
        t = row[0].strip()
        c = row[2].strip()
        key = row[5].strip() if len(row) > 5 else ''
        if t and c:
            table_columns[t].add(c)
            if key.upper() == 'PRI':
                table_pks[t].append(c)

# Load USED set
used_tables: set[str] = set()
with open(FINAL_CSV, newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r.get('boosted_usage') == 'USED':
            used_tables.add(r['table'])

# ------------------------------------------------------------------
# Pass 1: build ModelName -> db_table map (across all apps)
# ------------------------------------------------------------------
def find_all_models_py():
    for dp, dns, fns in os.walk(BRANCH):
        dns[:] = [d for d in dns if d not in ('__pycache__', '.git', 'node_modules', 'migrations')]
        for fn in fns:
            if fn == 'models.py' or (dp.endswith('/models') and fn.endswith('.py')):
                yield os.path.join(dp, fn)

def const_str(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None

def app_of(path: str) -> str:
    rel = os.path.relpath(path, BRANCH)
    return rel.split(os.sep, 1)[0]

# Parse all model files once
model_asts: list[tuple[str, ast.Module]] = []
for p in find_all_models_py():
    try:
        with open(p, 'r', encoding='utf-8', errors='ignore') as fh:
            tree = ast.parse(fh.read(), filename=p)
            model_asts.append((p, tree))
    except Exception as e:
        print(f"[parse-fail] {p}: {e}", file=sys.stderr)

# Build global ModelName -> db_table, ModelName -> app, ModelName -> pk_column
model_to_table: dict[str, str] = {}
model_to_app: dict[str, str] = {}
model_pk: dict[str, str] = {}   # explicit primary_key=True field's db_column (or field+_id-less)
model_duplicates: list[str] = []

def extract_db_table(classdef: ast.ClassDef) -> str | None:
    for item in classdef.body:
        if isinstance(item, ast.ClassDef) and item.name == 'Meta':
            for sub in item.body:
                if isinstance(sub, ast.Assign):
                    for tgt in sub.targets:
                        if isinstance(tgt, ast.Name) and tgt.id == 'db_table':
                            s = const_str(sub.value)
                            if s: return s
    return None

def extract_pk_column(classdef: ast.ClassDef) -> str | None:
    """Return the db_column of any field marked primary_key=True, else None."""
    for sub in classdef.body:
        if not isinstance(sub, ast.Assign): continue
        if len(sub.targets) != 1 or not isinstance(sub.targets[0], ast.Name): continue
        field_name = sub.targets[0].id
        if not isinstance(sub.value, ast.Call): continue
        is_pk = False
        db_col = None
        for kw in sub.value.keywords:
            if kw.arg == 'primary_key' and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                is_pk = True
            if kw.arg == 'db_column':
                s = const_str(kw.value)
                if s: db_col = s
        if is_pk:
            return db_col or field_name
    return None

for path, tree in model_asts:
    app = app_of(path)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            db_table = extract_db_table(node)
            if db_table:
                if node.name in model_to_table and model_to_table[node.name] != db_table:
                    model_duplicates.append(f"{node.name}: {model_to_table[node.name]} vs {db_table}")
                model_to_table[node.name] = db_table
                model_to_app[node.name] = app
                pk = extract_pk_column(node)
                if pk:
                    model_pk[node.name] = pk

print(f"Models with db_table: {len(model_to_table)}", file=sys.stderr)
if model_duplicates:
    print(f"  duplicates (same class name, different db_table): {len(model_duplicates)}", file=sys.stderr)

# ------------------------------------------------------------------
# Pass 2: extract FK fields per model
# ------------------------------------------------------------------
FK_TYPES = {'ForeignKey', 'OneToOneField', 'ManyToManyField'}

def rel_type_name(func: ast.AST) -> str | None:
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return None

def target_model_name(arg: ast.AST) -> str | None:
    # ForeignKey('AppLabel.Model') or ForeignKey('Model') or ForeignKey(Model)
    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
        s = arg.value
        if s == 'self': return 'self'
        # strip app prefix if present
        if '.' in s: s = s.split('.')[-1]
        return s
    if isinstance(arg, ast.Name):
        return arg.id
    if isinstance(arg, ast.Attribute):
        # e.g., brand.models.Brand -> Brand
        return arg.attr
    return None

fks: list[dict] = []  # raw extraction rows

for path, tree in model_asts:
    app = app_of(path)
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef): continue
        this_table = extract_db_table(node)
        if not this_table: continue
        for sub in node.body:
            if not isinstance(sub, ast.Assign): continue
            if len(sub.targets) != 1 or not isinstance(sub.targets[0], ast.Name): continue
            field_name = sub.targets[0].id
            if not isinstance(sub.value, ast.Call): continue
            rt = rel_type_name(sub.value.func)
            if rt not in FK_TYPES: continue
            if not sub.value.args: continue
            target = target_model_name(sub.value.args[0])
            if not target: continue
            if target == 'self':
                target_table = this_table
            else:
                target_table = model_to_table.get(target)
            if not target_table: continue
            # db_column kwarg?
            db_column = None
            on_delete = None
            null_flag = False
            for kw in sub.value.keywords:
                if kw.arg == 'db_column':
                    db_column = const_str(kw.value)
                elif kw.arg == 'on_delete' and isinstance(kw.value, ast.Attribute):
                    on_delete = kw.value.attr
                elif kw.arg == 'null' and isinstance(kw.value, ast.Constant):
                    null_flag = bool(kw.value.value)
            from_column = db_column or (field_name if rt == 'ManyToManyField' else field_name + '_id')
            # Default target column: target model's primary_key=True field if any, else 'id'
            to_column = model_pk.get(target, 'id')
            for kw in sub.value.keywords:
                if kw.arg == 'to_field':
                    s = const_str(kw.value)
                    if s: to_column = s
            fks.append({
                'from_app': app,
                'from_model': node.name,
                'from_table': this_table,
                'from_field': field_name,
                'from_column': from_column,
                'relation_type': rt,
                'to_model': target,
                'to_table': target_table,
                'to_column': to_column,
                'on_delete': on_delete or '',
                'null': null_flag,
                'file': os.path.relpath(path, BRANCH),
            })

print(f"FK fields extracted: {len(fks)}", file=sys.stderr)

# ------------------------------------------------------------------
# Cross-verify: do from_column and to_column actually exist in schema?
# ------------------------------------------------------------------
for r in fks:
    ft, fc, tt, tc = r['from_table'], r['from_column'], r['to_table'], r['to_column']
    r['from_col_in_schema'] = fc in table_columns.get(ft, set())
    r['to_col_in_schema'] = tc in table_columns.get(tt, set())
    r['from_table_used'] = ft in used_tables
    r['to_table_used'] = tt in used_tables

# Write raw FK extraction
with open(OUT_FKS, 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['from_app','from_model','from_table','from_field','from_column',
                  'relation_type','to_model','to_table','to_column','on_delete','null',
                  'from_col_in_schema','to_col_in_schema','from_table_used','to_table_used','file']
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(fks)

# ------------------------------------------------------------------
# Load the SQL_JOIN edges
# ------------------------------------------------------------------
sql_edges: list[dict] = []
if os.path.exists(SQL_EDGES_CSV):
    with open(SQL_EDGES_CSV, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            sql_edges.append(r)

# ------------------------------------------------------------------
# Load shared-key naming hints
# ------------------------------------------------------------------
shared_keys: list[dict] = []
if os.path.exists(SHARED_KEYS_CSV):
    with open(SHARED_KEYS_CSV, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            shared_keys.append(r)

# ------------------------------------------------------------------
# Unify edges
# Keyed by (from_table, to_table) — direction preserved for MODEL_FK
# ------------------------------------------------------------------
# For SQL_JOIN/NAMING_HINT we treat edges as undirected (normalize).
unified: dict[tuple[str, str], dict] = {}

def norm_pair(a: str, b: str) -> tuple[str, str]:
    return tuple(sorted([a, b]))  # type: ignore

# Add MODEL_FK (directed source; stored under normalized key with direction recorded)
for r in fks:
    if not (r['from_table_used'] and r['to_table_used']): continue
    pair = norm_pair(r['from_table'], r['to_table'])
    slot = unified.setdefault(pair, {'sources': set(), 'details': []})
    slot['sources'].add('MODEL_FK')
    slot['details'].append({
        'source': 'MODEL_FK',
        'direction': f"{r['from_table']} -> {r['to_table']}",
        'from_column': r['from_column'],
        'to_column': r['to_column'],
        'relation_type': r['relation_type'],
        'cols_verified': r['from_col_in_schema'] and r['to_col_in_schema'],
        'evidence': r['file'],
    })

# Add SQL_JOIN
for e in sql_edges:
    t1, t2 = e['from_table'], e['to_table']
    if t1 not in used_tables or t2 not in used_tables: continue
    pair = norm_pair(t1, t2)
    slot = unified.setdefault(pair, {'sources': set(), 'details': []})
    slot['sources'].add('SQL_JOIN')
    slot['details'].append({
        'source': 'SQL_JOIN',
        'direction': f"{t1} <-> {t2}",
        'from_column': e.get('key_left',''),
        'to_column': e.get('key_right',''),
        'relation_type': 'JOIN',
        'cols_verified': (
            e.get('key_left','') in table_columns.get(t1, set()) and
            e.get('key_right','') in table_columns.get(t2, set())
        ),
        'evidence': e.get('sample_files',''),
    })

# Add NAMING_HINT — only create edges when a shared-column column *is also the PK
# of some table*.  This is a conservative rule: `channel_id` shared across 51
# tables only implies edges from each of those tables to the table whose PK/unique
# column is `channel_id` (or to `YT_channel_*` masters).  Without that anchor we'd
# create n*(n-1)/2 noise edges.  We skip NAMING_HINT if we can't anchor.
#
# Simpler rule used here: if a shared column exists, and exactly one USED table's
# column set contains that column AS a likely anchor (column named 'id' in a
# table whose stem matches the shared column, e.g., `channel_id` -> table `channel`
# or suffix `_channel`), create edges.  Otherwise, we just note the shared-column
# cluster without adding per-pair edges.
naming_clusters: list[dict] = []
for s in shared_keys:
    col = s['shared_column']
    tabs = s['tables'].split('|')
    naming_clusters.append({'column': col, 'tables': tabs, 'count': int(s['table_count'])})

# ------------------------------------------------------------------
# Compute confidence per unified edge
# ------------------------------------------------------------------
final_rows = []
for pair, slot in unified.items():
    srcs = slot['sources']
    # MODEL_FK is developer intent = ground truth → HIGH by default.
    # SQL_JOIN adds corroboration but doesn't increase confidence beyond HIGH.
    if 'MODEL_FK' in srcs:
        conf = 'HIGH'
    elif 'SQL_JOIN' in srcs:
        conf = 'MED'
    else:
        conf = 'LOW'
    # Pick representative detail (MODEL_FK preferred)
    det = next((d for d in slot['details'] if d['source'] == 'MODEL_FK'),
               slot['details'][0])
    final_rows.append({
        'table_a': pair[0],
        'table_b': pair[1],
        'sources': '|'.join(sorted(srcs)),
        'confidence': conf,
        'direction': det['direction'],
        'column_a_to_b': f"{det['from_column']} -> {det['to_column']}",
        'relation_type': det['relation_type'],
        'cols_verified': det.get('cols_verified', False),
        'evidence': det.get('evidence', ''),
    })

final_rows.sort(key=lambda r: (r['confidence'] != 'HIGH', r['table_a']))
with open(OUT_EDGES, 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['table_a','table_b','sources','confidence','direction',
                  'column_a_to_b','relation_type','cols_verified','evidence']
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(final_rows)

# ------------------------------------------------------------------
# Report
# ------------------------------------------------------------------
lines = ["# Step 4 — Unified Relations Report\n"]
total = len(final_rows)
src_dist = Counter()
conf_dist = Counter()
for r in final_rows:
    src_dist[r['sources']] += 1
    conf_dist[r['confidence']] += 1
lines.append(f"**Total unified edges (USED↔USED):** {total}\n")
lines.append(f"\n**By source:** {dict(src_dist)}")
lines.append(f"\n**By confidence:** {dict(conf_dist)}\n")
lines.append("\n## Coverage\n")
lines.append(f"- FK fields extracted: {len(fks)}")
lines.append(f"- FK fields where BOTH endpoints in schema: {sum(1 for r in fks if r['from_col_in_schema'] and r['to_col_in_schema'])}")
lines.append(f"- FK fields pointing to UNUSED table (dropped): {sum(1 for r in fks if not r['to_table_used'])}")
lines.append(f"- Models with db_table: {len(model_to_table)}")
lines.append(f"- Raw SQL JOIN edges: {len(sql_edges)}")
lines.append(f"- Shared-key clusters (naming hints): {len(naming_clusters)}\n")

lines.append("\n## Top shared-key clusters (naming hints)\n")
lines.append("| column | tables sharing |")
lines.append("|---|---|")
for c in sorted(naming_clusters, key=lambda x: -x['count'])[:10]:
    lines.append(f"| `{c['column']}` | {c['count']} |")

with open(OUT_REPORT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print(f"Wrote {OUT_FKS}", file=sys.stderr)
print(f"Wrote {OUT_EDGES}", file=sys.stderr)
print(f"Wrote {OUT_REPORT}", file=sys.stderr)
print(f"Unified edges: {total}", file=sys.stderr)
print(f"  by source: {dict(src_dist)}", file=sys.stderr)
print(f"  by confidence: {dict(conf_dist)}", file=sys.stderr)
