"""
Step 3: Map USED tables to Django apps.

For each USED table (usage_final=USED in Step 2 output), determine:
  - owner_app: the app that defines the Django model (`db_table="T"` inside
      that app's models.py / models/*.py).  If multiple apps define the same
      db_table, list all (flagged as MULTI_OWNER).
  - writer_apps: apps whose code runs INSERT/UPDATE/DELETE against the table.
  - reader_apps: apps whose code contains SELECT/FROM/.objects/JOIN references.
  - consumer_apps: writer_apps ∪ reader_apps minus owner_app.
  - total_hits_by_app: JSON-ish string {app: n} for transparency.

Also emit inverse: for each app, which tables it owns vs consumes.

Outputs:
  - table_to_apps.csv
  - app_to_tables.csv
"""
from __future__ import annotations
import csv, os, re, sys, json
from collections import defaultdict, Counter

ROOT = "/Users/rachel/Documents/김명승 작업실/ugwanggiAPI-main"
BRANCH = os.path.join(ROOT, "ugwanggiAPI-main")
FINAL_CSV = os.path.join(ROOT, "hifen_scheme_table_usage_final.csv")
OUT_T2A = os.path.join(ROOT, "table_to_apps.csv")
OUT_A2T = os.path.join(ROOT, "app_to_tables.csv")

# Only these are actual Django apps (exclude templates, top-level project pkg)
APPS = [
    'admin','ads','aichat','aitools','amore','archive','brand','creators_insights',
    'express','instagram','instagram_admin','keywords','kpi','monitoring',
    'oliveyoung','partner','partner_admin','partner_instagram','preview','search',
    'subscribe','survey','tiktok','trends','ugwanggiAPI','user','youtube','youtube_shopping',
]

# Load USED tables
used_tables: list[str] = []
with open(FINAL_CSV, newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r['usage_final'] == 'USED':
            used_tables.append(r['table'])
print(f"USED tables: {len(used_tables)}", file=sys.stderr)

# Index files by app
app_files: dict[str, list[tuple[str, str]]] = defaultdict(list)
for app in APPS:
    app_root = os.path.join(BRANCH, app)
    if not os.path.isdir(app_root): continue
    for dp, dns, fns in os.walk(app_root):
        dns[:] = [d for d in dns if d not in ('__pycache__', '.git', 'node_modules')]
        for fn in fns:
            if fn.endswith('.py') or fn.endswith('.sql') or fn.endswith('.txt'):
                p = os.path.join(dp, fn)
                try:
                    with open(p, 'r', encoding='utf-8', errors='ignore') as fh:
                        app_files[app].append((p, fh.read()))
                except Exception:
                    pass

total_files = sum(len(v) for v in app_files.values())
print(f"Indexed {total_files} files across {len(app_files)} apps", file=sys.stderr)

# Pre-compile per-table patterns
def analyze(table: str):
    esc = re.escape(table)
    owner_pat = re.compile(r'db_table\s*=\s*["\']' + esc + r'["\']')
    write_pat = re.compile(
        r'\b(INSERT\s+INTO|UPDATE|DELETE\s+FROM)\s+`?' + esc + r'`?\b',
        re.IGNORECASE,
    )
    read_from_pat = re.compile(r'\bFROM\s+`?' + esc + r'`?\b', re.IGNORECASE)
    join_pat = re.compile(r'\bJOIN\s+`?' + esc + r'`?\b', re.IGNORECASE)
    # ORM write: Model.objects.create / save / update / delete — we can't bind
    # to a specific db_table from code alone; the owner_pat captures ownership.

    owner_apps: list[str] = []
    writer_apps: set[str] = set()
    reader_apps: set[str] = set()
    join_apps: set[str] = set()
    per_app_hits: dict[str, int] = {}

    for app, files in app_files.items():
        hits = 0
        for p, text in files:
            if owner_pat.search(text):
                if app not in owner_apps:
                    owner_apps.append(app)
                hits += 1
            if write_pat.search(text):
                writer_apps.add(app)
                hits += 1
            if read_from_pat.search(text):
                reader_apps.add(app)
                hits += 1
            if join_pat.search(text):
                join_apps.add(app)
                hits += 1
        if hits:
            per_app_hits[app] = hits

    consumer_apps = (writer_apps | reader_apps | join_apps) - set(owner_apps)
    return {
        'owner_apps': owner_apps,
        'writer_apps': sorted(writer_apps),
        'reader_apps': sorted(reader_apps),
        'join_apps': sorted(join_apps),
        'consumer_apps': sorted(consumer_apps),
        'per_app_hits': per_app_hits,
    }

results: dict[str, dict] = {}
for i, t in enumerate(used_tables, 1):
    results[t] = analyze(t)
    if i % 50 == 0:
        print(f"... {i}/{len(used_tables)}", file=sys.stderr)

# Owner stats
no_owner = [t for t, r in results.items() if not r['owner_apps']]
multi_owner = [t for t, r in results.items() if len(r['owner_apps']) > 1]
shared = [t for t, r in results.items() if len(r['consumer_apps']) >= 1]
print(f"no_owner (no db_table= found): {len(no_owner)}", file=sys.stderr)
print(f"multi_owner: {len(multi_owner)}", file=sys.stderr)
print(f"shared across apps (owner + ≥1 consumer): {len(shared)}", file=sys.stderr)

# Write table_to_apps.csv
with open(OUT_T2A, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['table','owner_app','owner_status','writer_apps','reader_apps','join_apps','consumer_apps','per_app_hits'])
    for t in used_tables:
        r = results[t]
        owners = r['owner_apps']
        if not owners:
            owner_app = ''
            owner_status = 'NO_MODEL'  # raw-SQL-only table
        elif len(owners) == 1:
            owner_app = owners[0]
            owner_status = 'SINGLE'
        else:
            owner_app = '|'.join(owners)
            owner_status = 'MULTI_OWNER'
        w.writerow([
            t, owner_app, owner_status,
            '|'.join(r['writer_apps']),
            '|'.join(r['reader_apps']),
            '|'.join(r['join_apps']),
            '|'.join(r['consumer_apps']),
            json.dumps(r['per_app_hits'], ensure_ascii=False),
        ])

# Build inverse: app -> owned / consumed tables
owned_by: dict[str, list[str]] = defaultdict(list)
consumed_by: dict[str, list[str]] = defaultdict(list)
for t, r in results.items():
    for a in r['owner_apps']:
        owned_by[a].append(t)
    for a in r['consumer_apps']:
        consumed_by[a].append(t)

with open(OUT_A2T, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['app','owned_count','consumed_count','owned_tables','consumed_tables'])
    all_apps = sorted(set(list(owned_by.keys()) + list(consumed_by.keys())))
    for a in all_apps:
        ow = sorted(owned_by.get(a, []))
        co = sorted(consumed_by.get(a, []))
        w.writerow([a, len(ow), len(co), '|'.join(ow), '|'.join(co)])

print(f"Wrote {OUT_T2A}", file=sys.stderr)
print(f"Wrote {OUT_A2T}", file=sys.stderr)

# Quick top-owners print
top = Counter({a: len(v) for a, v in owned_by.items()}).most_common(10)
print("Top owners:", top, file=sys.stderr)
