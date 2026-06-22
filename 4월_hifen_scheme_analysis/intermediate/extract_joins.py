"""
Step 4: Extract table-to-table JOIN relationships from raw SQL in the branch.

Strategy:
  A) Parse JOIN clauses: `(LEFT|RIGHT|INNER|OUTER)? JOIN <table> [alias] ON <cond>`
     and the FROM clause that anchors them, to build edges.
  B) For each JOIN, try to extract the join keys from the ON clause
     (e.g., `A.channel_id = B.channel_id`).
  C) Cross-check both endpoints are in the USED table set.  Non-USED endpoints
     get dropped as noise.
  D) Also derive *candidate* relationships from schema: any column named
     `<something>_id` that appears in multiple tables is a likely shared key.

Outputs:
  - table_edges.csv: (from_table, to_table, key_left, key_right, hit_count, sample_files)
  - candidate_shared_keys.csv: (column, tables_using_it, count)
"""
from __future__ import annotations
import csv, os, re, sys
from collections import defaultdict, Counter

ROOT = "/Users/rachel/Documents/김명승 작업실/ugwanggiAPI-main"
BRANCH = os.path.join(ROOT, "ugwanggiAPI-main")
SCHEMA_CSV = os.path.join(ROOT, "hifen_scheme.csv")
FINAL_CSV = os.path.join(ROOT, "hifen_scheme_table_usage_final_boosted.csv")
OUT_EDGES = os.path.join(ROOT, "table_edges.csv")
OUT_SHARED = os.path.join(ROOT, "candidate_shared_keys.csv")

