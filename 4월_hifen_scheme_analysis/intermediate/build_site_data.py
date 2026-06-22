"""
Step 8: Build a single HTML-consumable JSON bundle from core_materials/.

Output:
  - core_materials/site_data.json            (primary, pretty=False for size)
  - core_materials/site_data.pretty.json     (pretty-printed, for inspection)

Schema (top-level keys):
  meta        — counts, apps list, generated_at
  tables      — dict keyed by table name
  apps        — dict keyed by app name
  endpoints   — list
  edges       — { table_edges, service_edges, shared_keys }
  clusters    — { normalization_components, isolated_tables,
                  naming_clusters, domain_gaps, denormalization_hotspots }
  diagnostics — { zombie_models, no_model_tables, multi_owner_tables,
                  self_loops }
"""
from __future__ import annotations
import csv, json, os, sys
from datetime import date
from collections import defaultdict

ROOT = "/Users/rachel/Documents/김명승 작업실/ugwanggiAPI-main"
CORE = os.path.join(ROOT, "core_materials")

def load(name):
    with open(os.path.join(CORE, name), newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

schema_rows = load("hifen_scheme.csv")
usage_rows = load("hifen_scheme_table_usage_final_boosted.csv")
t2a_rows = load("table_to_apps_boosted.csv")
a2t_rows = load("app_to_tables.csv")
fk_rows = load("model_fks.csv")
edge_rows = load("table_edges_unified.csv")
shared_rows = load("candidate_shared_keys.csv")
cluster_rows = load("normalization_clusters.csv")
isolated_rows = load("isolated_tables.csv")
hotspot_rows = load("denormalization_hotspots.csv")
naming_rows = load("naming_clusters.csv")
gap_rows = load("domain_vs_fk_gap.csv")
ep_rows = load("api_endpoints.csv")
ep_usage_rows = load("endpoint_usage.csv")
svc_edge_rows = load("service_edges.csv")
svc_sum_rows = load("service_summary.csv")

APPS = sorted(set(r['app'] for r in a2t_rows) | set(r['app'] for r in svc_sum_rows))

# ----- Build per-table columns from schema CSV -----
# Header in hifen_scheme.csv (Korean):
# 테이블명, 테이블 설명, 컬럼명, 데이터 타입, Null 허용, Key (PK/FK), 기본값, 추가 속성, 컬럼 설명
def col_from_row(row):
    vals = list(row.values())
    # defensive index
    return {
        'name': vals[2].strip() if len(vals) > 2 else '',
        'type': vals[3].strip() if len(vals) > 3 else '',
        'nullable': (vals[4].strip().upper() == 'YES') if len(vals) > 4 else None,
        'key': vals[5].strip() if len(vals) > 5 else '',
        'default': vals[6].strip() if len(vals) > 6 else '',
        'extra': vals[7].strip() if len(vals) > 7 else '',
        'comment': vals[8].strip() if len(vals) > 8 else '',
    }

table_columns = defaultdict(list)
table_description = {}
for row in schema_rows:
    vals = list(row.values())
    tname = vals[0].strip() if vals else ''
    if not tname: continue
    if vals[1].strip():  # description only present on first row per table
        table_description.setdefault(tname, vals[1].strip())
    c = col_from_row(row)
    if c['name']:
        table_columns[tname].append(c)

# ----- Pre-index cluster membership -----
cluster_by_table = {}
for r in cluster_rows:
    for t in r['member_tables'].split('|'):
        cluster_by_table[t] = {
            'id': r['cluster_id'], 'size': int(r['size']),
            'hub_table': r['hub_table'], 'hub_degree': int(r['hub_degree']),
        }

isolated_set = set(r['table'] for r in isolated_rows)
isolated_note = {r['table']: r['note'] for r in isolated_rows}

def domain_prefix(t):
    if t.startswith('YT_'):
        parts = t.split('_')
        if len(parts) >= 2: return '_'.join(parts[:2])
    return t.split('_')[0] if '_' in t else t

# ----- Index FKs per table -----
outgoing = defaultdict(list)
incoming = defaultdict(list)
for r in fk_rows:
    from_t, to_t = r['from_table'], r['to_table']
    entry = {
        'from_table': from_t, 'to_table': to_t,
        'from_column': r['from_column'], 'to_column': r['to_column'],
        'relation_type': r['relation_type'], 'from_app': r['from_app'],
        'from_model': r['from_model'], 'to_model': r['to_model'],
        'on_delete': r['on_delete'],
        'null': r['null'] == 'True',
        'file': r['file'],
    }
    outgoing[from_t].append(entry)
    incoming[to_t].append(entry)

# ----- Index edges per table (from unified edges) -----
edge_by_table = defaultdict(list)
for r in edge_rows:
    a, b = r['table_a'], r['table_b']
    entry = {
        'partner': None, 'sources': r['sources'].split('|'),
        'confidence': r['confidence'], 'direction': r['direction'],
        'column_a_to_b': r['column_a_to_b'], 'relation_type': r['relation_type'],
        'cols_verified': r['cols_verified'] == 'True',
        'evidence': r['evidence'],
    }
    e_a = dict(entry); e_a['partner'] = b
    e_b = dict(entry); e_b['partner'] = a
    edge_by_table[a].append(e_a)
    edge_by_table[b].append(e_b)

# ----- Index shared keys per table -----
shared_by_table = defaultdict(list)
for r in shared_rows:
    col = r['shared_column']
    tbls = [t for t in r['tables'].split('|') if t]
    for t in tbls:
        shared_by_table[t].append({'column': col, 'co_tables_count': int(r['table_count'])})

# ----- Build tables dict -----
# From usage CSV: authoritative list
tables = {}
for r in usage_rows:
    t = r['table']
    tables[t] = {
        'name': t,
        'description': table_description.get(t, ''),
        'usage': r['usage_final'],
        'boosted_usage': r.get('boosted_usage', r['usage_final']),
        'subcategory': r['subcategory'],
        'confidence': r['confidence_final'],
        'direct_hits': int(r['direct_hits']),
        'indirect_hits': int(r['indirect_hits']),
        'mention_hits': int(r['mention_hits']),
        'note': r['note'],
        'domain_prefix': domain_prefix(t),
        'columns': table_columns.get(t, []),
        'pk_columns': [c['name'] for c in table_columns.get(t, []) if c['key'] == 'PRI'],
        'owner_app': None,
        'owner_status': None,
        'writer_apps': [], 'reader_apps': [], 'join_apps': [], 'consumer_apps': [],
        'per_app_hits': {},
        'is_isolated': t in isolated_set,
        'isolated_note': isolated_note.get(t, ''),
        'cluster': cluster_by_table.get(t),
        'outgoing_fks': outgoing.get(t, []),
        'incoming_fks': incoming.get(t, []),
        'edges': edge_by_table.get(t, []),
        'shared_keys': shared_by_table.get(t, []),
    }

# Merge in app mapping
for r in t2a_rows:
    t = r['table']
    if t not in tables: continue
    tables[t]['owner_app'] = r['owner_app']
    tables[t]['owner_status'] = r['owner_status']
    tables[t]['writer_apps'] = [a for a in r['writer_apps'].split('|') if a]
    tables[t]['reader_apps'] = [a for a in r['reader_apps'].split('|') if a]
    tables[t]['join_apps'] = [a for a in r['join_apps'].split('|') if a]
    tables[t]['consumer_apps'] = [a for a in r['consumer_apps'].split('|') if a]
    try:
        tables[t]['per_app_hits'] = json.loads(r['per_app_hits']) if r['per_app_hits'] else {}
    except Exception:
        tables[t]['per_app_hits'] = {}

# ----- Build apps dict -----
# Start from service_summary
apps = {}
for r in svc_sum_rows:
    a = r['app']
    apps[a] = {
        'name': a,
        'owned_tables': [],
        'consumed_tables': [],
        'owned_count': int(r['owned_tables']),
        'consumed_count': int(r['consumed_tables']),
        'endpoints_total': int(r['endpoints_total']),
        'endpoints_uncalled': int(r['endpoints_uncalled']),
        'endpoints_called': int(r['endpoints_total']) - int(r['endpoints_uncalled']),
        'outbound_deps': [],
        'inbound_deps': [],
        'outbound_count': int(r['outbound_deps']),
        'inbound_count': int(r['inbound_deps']),
    }
# Fill owned/consumed tables from a2t
for r in a2t_rows:
    a = r['app']
    if a not in apps:
        apps[a] = {
            'name': a, 'owned_tables': [], 'consumed_tables': [],
            'owned_count': 0, 'consumed_count': 0,
            'endpoints_total': 0, 'endpoints_uncalled': 0, 'endpoints_called': 0,
            'outbound_deps': [], 'inbound_deps': [],
            'outbound_count': 0, 'inbound_count': 0,
        }
    apps[a]['owned_tables'] = [t for t in r['owned_tables'].split('|') if t]
    apps[a]['consumed_tables'] = [t for t in r['consumed_tables'].split('|') if t]

# Attach service edges
for r in svc_edge_rows:
    edge = {
        'from_app': r['from_app'], 'to_app': r['to_app'],
        'weight': int(r['weight']),
        'sources': r['sources'].split('|'),
        'imports_count': int(r['imports_count']),
        'shared_tables_count': int(r['shared_tables_count']),
        'cron_count': int(r['cron_count']),
        'import_samples': [s for s in r['import_samples'].split(' | ') if s],
        'shared_tables': [s for s in r['shared_tables'].split(' | ') if s],
        'cron_samples': [s for s in r['cron_samples'].split(' | ') if s],
    }
    if r['from_app'] in apps:
        apps[r['from_app']]['outbound_deps'].append(edge)
    if r['to_app'] in apps:
        apps[r['to_app']]['inbound_deps'].append(edge)

# Derive health category from uncalled %
for a, info in apps.items():
    t = info['endpoints_total']
    u = info['endpoints_uncalled']
    if t == 0:
        info['health'] = 'no_api'
    else:
        pct = u / t
        if pct == 0: info['health'] = 'healthy'
        elif pct <= 0.2: info['health'] = 'healthy'
        elif pct <= 0.5: info['health'] = 'over_developed'
        else: info['health'] = 'abandoned_or_experimental'
    info['uncalled_pct'] = round((u/t)*100, 1) if t else 0.0

# ----- Build endpoints list (merge api_endpoints + endpoint_usage) -----
usage_by_path_method = {}
for r in ep_usage_rows:
    key = (r['app'], r['http_methods'], r['url_path'])
    usage_by_path_method[key] = r

endpoints = []
for r in ep_rows:
    key = (r['app'], r['http_methods'], r['url_path'])
    u = usage_by_path_method.get(key, {})
    endpoints.append({
        'app': r['app'],
        'http_methods': [m for m in r['http_methods'].split('|') if m],
        'url_path': r['url_path'],
        'norm_path': u.get('norm_path', ''),
        'view_ref': r['view_ref'],
        'view_kind': r['view_kind'],
        'view_file': r['view_file'],
        'tables_touched': [t for t in r['tables_touched'].split('|') if t],
        'usage': u.get('usage', 'UNKNOWN'),
        'match_type': u.get('match_type', ''),
        'confidence': u.get('confidence', ''),
        'frontend_hits': int(u.get('frontend_hits') or 0),
        'evidence_files': [f for f in (u.get('evidence_files') or '').split(' | ') if f],
    })

# ----- Build edges block -----
table_edges = []
for r in edge_rows:
    table_edges.append({
        'table_a': r['table_a'], 'table_b': r['table_b'],
        'sources': r['sources'].split('|'),
        'confidence': r['confidence'], 'direction': r['direction'],
        'column_a_to_b': r['column_a_to_b'], 'relation_type': r['relation_type'],
        'cols_verified': r['cols_verified'] == 'True',
        'evidence': r['evidence'],
    })

service_edges_list = []
for r in svc_edge_rows:
    service_edges_list.append({
        'from_app': r['from_app'], 'to_app': r['to_app'],
        'weight': int(r['weight']),
        'sources': r['sources'].split('|'),
        'imports_count': int(r['imports_count']),
        'shared_tables_count': int(r['shared_tables_count']),
        'cron_count': int(r['cron_count']),
    })

shared_keys_list = []
for r in shared_rows:
    shared_keys_list.append({
        'column': r['shared_column'],
        'table_count': int(r['table_count']),
        'tables': [t for t in r['tables'].split('|') if t],
    })

# ----- Build clusters block -----
normalization_components = []
for r in cluster_rows:
    normalization_components.append({
        'id': r['cluster_id'],
        'size': int(r['size']),
        'hub_table': r['hub_table'],
        'hub_degree': int(r['hub_degree']),
        'members': r['member_tables'].split('|'),
    })

isolated_list = [{'table': r['table'], 'note': r['note']} for r in isolated_rows]

naming_clusters = []
for r in naming_rows:
    naming_clusters.append({
        'prefix': r['prefix'],
        'size': int(r['size']),
        'fk_internal_linked': int(r['fk_internal_linked']),
        'fk_internal_total_possible': int(r['fk_internal_total_possible']),
        'fk_internal_coverage': float(r['fk_internal_coverage']),
        'isolated_members_in_cluster': int(r['isolated_members_in_cluster']),
        'members': r['members'].split('|'),
    })

domain_gaps = []
for r in gap_rows:
    domain_gaps.append({
        'prefix': r['prefix'],
        'size': int(r['size']),
        'fk_coverage': float(r['fk_coverage']),
        'isolated_members': int(r['isolated_members']),
        'gap_severity': r['gap_severity'],
        'members': r['members'].split('|'),
    })

denorm_hotspots = []
for r in hotspot_rows:
    denorm_hotspots.append({
        'shared_column': r['shared_column'],
        'tables_sharing': int(r['tables_sharing']),
        'fk_linked_pairs': int(r['fk_linked_pairs']),
        'total_possible_pairs': int(r['total_possible_pairs']),
        'coverage_ratio': float(r['coverage_ratio']),
        'hotspot_level': r['hotspot_level'],
    })

# ----- Diagnostics -----
# Zombie models: FK source/target tables NOT in schema
schema_table_set = set(table_columns.keys())
zombie = []
for r in fk_rows:
    if r['from_table'] not in schema_table_set:
        zombie.append({'model': r['from_model'], 'declared_table': r['from_table'],
                        'app': r['from_app'], 'file': r['file'], 'direction': 'from'})
    if r['to_table'] not in schema_table_set:
        zombie.append({'model': r['to_model'], 'declared_table': r['to_table'],
                        'app': r['from_app'], 'file': r['file'], 'direction': 'to'})
# dedupe
seen_z = set(); zombie_unique = []
for z in zombie:
    k = (z['model'], z['declared_table'], z['direction'])
    if k in seen_z: continue
    seen_z.add(k); zombie_unique.append(z)

no_model_tables = [r['table'] for r in t2a_rows if r['owner_status'] == 'NO_MODEL']
multi_owner_tables = [
    {'table': r['table'], 'owners': r['owner_app'].split('|')}
    for r in t2a_rows if r['owner_status'] == 'MULTI_OWNER'
]
self_loops = [
    {'table': r['table_a'], 'column': r['column_a_to_b'], 'evidence': r['evidence']}
    for r in edge_rows if r['table_a'] == r['table_b']
]

# ----- Meta -----
meta = {
    'generated_at': str(date.today()),
    'total_schema_tables': len(schema_table_set),
    'used_tables': sum(1 for r in usage_rows if r['usage_final'] == 'USED'),
    'unused_tables': sum(1 for r in usage_rows if r['usage_final'] == 'UNUSED'),
    'total_endpoints': len(endpoints),
    'called_endpoints': sum(1 for e in endpoints if e['usage'] == 'CALLED'),
    'uncalled_endpoints': sum(1 for e in endpoints if e['usage'] == 'UNCALLED'),
    'total_table_edges': len(table_edges),
    'total_service_edges': len(service_edges_list),
    'apps': sorted(apps.keys()),
    'app_count': len(apps),
    'source_trees': {
        'backend': 'ugwanggiAPI-main',
        'frontend': 'ugwanggiNext-main',
    },
    'closed_world_assumption': True,
    'notes': 'Generated from core_materials/ CSVs. Closed world: this backend + this frontend + this schema are the only artifacts.',
}

bundle = {
    'meta': meta,
    'tables': tables,
    'apps': apps,
    'endpoints': endpoints,
    'edges': {
        'table_edges': table_edges,
        'service_edges': service_edges_list,
        'shared_keys': shared_keys_list,
    },
    'clusters': {
        'normalization_components': normalization_components,
        'isolated_tables': isolated_list,
        'naming_clusters': naming_clusters,
        'domain_gaps': domain_gaps,
        'denormalization_hotspots': denorm_hotspots,
    },
    'diagnostics': {
        'zombie_models': zombie_unique,
        'no_model_tables': no_model_tables,
        'multi_owner_tables': multi_owner_tables,
        'self_loops': self_loops,
    },
}

compact_path = os.path.join(CORE, 'site_data.json')
pretty_path = os.path.join(CORE, 'site_data.pretty.json')
with open(compact_path, 'w', encoding='utf-8') as f:
    json.dump(bundle, f, ensure_ascii=False, separators=(',', ':'))
with open(pretty_path, 'w', encoding='utf-8') as f:
    json.dump(bundle, f, ensure_ascii=False, indent=2)

size_c = os.path.getsize(compact_path)
size_p = os.path.getsize(pretty_path)
print(f"Tables: {len(tables)}, Apps: {len(apps)}, Endpoints: {len(endpoints)}", file=sys.stderr)
print(f"Table edges: {len(table_edges)}, Service edges: {len(service_edges_list)}", file=sys.stderr)
print(f"Zombie models: {len(zombie_unique)}, NO_MODEL tables: {len(no_model_tables)}, MULTI_OWNER: {len(multi_owner_tables)}, Self-loops: {len(self_loops)}", file=sys.stderr)
print(f"Compact JSON: {size_c/1024:.1f} KB", file=sys.stderr)
print(f"Pretty JSON: {size_p/1024:.1f} KB", file=sys.stderr)
print(f"Wrote {compact_path}", file=sys.stderr)
print(f"Wrote {pretty_path}", file=sys.stderr)
