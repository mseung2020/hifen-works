"""
Step 4.5 (extension): Naming-based domain clusters.

Complements FK-based clusters by grouping tables by common name prefix/stem.
Compares naming clusters against FK clusters to surface domains where FK
coverage is weak (= denormalization within the domain).

Inputs:
  - hifen_scheme_table_usage_final_boosted.csv  (USED tables)
  - table_edges_unified.csv                     (FK + SQL_JOIN edges)
  - normalization_clusters.csv                  (FK components)

Outputs:
  - naming_clusters.csv: prefix -> member tables, FK internal coverage %
  - domain_vs_fk_gap.csv: domains where naming says "same family" but
                          FK graph doesn't connect them → denorm candidates
"""
from __future__ import annotations
import csv, os, re, sys
from collections import defaultdict

ROOT = "/Users/rachel/Documents/김명승 작업실/ugwanggiAPI-main"
FINAL = os.path.join(ROOT, "hifen_scheme_table_usage_final_boosted.csv")
EDGES = os.path.join(ROOT, "table_edges_unified.csv")

OUT_NAMES = os.path.join(ROOT, "naming_clusters.csv")
OUT_GAP = os.path.join(ROOT, "domain_vs_fk_gap.csv")

used: list[str] = []
with open(FINAL, newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r.get('boosted_usage') == 'USED':
            used.append(r['table'])

adj: dict[str, set[str]] = defaultdict(set)
with open(EDGES, newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        a, b = r['table_a'], r['table_b']
        if a == b: continue
        adj[a].add(b); adj[b].add(a)

# --- Derive "domain prefix" for each table ---
# Rule (tuned for this schema):
#  - If name starts with 'YT_' -> prefix = 'YT_' + next token
#      (e.g., YT_bumper_ad  -> 'YT_bumper'; YT_comment_analysis -> 'YT_comment')
#  - Else take the first underscore-separated token as the coarse domain,
#      but also compute a 2-token finer domain (e.g., 'instagram_post')
#  - Tables with no underscore -> prefix = themselves
def coarse_prefix(t: str) -> str:
    if t.startswith('YT_'):
        parts = t.split('_')
        if len(parts) >= 2:
            return '_'.join(parts[:2])  # 'YT_bumper'
        return t
    parts = t.split('_')
    return parts[0] if parts[0] else t

def fine_prefix(t: str) -> str:
    if t.startswith('YT_'):
        parts = t.split('_')
        return '_'.join(parts[:3]) if len(parts) >= 3 else '_'.join(parts[:2])
    parts = t.split('_')
    return '_'.join(parts[:2]) if len(parts) >= 2 else parts[0]

coarse_groups: dict[str, list[str]] = defaultdict(list)
fine_groups: dict[str, list[str]] = defaultdict(list)
for t in used:
    coarse_groups[coarse_prefix(t)].append(t)
    fine_groups[fine_prefix(t)].append(t)

def fk_internal_coverage(members: list[str]) -> tuple[int, int]:
    """Count FK-linked pairs among members; return (linked, total_possible)."""
    n = len(members)
    if n < 2: return (0, 0)
    mset = set(members)
    linked = 0
    for i, a in enumerate(members):
        for b in members[i+1:]:
            if b in adj.get(a, set()):
                linked += 1
    return (linked, n * (n - 1) // 2)

# Write naming_clusters.csv (coarse level, size>=2 only)
with open(OUT_NAMES, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['prefix','size','fk_internal_linked','fk_internal_total_possible',
                'fk_internal_coverage','isolated_members_in_cluster','members'])
    rows = []
    for prefix, members in coarse_groups.items():
        if len(members) < 2: continue
        linked, total = fk_internal_coverage(members)
        isolated_in = sum(1 for m in members if not adj.get(m))
        coverage = round(linked / total, 4) if total else 0
        rows.append((prefix, len(members), linked, total, coverage, isolated_in,
                     '|'.join(sorted(members))))
    rows.sort(key=lambda r: -r[1])
    for r in rows:
        w.writerow(r)

# Domain-vs-FK gap: prefixes with size>=3 and coverage <20% → denorm candidates
with open(OUT_GAP, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['prefix','size','fk_coverage','isolated_members','gap_severity','members'])
    gap_rows = []
    for prefix, members in coarse_groups.items():
        if len(members) < 3: continue
        linked, total = fk_internal_coverage(members)
        coverage = linked / total if total else 0
        isolated_in = sum(1 for m in members if not adj.get(m))
        if coverage >= 0.3:
            sev = 'LOW'
        elif coverage >= 0.1:
            sev = 'MEDIUM'
        elif coverage > 0:
            sev = 'HIGH'
        else:
            sev = 'SEVERE'
        gap_rows.append((prefix, len(members), round(coverage, 4), isolated_in, sev,
                         '|'.join(sorted(members))))
    order = {'SEVERE':0,'HIGH':1,'MEDIUM':2,'LOW':3}
    gap_rows.sort(key=lambda r: (order[r[4]], -r[1]))
    for r in gap_rows:
        w.writerow(r)

# Console summary
print(f"USED tables: {len(used)}", file=sys.stderr)
print(f"Coarse naming clusters (size≥2): {sum(1 for m in coarse_groups.values() if len(m)>=2)}", file=sys.stderr)
print(f"\nTop 10 naming clusters by size:", file=sys.stderr)
biggest = sorted(coarse_groups.items(), key=lambda kv: -len(kv[1]))[:10]
for prefix, members in biggest:
    linked, total = fk_internal_coverage(members)
    cov = (linked/total*100) if total else 0
    print(f"  {prefix}  size={len(members)}  FK-coverage={cov:.1f}%", file=sys.stderr)
print(f"\nDomain-vs-FK gap rows written: {len(gap_rows)}", file=sys.stderr)
print(f"Severity breakdown: SEVERE={sum(1 for r in gap_rows if r[4]=='SEVERE')}, "
      f"HIGH={sum(1 for r in gap_rows if r[4]=='HIGH')}, "
      f"MEDIUM={sum(1 for r in gap_rows if r[4]=='MEDIUM')}, "
      f"LOW={sum(1 for r in gap_rows if r[4]=='LOW')}", file=sys.stderr)
print(f"\nWrote {OUT_NAMES}", file=sys.stderr)
print(f"Wrote {OUT_GAP}", file=sys.stderr)
