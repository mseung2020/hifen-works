"""
Step 3.5: Boost pass — catch two known blind spots from Steps 1-3.

1) Dynamic table names: `f"YT_bumper_crawl_video_list_{country}"` would evade
   exact-name matching.  For each UNUSED table we derive a candidate prefix
   (strip the last `_<tail>` segment) and look for that prefix + `_` appearing
   in f-strings or string-concat/format contexts.  Promote such tables to
   USED_DYNAMIC.

2) Generic-word tables (e.g., `brand`, `users`, `keywords`) produce consumer-app
   false positives from column names and variables.  For each consumer hit, we
   require a stronger SQL context signal within ~200 chars (SELECT/.raw/
   cursor.execute/triple-quoted SQL marker).

Inputs:
  - hifen_scheme_table_usage_final.csv
  - table_to_apps.csv
Outputs:
  - hifen_scheme_table_usage_final_boosted.csv
  - table_to_apps_boosted.csv
  - boost_report.md (human-readable delta summary)
"""
from __future__ import annotations
import csv, os, re, sys, json
from collections import defaultdict, Counter

ROOT = "/Users/rachel/Documents/김명승 작업실/ugwanggiAPI-main"
BRANCH = os.path.join(ROOT, "ugwanggiAPI-main")
IN_FINAL = os.path.join(ROOT, "hifen_scheme_table_usage_final.csv")
IN_T2A = os.path.join(ROOT, "table_to_apps.csv")
OUT_FINAL = os.path.join(ROOT, "hifen_scheme_table_usage_final_boosted.csv")
OUT_T2A = os.path.join(ROOT, "table_to_apps_boosted.csv")
OUT_REPORT = os.path.join(ROOT, "boost_report.md")

# --- Load branch files ---
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

# --- Load Step 2 final + Step 3 mapping ---
final_rows: list[dict] = []
with open(IN_FINAL, newline='', encoding='utf-8') as f:
    final_rows = list(csv.DictReader(f))
t2a_rows: list[dict] = []
with open(IN_T2A, newline='', encoding='utf-8') as f:
    t2a_rows = list(csv.DictReader(f))
t2a_by_table = {r['table']: r for r in t2a_rows}
used_names = {r['table'] for r in final_rows if r['usage_final'] == 'USED'}

# ==========================================================================
# Boost 1: dynamic-name detection
# ==========================================================================
# For each UNUSED table, derive prefix by stripping last `_<tail>` segment.
# If prefix contains nothing (no underscore), skip.
# Look for pattern  <prefix>_  that appears right before a formatting token:
#   f"<prefix>_{...}"
#   "<prefix>_" + var
#   "<prefix>_%s"
#   "<prefix>_{}".format(...)
DYNAMIC_CONTEXTS = [
    r'f["\']{prefix}_\{{',          # f"prefix_{...
    r'["\']{prefix}_["\']\s*\+',     # "prefix_" +
    r'["\']{prefix}_%s',             # "prefix_%s"
    r'["\']{prefix}_\{{\}}',         # "prefix_{}"
    r'["\']{prefix}_["\']\s*\.format', # "prefix_".format
]

def looks_dynamically_constructed(prefix: str) -> tuple[bool, str]:
    esc = re.escape(prefix)
    for pat_tpl in DYNAMIC_CONTEXTS:
        pat = re.compile(pat_tpl.format(prefix=esc))
        for p, text in all_files:
            m = pat.search(text)
            if m:
                return True, f"{os.path.relpath(p, BRANCH)} ← {pat_tpl}"
    return False, ''

dynamic_promotions: list[tuple[str, str]] = []  # (table, evidence)
for r in final_rows:
    if r['usage_final'] != 'UNUSED':
        continue
    t = r['table']
    if '_' not in t:
        continue
    prefix = t.rsplit('_', 1)[0]
    if len(prefix) < 3:  # too short = too noisy
        continue
    hit, evidence = looks_dynamically_constructed(prefix)
    if hit:
        dynamic_promotions.append((t, evidence))

promoted_set = {t for t, _ in dynamic_promotions}
print(f"Dynamic-name promotions: {len(dynamic_promotions)}", file=sys.stderr)
for t, ev in dynamic_promotions[:10]:
    print(f"  {t}  <- {ev}", file=sys.stderr)

# ==========================================================================
# Boost 2: generic-word consumer re-verification
# ==========================================================================
# Heuristic for "generic": single lowercase word, <=12 chars, no digits.
def is_generic(name: str) -> bool:
    return (re.match(r'^[a-z][a-z_]{0,11}$', name) is not None
            and name.count('_') <= 1
            and len(name) <= 12)

