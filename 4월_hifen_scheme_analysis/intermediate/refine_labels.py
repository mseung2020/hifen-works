"""
Step 2: refine AMBIGUOUS + UNUSED labels from Step 1.

For AMBIGUOUS tables (generic English names that collide with Python identifiers),
re-check whether any mention is in a *DB context* (near SQL keywords or ORM calls).
If yes -> reclassify DIRECT. If no -> NOT_A_DB_REF.

For UNUSED tables, split into sub-categories:
  - ARCHIVE_SUFFIX: name ends with _old/_temp/_test/_2022/_2023/_bak/_backup
  - EXTERNAL_ETL: known external-pipeline tables (SequelizeMeta etc.)
  - MIGRATION_ONLY: appears only in migrations/ files (our Step 1 scan would have
      still labeled these UNUSED because db_table/FROM patterns match, but we
      double-check here using plain mention search restricted to migrations)
  - TRULY_UNUSED: no reference anywhere in branch

Output: hifen_scheme_table_usage_refined.csv
"""
from __future__ import annotations
import csv, os, re, sys

ROOT = "/Users/rachel/Documents/김명승 작업실/ugwanggiAPI-main"
SUMMARY_IN = os.path.join(ROOT, "hifen_scheme_table_usage.csv")
SUMMARY_OUT = os.path.join(ROOT, "hifen_scheme_table_usage_refined.csv")
BRANCH = os.path.join(ROOT, "ugwanggiAPI-main")

# Load files once, split by whether path is inside a migrations dir
non_mig_files: list[tuple[str, str]] = []
mig_files: list[tuple[str, str]] = []
for dirpath, dirnames, filenames in os.walk(BRANCH):
    dirnames[:] = [d for d in dirnames if d not in ('.git', '__pycache__', 'node_modules')]
    is_mig = '/migrations' in dirpath.replace(os.sep, '/')
    for fn in filenames:
        if fn.endswith('.py') or fn.endswith('.sql') or fn.endswith('.txt'):
            p = os.path.join(dirpath, fn)
            try:
                with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                    data = f.read()
                (mig_files if is_mig else non_mig_files).append((p, data))
            except Exception:
                pass

print(f"non-migration files: {len(non_mig_files)}, migration files: {len(mig_files)}", file=sys.stderr)

# DB-context detection: is a mention of <table> near a SQL keyword / ORM call?
# We look for the table name within a 80-char window of these signals.
DB_SIGNALS = re.compile(
    r'\b(SELECT|FROM|JOIN|INSERT\s+INTO|UPDATE|DELETE\s+FROM|db_table|\.objects|Meta)\b',
    re.IGNORECASE,
)

def db_context_hits(name: str, text: str) -> int:
    hits = 0
    pattern = re.compile(r'(?<![A-Za-z0-9_])' + re.escape(name) + r'(?![A-Za-z0-9_])')
    for m in pattern.finditer(text):
        lo = max(0, m.start() - 80)
        hi = min(len(text), m.end() + 80)
        if DB_SIGNALS.search(text[lo:hi]):
            hits += 1
    return hits

def plain_mention(name: str, text: str) -> int:
    pattern = re.compile(r'(?<![A-Za-z0-9_])' + re.escape(name) + r'(?![A-Za-z0-9_])')
    return len(pattern.findall(text))

ARCHIVE_RX = re.compile(r'(_old|_temp|_test|_2022|_2023|_bak|_backup)$', re.IGNORECASE)
EXTERNAL_NAMES = {'SequelizeMeta'}

# Read Step 1 summary
rows: list[dict] = []
with open(SUMMARY_IN, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

refined: list[dict] = []
for r in rows:
    t = r['table']
    usage = r['usage']
    new_usage = usage
    new_conf = r['confidence']
    note = ''

    if usage == 'AMBIGUOUS':
        # Re-scan for DB-context hits across all files
        ctx = 0
        for _, text in non_mig_files + mig_files:
            ctx += db_context_hits(t, text)
        if ctx > 0:
            new_usage = 'DIRECT'
            new_conf = 'MED'  # reclassified, so not as confident as a pure hardcoded match
            note = f'AMBIGUOUS→DIRECT via {ctx} DB-context hits'
        else:
            new_usage = 'NOT_A_DB_REF'
            new_conf = 'HIGH'
            note = 'generic word; all mentions appear outside DB context'
    elif usage == 'UNUSED':
        if t in EXTERNAL_NAMES:
            new_usage = 'EXTERNAL_ETL'
            new_conf = 'HIGH'
            note = 'known external pipeline table'
        elif ARCHIVE_RX.search(t):
            new_usage = 'ARCHIVE_SUFFIX'
            new_conf = 'HIGH'
            note = 'name suffix indicates archive/backup/test'
        else:
            # Check migrations-only mention
            mig_hits = 0
            for _, text in mig_files:
                mig_hits += plain_mention(t, text)
            non_mig_hits = 0
            for _, text in non_mig_files:
                non_mig_hits += plain_mention(t, text)
            if mig_hits > 0 and non_mig_hits == 0:
                new_usage = 'MIGRATION_ONLY'
                new_conf = 'HIGH'
                note = f'found only in migrations ({mig_hits} hits)'
            else:
                new_usage = 'TRULY_UNUSED'
                new_conf = 'MED'  # still just "unused in this branch"
                note = 'no reference found anywhere in branch'

    refined.append({
        **r,
        'usage_refined': new_usage,
        'confidence_refined': new_conf,
        'note': note,
    })

# Write output
with open(SUMMARY_OUT, 'w', newline='', encoding='utf-8') as f:
    fieldnames = list(rows[0].keys()) + ['usage_refined', 'confidence_refined', 'note']
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for r in refined:
        w.writerow(r)

# Print distribution
from collections import Counter
dist = Counter(r['usage_refined'] for r in refined)
print("Refined distribution:", dict(dist), file=sys.stderr)
print(f"Wrote {SUMMARY_OUT}", file=sys.stderr)