# Load USED tables
used_tables: set[str] = set()
with open(FINAL_CSV, newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r.get('boosted_usage') == 'USED':
            used_tables.add(r['table'])
print(f"USED tables: {len(used_tables)}", file=sys.stderr)

# Load all files
all_files: list[tuple[str, str]] = []
for dp, dns, fns in os.walk(BRANCH):
    dns[:] = [d for d in dns if d not in ('__pycache__', '.git', 'node_modules')]
    for fn in fns:
        if fn.endswith(('.py', '.sql', '.txt')):
            p = os.path.join(dp, fn)
            try:
                with open(p, 'r', encoding='utf-8', errors='ignore') as fh:
                    all_files.append((p, fh.read()))
            except Exception:
                pass

# ------------- A) JOIN edge extraction -------------
# Simplified: find sliding windows around "FROM <T> [alias]" ... "JOIN <T2> [alias] ON <cond>"
# We capture the nearest FROM/JOIN-anchor table for each JOIN clause.
IDENT = r'[A-Za-z_][A-Za-z0-9_]*'
FROM_RX = re.compile(
    r'\bFROM\s+`?(' + IDENT + r')`?(?:\s+(?:AS\s+)?(' + IDENT + r'))?',
    re.IGNORECASE,
)
JOIN_RX = re.compile(
    r'\b(?:LEFT|RIGHT|INNER|OUTER|CROSS)?\s*(?:OUTER\s+)?JOIN\s+`?(' + IDENT + r')`?'
    r'(?:\s+(?:AS\s+)?(' + IDENT + r'))?'
    r'\s+ON\s+([^\n;]+?)(?=\b(?:LEFT|RIGHT|INNER|OUTER|CROSS|JOIN|WHERE|GROUP|ORDER|LIMIT|HAVING|\))|$)',
    re.IGNORECASE,
)
ON_KEY_RX = re.compile(
    r'(?:(' + IDENT + r')\.)?(' + IDENT + r')\s*=\s*(?:(' + IDENT + r')\.)?(' + IDENT + r')'
)

edges: dict[tuple[str, str, str, str], dict] = defaultdict(lambda: {'count': 0, 'files': []})

for p, text in all_files:
    # Find FROM anchors and JOINs in proximity.  We track (table, alias) map per
    # text scan; for simplicity, per-match we resolve aliases in a local window.
    # Build a list of (pos, kind, table, alias)
    anchors = []
    for m in FROM_RX.finditer(text):
        anchors.append((m.start(), 'FROM', m.group(1), m.group(2)))
    for m in JOIN_RX.finditer(text):
        anchors.append((m.start(), 'JOIN', m.group(1), m.group(2), m.group(3)))

    # Build alias map per proximity cluster (grouped by nearest FROM within 2000 chars)
    # We'll process JOINs: find last FROM before this JOIN within 2000 chars.
    from_positions = [(a[0], a[2], a[3]) for a in anchors if a[1] == 'FROM']

    def resolve_alias(alias_or_table: str, join_local_aliases: dict[str, str], from_alias: dict[str, str]) -> str:
        if alias_or_table in join_local_aliases:
            return join_local_aliases[alias_or_table]
        if alias_or_table in from_alias:
            return from_alias[alias_or_table]
        return alias_or_table  # treat as table name

    for a in anchors:
        if a[1] != 'JOIN':
            continue
        pos, _, jt, j_alias, on_expr = a
        # Find nearest preceding FROM within 2000 chars
        from_ctx = None
        for (fp, ft, fa) in from_positions:
            if fp < pos and pos - fp < 2000:
                from_ctx = (ft, fa)
        if not from_ctx:
            continue
        from_table, from_alias = from_ctx
        # Alias map for this local scope: FROM alias → table, plus JOIN alias → table
        alias_map = {}
        if from_alias:
            alias_map[from_alias] = from_table
        if j_alias:
            alias_map[j_alias] = jt
        # Also include other JOIN tables seen in a small window before this one
        for b in anchors:
            if b[1] == 'JOIN' and b[0] < pos and pos - b[0] < 2000:
                bt, ba = b[2], b[3]
                if ba:
                    alias_map[ba] = bt

        # Extract keys from ON expression
        km = ON_KEY_RX.search(on_expr)
        if km:
            lq, lk, rq, rk = km.groups()
            left_table = alias_map.get(lq, lq) if lq else from_table
            right_table = alias_map.get(rq, rq) if rq else jt
            # We want the edge between from-ish side and joined-side
            t1, t2 = sorted([from_table, jt])
            # Normalize key direction
            if left_table == from_table and right_table == jt:
                key_pair = (lk, rk)
            elif left_table == jt and right_table == from_table:
                key_pair = (rk, lk)
            else:
                key_pair = (lk, rk)
            edge_key = (from_table, jt, key_pair[0], key_pair[1])
        else:
            edge_key = (from_table, jt, '', '')
        rec = edges[edge_key]
        rec['count'] += 1
        rel = os.path.relpath(p, BRANCH)
        if rel not in rec['files'] and len(rec['files']) < 3:
            rec['files'].append(rel)

# Filter edges to USED tables on both sides
filtered_edges = []
dropped_noise = 0
for (t1, t2, k1, k2), rec in edges.items():
    if t1 not in used_tables or t2 not in used_tables:
        dropped_noise += 1
        continue
    if t1 == t2:
        continue  # self-join skipped
    filtered_edges.append((t1, t2, k1, k2, rec['count'], ' | '.join(rec['files'])))

# Sort by count desc
filtered_edges.sort(key=lambda r: -r[4])

with open(OUT_EDGES, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['from_table','to_table','key_left','key_right','hit_count','sample_files'])
    for e in filtered_edges:
        w.writerow(e)

print(f"Extracted JOIN edges (USED↔USED): {len(filtered_edges)} (dropped {dropped_noise} noise edges)", file=sys.stderr)

# ------------- B) Candidate shared keys from schema -------------
# From schema CSV, collect columns shaped like `<something>_id` or well-known
# join keys (channel_id, video_id, user_id, brand_id, etc.).  Flag any column
# name that appears in ≥2 tables.
col_to_tables: dict[str, list[str]] = defaultdict(list)
with open(SCHEMA_CSV, newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    header = next(reader)
    seen_pairs = set()
    for row in reader:
        if len(row) < 3: continue
        table = row[0].strip()
        col = row[2].strip()
        if not table or not col: continue
        if table not in used_tables: continue  # only USED tables
        pair = (table, col)
        if pair in seen_pairs: continue
        seen_pairs.add(pair)
        col_to_tables[col].append(table)

JOIN_KEY_CANDIDATE_RX = re.compile(r'(_id|_key|_code|_no|_number)$', re.IGNORECASE)
shared = []
for col, tabs in col_to_tables.items():
    if len(tabs) < 2:
        continue
    is_key_shape = bool(JOIN_KEY_CANDIDATE_RX.search(col)) or col in {
        'channel_id','video_id','user_id','brand_id','post_id','comment_id',
        'campaign_id','product_id','hashtag_id','creator_id','owner_id','tag_id',
    }
    if is_key_shape:
        shared.append((col, len(tabs), '|'.join(sorted(tabs))))

shared.sort(key=lambda r: -r[1])
with open(OUT_SHARED, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['shared_column','table_count','tables'])
    for row in shared:
        w.writerow(row)

print(f"Candidate shared-key columns: {len(shared)}", file=sys.stderr)
print(f"Wrote {OUT_EDGES}", file=sys.stderr)
print(f"Wrote {OUT_SHARED}", file=sys.stderr)

# Print top edges and top shared keys
print("\nTop 15 JOIN edges by frequency:", file=sys.stderr)
for e in filtered_edges[:15]:
    print(f"  {e[0]} ↔ {e[1]}  key={e[2]}={e[3]}  (x{e[4]})", file=sys.stderr)
print("\nTop 10 shared-key columns:", file=sys.stderr)
for s in shared[:10]:
    print(f"  {s[0]}  ({s[1]} tables)", file=sys.stderr)
