"""
Step 7.5: Reliability audit of all core_materials/ files.

Runs cross-file integrity checks and sanity checks; reports CRITICAL / WARNING /
INFO findings.  Does NOT modify data.
"""
import csv, os, sys
from collections import Counter, defaultdict

ROOT = "/Users/rachel/Documents/김명승 작업실/ugwanggiAPI-main"
CORE = os.path.join(ROOT, "core_materials")

def load_csv(name):
    with open(os.path.join(CORE, name), newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

schema = load_csv("hifen_scheme.csv")
usage = load_csv("hifen_scheme_table_usage_final_boosted.csv")
t2a = load_csv("table_to_apps_boosted.csv")
a2t = load_csv("app_to_tables.csv")
fks = load_csv("model_fks.csv")
edges = load_csv("table_edges_unified.csv")
shared = load_csv("candidate_shared_keys.csv")
clusters = load_csv("normalization_clusters.csv")
isolated = load_csv("isolated_tables.csv")
hotspots = load_csv("denormalization_hotspots.csv")
naming = load_csv("naming_clusters.csv")
domain_gap = load_csv("domain_vs_fk_gap.csv")
endpoints = load_csv("api_endpoints.csv")
ep_usage = load_csv("endpoint_usage.csv")
svc_edges = load_csv("service_edges.csv")
svc_summary = load_csv("service_summary.csv")

findings = []

def add(level, msg):
    findings.append((level, msg))

# ----- derive canonical sets -----
schema_tables = set(r['테이블명'].strip() for r in schema if r.get('테이블명')) if schema[0].get('테이블명') else set(r[list(r.keys())[0]].strip() for r in schema)
# Actually hifen_scheme.csv has Korean header "테이블명" as first col
# Fall back:
schema_tables = set()
for r in schema:
    v = list(r.values())[0]
    if v: schema_tables.add(v.strip())
schema_tables.discard('')

used = set(r['table'] for r in usage if r['boosted_usage'] == 'USED')
unused = set(r['table'] for r in usage if r['boosted_usage'] == 'UNUSED')
all_tables = used | unused

# ===== CHECK 1: usage file covers every table in schema =====
if all_tables != schema_tables:
    only_schema = schema_tables - all_tables
    only_usage = all_tables - schema_tables
    if only_schema:
        add('WARNING', f"{len(only_schema)} schema tables missing from usage CSV (sample: {list(only_schema)[:5]})")
    if only_usage:
        add('CRITICAL', f"{len(only_usage)} usage rows reference tables not in schema (sample: {list(only_usage)[:5]})")
else:
    add('INFO', f"usage CSV covers all {len(schema_tables)} schema tables ✓")

# ===== CHECK 2: USED/UNUSED sum = total =====
if len(used) + len(unused) != len(all_tables):
    add('CRITICAL', f"USED+UNUSED mismatch: {len(used)} + {len(unused)} ≠ {len(all_tables)}")
else:
    add('INFO', f"USED ({len(used)}) + UNUSED ({len(unused)}) = {len(all_tables)} ✓")

# ===== CHECK 3: table_to_apps only contains USED tables =====
t2a_tables = set(r['table'] for r in t2a)
bad_t2a = t2a_tables - used
if bad_t2a:
    add('CRITICAL', f"table_to_apps contains {len(bad_t2a)} non-USED tables: {list(bad_t2a)[:5]}")
if used - t2a_tables:
    missing = used - t2a_tables
    add('WARNING', f"{len(missing)} USED tables missing from table_to_apps: {list(missing)[:5]}")
else:
    add('INFO', f"table_to_apps covers all {len(used)} USED tables ✓")

# ===== CHECK 4: every edge endpoint is a USED table =====
bad_edges = [r for r in edges if r['table_a'] not in used or r['table_b'] not in used]
if bad_edges:
    add('CRITICAL', f"{len(bad_edges)} edges reference non-USED tables (sample: {bad_edges[0]})")
else:
    add('INFO', f"all {len(edges)} edges use USED tables on both ends ✓")

# ===== CHECK 5: self-loop edges =====
self_loops = [r for r in edges if r['table_a'] == r['table_b']]
if self_loops:
    add('WARNING', f"{len(self_loops)} self-loop edges present (may be intended for hierarchical models)")

# ===== CHECK 6: FK endpoints USED =====
fk_bad_src = [r for r in fks if r['from_table_used'] != 'True']
fk_bad_dst = [r for r in fks if r['to_table_used'] != 'True']
if fk_bad_src:
    add('WARNING', f"{len(fk_bad_src)} FKs originate from UNUSED tables")
if fk_bad_dst:
    add('WARNING', f"{len(fk_bad_dst)} FKs target UNUSED tables")
unverified = [r for r in fks if r['from_col_in_schema']=='False' or r['to_col_in_schema']=='False']
add('INFO', f"FKs with unverified columns in schema: {len(unverified)}/{len(fks)}")

# ===== CHECK 7: edge confidence distribution =====
conf_dist = Counter(r['confidence'] for r in edges)
add('INFO', f"edge confidence: {dict(conf_dist)}")

# ===== CHECK 8: API endpoints vs endpoint_usage counts match =====
if len(endpoints) != len(ep_usage):
    add('CRITICAL', f"api_endpoints.csv ({len(endpoints)}) != endpoint_usage.csv ({len(ep_usage)})")
else:
    add('INFO', f"api_endpoints and endpoint_usage both have {len(endpoints)} rows ✓")

# ===== CHECK 9: endpoint apps are valid Django apps =====
VALID_APPS = set([
    'admin','ads','aichat','aitools','amore','archive','brand','creators_insights',
    'express','instagram','instagram_admin','keywords','kpi','monitoring',
    'oliveyoung','partner','partner_admin','partner_instagram','preview','search',
    'subscribe','survey','tiktok','trends','ugwanggiAPI','user','youtube','youtube_shopping',
])
bad_apps = set(r['app'] for r in endpoints) - VALID_APPS
if bad_apps:
    add('WARNING', f"endpoint apps not in valid list: {bad_apps}")

# ===== CHECK 10: endpoints touching only USED tables =====
ep_bad = 0
for r in endpoints:
    tbls = [t for t in r['tables_touched'].split('|') if t]
    for t in tbls:
        if t not in used:
            ep_bad += 1
            break
if ep_bad:
    add('WARNING', f"{ep_bad} endpoints reference tables NOT in USED set (possible stale refs)")
else:
    add('INFO', f"endpoints only reference USED tables ✓")

# ===== CHECK 11: connected components sanity =====
total_in_clusters = sum(int(r['size']) for r in clusters)
total_iso = len(isolated)
if total_in_clusters + total_iso != len(used):
    add('WARNING', f"cluster sum ({total_in_clusters}) + isolated ({total_iso}) != USED ({len(used)})")
else:
    add('INFO', f"clusters + isolated = USED tables ({len(used)}) ✓")

# ===== CHECK 12: service_edges apps are valid =====
svc_bad = set()
for r in svc_edges:
    if r['from_app'] not in VALID_APPS: svc_bad.add(r['from_app'])
    if r['to_app'] not in VALID_APPS: svc_bad.add(r['to_app'])
if svc_bad:
    add('WARNING', f"service_edges uses unknown apps: {svc_bad}")

# ===== CHECK 13: endpoint CALLED+UNCALLED = total =====
ep_dist = Counter(r['usage'] for r in ep_usage)
if ep_dist.get('CALLED',0) + ep_dist.get('UNCALLED',0) != len(ep_usage):
    add('CRITICAL', f"endpoint usage labels don't sum to total: {dict(ep_dist)}")
else:
    add('INFO', f"endpoint CALLED+UNCALLED = total ({len(ep_usage)}) ✓")

# ===== CHECK 14: owner app consistency — an owned table's owner app shouldn't appear as consumer =====
conflict = 0
for r in t2a:
    owners = set(r['owner_app'].split('|')) - {''}
    consumers = set(r['consumer_apps'].split('|')) - {''}
    if owners & consumers:
        conflict += 1
if conflict:
    add('WARNING', f"{conflict} tables list an owner app also as consumer")
else:
    add('INFO', f"owner/consumer disjoint for all t2a rows ✓")

# ===== CHECK 15: duplicate tables in usage =====
usage_tabs = [r['table'] for r in usage]
if len(usage_tabs) != len(set(usage_tabs)):
    add('CRITICAL', f"duplicate table rows in usage CSV")
else:
    add('INFO', "usage table rows all distinct ✓")

# ===== CHECK 16: svc_summary endpoint totals reconcile =====
total_eps_from_summary = sum(int(r['endpoints_total']) for r in svc_summary)
if total_eps_from_summary != len(endpoints):
    add('WARNING', f"service_summary endpoints_total sum ({total_eps_from_summary}) != endpoints.csv rows ({len(endpoints)})")
else:
    add('INFO', f"service_summary endpoint counts reconcile ({len(endpoints)}) ✓")

# ===== CHECK 17: shared keys referenced tables all USED =====
bad_shared = 0
for r in shared:
    for t in r['tables'].split('|'):
        if t and t not in used:
            bad_shared += 1; break
if bad_shared:
    add('WARNING', f"{bad_shared} shared_key clusters reference non-USED tables")

# ===== CHECK 18: naming clusters contains any orphan =====
for r in naming:
    members = r['members'].split('|')
    for m in members:
        if m not in used:
            add('WARNING', f"naming cluster '{r['prefix']}' has non-USED member '{m}'")
            break

# ===== Print =====
counts = Counter(l for l,_ in findings)
print(f"=== Audit finished: "
      f"CRITICAL={counts.get('CRITICAL',0)}, "
      f"WARNING={counts.get('WARNING',0)}, "
      f"INFO={counts.get('INFO',0)} ===\n")
for level in ('CRITICAL', 'WARNING', 'INFO'):
    rows = [m for l,m in findings if l == level]
    if not rows: continue
    print(f"--- {level} ({len(rows)}) ---")
    for m in rows: print(f"  {m}")
    print()
