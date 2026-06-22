"""
Step 2 final: given the closed-world assumption (this branch is the only consumer
and hifen is the only schema), collapse the refined labels into a binary
USED/UNUSED view with HIGH confidence, while preserving the sub-category.
"""
import csv, os, sys
from collections import Counter

ROOT = "/Users/rachel/Documents/김명승 작업실/ugwanggiAPI-main"
IN_CSV = os.path.join(ROOT, "hifen_scheme_table_usage_refined.csv")
OUT_CSV = os.path.join(ROOT, "hifen_scheme_table_usage_final.csv")

USED_LABELS = {'DIRECT'}  # INDIRECT was 0 in Step 1
UNUSED_LABELS = {'TRULY_UNUSED', 'ARCHIVE_SUFFIX', 'EXTERNAL_ETL', 'NOT_A_DB_REF', 'MIGRATION_ONLY'}

rows = []
with open(IN_CSV, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        rows.append(r)

out_rows = []
for r in rows:
    ur = r['usage_refined']
    if ur in USED_LABELS:
        final = 'USED'
        conf = 'HIGH'
        sub = ur  # DIRECT
    elif ur in UNUSED_LABELS:
        final = 'UNUSED'
        conf = 'HIGH'  # closed-world: no external consumer possible
        sub = ur
    else:
        final = 'UNKNOWN'
        conf = 'LOW'
        sub = ur
    out_rows.append({
        'table': r['table'],
        'usage_final': final,
        'subcategory': sub,
        'confidence_final': conf,
        'direct_hits': r['direct_hits'],
        'indirect_hits': r['indirect_hits'],
        'mention_hits': r['mention_hits'],
        'sample_files': r['sample_files'],
        'note': r.get('note', ''),
    })

with open(OUT_CSV, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
    w.writeheader()
    w.writerows(out_rows)

dist_final = Counter(r['usage_final'] for r in out_rows)
dist_sub = Counter(r['subcategory'] for r in out_rows)
print(f"Final binary: {dict(dist_final)}", file=sys.stderr)
print(f"Subcategories: {dict(dist_sub)}", file=sys.stderr)
print(f"Wrote {OUT_CSV}", file=sys.stderr)
