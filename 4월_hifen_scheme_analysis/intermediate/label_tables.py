"""
Label each table in hifen_scheme.csv with usage status within the ugwanggiAPI branch.

Adds columns:
  - usage: DIRECT / INDIRECT / UNUSED / AMBIGUOUS
  - confidence: HIGH / MED / LOW
  - direct_hits: count of direct signals (db_table=, FROM, INSERT/UPDATE/DELETE)
  - indirect_hits: count of JOIN-only signals
  - sample_files: up to 3 example file paths

Only rows whose table name changes get the labels; all other rows (same table
repeated across columns) inherit blank cells for usage (still the same table).
We write labels only on the first-occurrence row per table to keep the CSV
readable, but also output a separate summary CSV.
"""
from __future__ import annotations
import csv, os, re, sys
from collections import defaultdict

ROOT = "/Users/rachel/Documents/김명승 작업실/ugwanggiAPI-main"
CSV_IN = os.path.join(ROOT, "hifen_scheme.csv")
CSV_OUT = os.path.join(ROOT, "hifen_scheme_labeled.csv")
SUMMARY_OUT = os.path.join(ROOT, "hifen_scheme_table_usage.csv")
BRANCH = os.path.join(ROOT, "ugwanggiAPI-main")

# 1) Collect unique table names (preserving order of first appearance)
tables: list[str] = []
seen: set[str] = set()
with open(CSV_IN, newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    header = next(reader)
    for row in reader:
        if not row: continue
        t = row[0].strip()
        # skip rows whose "table name" is obviously garbage from CSV bleed
        if not t or t in seen:
            if t: pass
            continue
        seen.add(t)
        tables.append(t)

# Filter out obviously-bad table names (containing spaces, quotes, colons)
def looks_like_table(name: str) -> bool:
    if not name: return False
    if re.search(r'[\s:"\'/]', name): return False
    return bool(re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', name))

valid_tables = [t for t in tables if looks_like_table(t)]
print(f"Total table name rows: {len(tables)}, valid identifiers: {len(valid_tables)}", file=sys.stderr)

# 2) Walk the branch, load all .py files once (ignore migrations for indirect classification but include for direct)
py_files: list[tuple[str, str]] = []
for dirpath, dirnames, filenames in os.walk(BRANCH):
    # skip noise dirs
    dirnames[:] = [d for d in dirnames if d not in ('.git', '__pycache__', 'node_modules')]
    for fn in filenames:
        if fn.endswith('.py') or fn.endswith('.sql') or fn.endswith('.txt'):
            p = os.path.join(dirpath, fn)
            try:
                with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                    py_files.append((p, f.read()))
            except Exception:
                pass
print(f"Scanned files: {len(py_files)}", file=sys.stderr)

# 3) For each table, look for signals
# Compile patterns per table lazily
DIRECT_PATTERNS = [
    # db_table="T" or db_table = 'T'
    r'db_table\s*=\s*["\']{T}["\']',
    # FROM T (word boundary, possibly with backticks or schema)
    r'\bFROM\s+`?{T}`?\b',
    # INTO T / UPDATE T / DELETE FROM T already covered by FROM, plus:
    r'\bINTO\s+`?{T}`?\b',
    r'\bUPDATE\s+`?{T}`?\b',
    # Meta model ref: class ... (Model): \n ... Meta ... managed/db_table
    # covered by db_table pattern.
]
INDIRECT_PATTERNS = [
    r'\bJOIN\s+`?{T}`?\b',
]
# generic mention (any occurrence as identifier)
MENTION_PATTERN = r'(?<![A-Za-z0-9_]){T}(?![A-Za-z0-9_])'

results = {}
for t in valid_tables:
    esc = re.escape(t)
    direct_hits = 0
    indirect_hits = 0
    mention_hits = 0
    sample_files: list[str] = []
    for p, text in py_files:
        local_direct = 0
        local_indirect = 0
        for pat in DIRECT_PATTERNS:
            local_direct += len(re.findall(pat.format(T=esc), text, re.IGNORECASE))
        for pat in INDIRECT_PATTERNS:
            local_indirect += len(re.findall(pat.format(T=esc), text, re.IGNORECASE))
        local_mention = len(re.findall(MENTION_PATTERN.format(T=esc), text))
        if local_direct or local_indirect or local_mention:
            if len(sample_files) < 3:
                rel = os.path.relpath(p, BRANCH)
                if rel not in sample_files:
                    sample_files.append(rel)
        direct_hits += local_direct
        indirect_hits += local_indirect
        mention_hits += local_mention
    # Classify
    if direct_hits > 0:
        usage = 'DIRECT'
        conf = 'HIGH'
    elif indirect_hits > 0:
        usage = 'INDIRECT'
        conf = 'HIGH' if indirect_hits >= 2 else 'MED'
    elif mention_hits > 0:
        # Mentioned somewhere (maybe comment, string concat, prompt text)
        usage = 'AMBIGUOUS'
        conf = 'LOW'
    else:
        usage = 'UNUSED'
        # Archive-ish suffix -> higher confidence it's really unused
        if re.search(r'(_old|_temp|_test|_2022|_2023)$', t, re.IGNORECASE):
            conf = 'HIGH'
        else:
            conf = 'MED'
    results[t] = {
        'usage': usage,
        'confidence': conf,
        'direct_hits': direct_hits,
        'indirect_hits': indirect_hits,
        'mention_hits': mention_hits,
        'sample_files': ' | '.join(sample_files),
    }

# Also mark invalid-identifier rows
for t in tables:
    if t not in results:
        results[t] = {
            'usage': 'INVALID_NAME',
            'confidence': 'LOW',
            'direct_hits': 0,
            'indirect_hits': 0,
            'mention_hits': 0,
            'sample_files': '',
        }

# 4) Write summary CSV (one row per table)
with open(SUMMARY_OUT, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['table', 'usage', 'confidence', 'direct_hits', 'indirect_hits', 'mention_hits', 'sample_files'])
    for t in tables:
        r = results[t]
        w.writerow([t, r['usage'], r['confidence'], r['direct_hits'], r['indirect_hits'], r['mention_hits'], r['sample_files']])

# 5) Write augmented CSV preserving original schema, with labels on first-occurrence row per table
with open(CSV_IN, newline='', encoding='utf-8') as fin, open(CSV_OUT, 'w', newline='', encoding='utf-8') as fout:
    reader = csv.reader(fin)
    writer = csv.writer(fout)
    header = next(reader)
    writer.writerow(header + ['usage', 'confidence', 'direct_hits', 'indirect_hits', 'mention_hits', 'sample_files'])
    written_label = set()
    for row in reader:
        if not row:
            writer.writerow(row); continue
        t = row[0].strip()
        if t and t not in written_label and t in results:
            r = results[t]
            writer.writerow(row + [r['usage'], r['confidence'], r['direct_hits'], r['indirect_hits'], r['mention_hits'], r['sample_files']])
            written_label.add(t)
        else:
            writer.writerow(row + ['', '', '', '', '', ''])

# 6) Print distribution
from collections import Counter
dist = Counter(r['usage'] for r in results.values())
print("Usage distribution:", dist, file=sys.stderr)
print(f"Wrote {SUMMARY_OUT}", file=sys.stderr)
print(f"Wrote {CSV_OUT}", file=sys.stderr)