# Stronger SQL signal within ~200 chars
STRONG_SQL_RX = re.compile(
    r'(SELECT\s|cursor\.execute|\.raw\(|connection\.cursor|"""\s*SELECT|\'\'\'\s*SELECT|INSERT\s+INTO|UPDATE\s+\w|DELETE\s+FROM)',
    re.IGNORECASE,
)

def verify_consumer(table: str, app: str) -> tuple[bool, int]:
    """Check if this app really references `table` within a strong SQL context."""
    esc = re.escape(table)
    ref_rx = re.compile(
        r'\b(FROM|JOIN|INSERT\s+INTO|UPDATE|DELETE\s+FROM)\s+`?' + esc + r'`?\b',
        re.IGNORECASE,
    )
    app_root_norm = os.path.join(BRANCH, app) + os.sep
    strong_hits = 0
    for p, text in all_files:
        if not p.startswith(app_root_norm):
            continue
        for m in ref_rx.finditer(text):
            lo = max(0, m.start() - 200)
            hi = min(len(text), m.end() + 200)
            if STRONG_SQL_RX.search(text[lo:hi]):
                strong_hits += 1
    return (strong_hits > 0, strong_hits)

generic_tables = [r['table'] for r in t2a_rows if is_generic(r['table'])]
print(f"Generic-word tables flagged for re-verification: {len(generic_tables)}", file=sys.stderr)
print(f"  {generic_tables}", file=sys.stderr)

consumer_changes: list[dict] = []  # for report
t2a_updated: dict[str, dict] = {r['table']: dict(r) for r in t2a_rows}

for t in generic_tables:
    row = t2a_updated[t]
    orig_consumers = row['consumer_apps'].split('|') if row['consumer_apps'] else []
    kept = []
    dropped = []
    for app in orig_consumers:
        if not app: continue
        ok, hits = verify_consumer(t, app)
        if ok:
            kept.append(app)
        else:
            dropped.append(app)
    if dropped:
        consumer_changes.append({'table': t, 'kept': kept, 'dropped': dropped})
        # Also tighten writer/reader/join lists to the verified set
        new_set = set(kept)
        row['consumer_apps'] = '|'.join(sorted(new_set))
        for k in ('writer_apps', 'reader_apps', 'join_apps'):
            orig = row[k].split('|') if row[k] else []
            owner_apps = row['owner_app'].split('|') if row['owner_app'] else []
            row[k] = '|'.join(sorted(set(a for a in orig if a in new_set or a in owner_apps)))

# ==========================================================================
# Write outputs
# ==========================================================================
# Boosted final-usage CSV
with open(OUT_FINAL, 'w', newline='', encoding='utf-8') as f:
    fieldnames = list(final_rows[0].keys()) + ['boosted_usage', 'boost_note']
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for r in final_rows:
        r2 = dict(r)
        if r['table'] in promoted_set:
            r2['boosted_usage'] = 'USED'
            r2['boost_note'] = 'promoted via dynamic-name detection'
        else:
            r2['boosted_usage'] = r['usage_final']
            r2['boost_note'] = ''
        w.writerow(r2)

with open(OUT_T2A, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(t2a_rows[0].keys()))
    w.writeheader()
    for t in [row['table'] for row in t2a_rows]:
        w.writerow(t2a_updated[t])

# Human-readable report
lines = []
lines.append("# Step 3.5 Boost Report\n")
lines.append(f"## Boost 1 — Dynamic-name promotions: {len(dynamic_promotions)}\n")
if dynamic_promotions:
    lines.append("| table | evidence |")
    lines.append("|---|---|")
    for t, ev in dynamic_promotions:
        lines.append(f"| {t} | {ev} |")
else:
    lines.append("_No dynamic-name patterns found._\n")
lines.append(f"\n## Boost 2 — Generic-word consumer re-verification: {len(consumer_changes)} tables revised\n")
if consumer_changes:
    lines.append("| table | kept consumers | dropped (likely false positives) |")
    lines.append("|---|---|---|")
    for c in consumer_changes:
        lines.append(f"| {c['table']} | {', '.join(c['kept']) or '—'} | {', '.join(c['dropped'])} |")
else:
    lines.append("_No consumer adjustments needed._\n")

# Updated binary counts
new_used = sum(1 for r in final_rows if r['table'] in promoted_set) + sum(1 for r in final_rows if r['usage_final'] == 'USED')
new_unused = len(final_rows) - new_used
lines.append(f"\n## Final counts after boost\n- USED: {new_used}\n- UNUSED: {new_unused}\n")

with open(OUT_REPORT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print(f"Wrote {OUT_FINAL}", file=sys.stderr)
print(f"Wrote {OUT_T2A}", file=sys.stderr)
print(f"Wrote {OUT_REPORT}", file=sys.stderr)
print(f"Post-boost: USED={new_used}, UNUSED={new_unused}", file=sys.stderr)
