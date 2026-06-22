"""
Step 4.5: Normalization topology analysis.

Inputs:
  - table_edges_unified.csv  (HIGH + MED edges from Step 4)
  - hifen_scheme_table_usage_final_boosted.csv  (USED tables)
  - candidate_shared_keys.csv  (shared-column clusters)

Outputs:
  - normalization_clusters.csv: connected components in the FK graph
      columns: cluster_id, size, hub_table, member_tables
  - isolated_tables.csv: USED tables with 0 FK edges
      columns: table, note
  - denormalization_hotspots.csv: shared-column clusters ranked by "FK coverage"
      columns: shared_column, tables_sharing, fk_linked_pairs, coverage_ratio, hotspot_level
"""
from __future__ import annotations
import csv, os, sys
from collections import defaultdict, Counter

ROOT = "/Users/rachel/Documents/김명승 작업실/ugwanggiAPI-main"
EDGES = os.path.join(ROOT, "table_edges_unified.csv")
FINAL = os.path.join(ROOT, "hifen_scheme_table_usage_final_boosted.csv")
SHARED = os.path.join(ROOT, "candidate_shared_keys.csv")

OUT_CLUSTERS = os.path.join(ROOT, "normalization_clusters.csv")
OUT_ISOLATED = os.path.join(ROOT, "isolated_tables.csv")
OUT_HOTSPOTS = os.path.join(ROOT, "denormalization_hotspots.csv")

# ---- Load USED tables ----
used: set[str] = set()
with open(FINAL, newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r.get('boosted_usage') == 'USED':
            used.add(r['table'])

# ---- Load edges (MODEL_FK and SQL_JOIN both count as "relationship exists") ----
adj: dict[str, set[str]] = defaultdict(set)
edge_pairs: set[tuple[str, str]] = set()
with open(EDGES, newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        a, b = r['table_a'], r['table_b']
        if a in used and b in used and a != b:
            adj[a].add(b)
            adj[b].add(a)
            edge_pairs.add(tuple(sorted([a, b])))

# ---- Connected components ----
seen: set[str] = set()
components: list[list[str]] = []
for t in used:
    if t in seen: continue
    stack = [t]
    comp: list[str] = []
    while stack:
        x = stack.pop()
        if x in seen: continue
        seen.add(x); comp.append(x)
        for n in adj[x]:
            if n not in seen:
                stack.append(n)
    components.append(comp)

# Rank components by size (desc), skipping size-1 isolates (written separately)
multi = [c for c in components if len(c) > 1]
isolates = [c[0] for c in components if len(c) == 1]
multi.sort(key=lambda c: -len(c))

# Hub = node with highest degree within the component
def hub_of(comp: list[str]) -> str:
    return max(comp, key=lambda t: len(adj[t] & set(comp)))

with open(OUT_CLUSTERS, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['cluster_id','size','hub_table','hub_degree','member_tables'])
    for i, comp in enumerate(multi, 1):
        hub = hub_of(comp)
        deg = len(adj[hub] & set(comp))
        w.writerow([f'C{i:03d}', len(comp), hub, deg, '|'.join(sorted(comp))])

with open(OUT_ISOLATED, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['table','note'])
    for t in sorted(isolates):
        # Heuristic note
        lower = t.lower()
        if any(k in lower for k in ('trend','daily','weekly','monthly','_cost_per_','snapshot','stat','history','_log')):
            note = 'flat/snapshot/log table (by name)'
        elif any(k in lower for k in ('crawl','scrap','task','waiting','queue')):
            note = 'pipeline/queue table (by name)'
        elif lower.startswith(('yt_ugwanggi_trending','yt_video_trending')):
            note = 'aggregate/trending output'
        else:
            note = ''
        w.writerow([t, note])

# ---- Denormalization hotspots ----
# For each shared-key column, count:
#   - tables sharing that column (from CSV)
#   - how many pairs among those tables are actually connected by FK
# Lower coverage ratio = more denormalized.
shared_rows = []
with open(SHARED, newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        shared_rows.append({
            'column': r['shared_column'],
            'tables': [t for t in r['tables'].split('|') if t in used],
            'count': 0,
        })

hotspots = []
for s in shared_rows:
    tabs = s['tables']
    n = len(tabs)
    if n < 2: continue
    total_pairs = n * (n - 1) // 2
    linked = 0
    for i in range(n):
        for j in range(i+1, n):
            if tuple(sorted([tabs[i], tabs[j]])) in edge_pairs:
                linked += 1
    coverage = linked / total_pairs if total_pairs else 0
    if coverage >= 0.3:  level = 'LOW'      # mostly normalized
    elif coverage >= 0.1: level = 'MEDIUM'  # partial
    elif coverage > 0:   level = 'HIGH'    # sparse
    else:                level = 'SEVERE'  # no FK at all
    hotspots.append({
        'shared_column': s['column'],
        'tables_sharing': n,
        'fk_linked_pairs': linked,
        'total_possible_pairs': total_pairs,
        'coverage_ratio': round(coverage, 4),
        'hotspot_level': level,
    })

# Sort: most severe first, then by size desc
level_order = {'SEVERE': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
hotspots.sort(key=lambda h: (level_order[h['hotspot_level']], -h['tables_sharing']))

with open(OUT_HOTSPOTS, 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['shared_column','tables_sharing','fk_linked_pairs',
                  'total_possible_pairs','coverage_ratio','hotspot_level']
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(hotspots)

# ---- Console summary ----
print(f"USED tables: {len(used)}", file=sys.stderr)
print(f"Edges considered: {len(edge_pairs)}", file=sys.stderr)
print(f"Connected components: {len(components)} (multi-node: {len(multi)}, isolates: {len(isolates)})", file=sys.stderr)
print(f"Biggest clusters:", file=sys.stderr)
for c in multi[:5]:
    print(f"  size {len(c)} — hub: {hub_of(c)}", file=sys.stderr)
print(f"\nIsolated tables: {len(isolates)}", file=sys.stderr)
print(f"\nHotspot distribution: {Counter(h['hotspot_level'] for h in hotspots)}", file=sys.stderr)
print(f"\nTop SEVERE hotspots (no FK coverage):", file=sys.stderr)
for h in [x for x in hotspots if x['hotspot_level'] == 'SEVERE'][:10]:
    print(f"  {h['shared_column']}: {h['tables_sharing']} tables, 0 FK links", file=sys.stderr)

print(f"\nWrote {OUT_CLUSTERS}", file=sys.stderr)
print(f"Wrote {OUT_ISOLATED}", file=sys.stderr)
print(f"Wrote {OUT_HOTSPOTS}", file=sys.stderr)
