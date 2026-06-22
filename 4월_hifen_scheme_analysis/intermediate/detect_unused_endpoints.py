"""
Step 6: Detect unused backend endpoints by cross-referencing with the frontend.

Closed-world assumption: ugwanggiNext is the ONLY client of the backend.

Strategy:
  A) Normalize every backend URL to a template form:
       /partner/<int:pk>/detail  ->  /partner/:PARAM/detail
  B) Walk the frontend repo.  Extract every API call site of the form
       `${api_url}/...`   or
       `axios.<method>('...')` / `fetch('...')` / `api.<method>('...')`
     Capture the raw path template (preserving text around `${}` / `+ var`).
     Normalize template variables to `:PARAM`.
  C) Match backend templates to frontend templates:
       - Exact template match → CALLED (HIGH)
       - Prefix match (frontend calls a deeper sub-path) → CALLED (MED)
       - No match → UNCALLED
  D) Emit:
       - endpoint_usage.csv  (per backend endpoint: usage + matched_by + evidence)
       - frontend_calls.csv  (all extracted frontend call sites)
       - unused_endpoints_report.md
"""
from __future__ import annotations
import csv, os, re, sys
from collections import defaultdict, Counter

ROOT = "/Users/rachel/Documents/김명승 작업실/ugwanggiAPI-main"
BE_ROOT = os.path.join(ROOT, "ugwanggiAPI-main")
FE_ROOT = os.path.join(ROOT, "ugwanggiNext-main")
IN_ENDPOINTS = os.path.join(ROOT, "api_endpoints.csv")

OUT_USAGE = os.path.join(ROOT, "endpoint_usage.csv")
OUT_FE_CALLS = os.path.join(ROOT, "frontend_calls.csv")
OUT_REPORT = os.path.join(ROOT, "unused_endpoints_report.md")

# ------------------------------------------------------------------
# A) Load + normalize backend endpoints
# ------------------------------------------------------------------
# Django path converters look like  <int:pk>  <str:slug>  or legacy  (?P<name>\d+)
BE_PARAM_RX = re.compile(r'<[^>]+>|\(\?P<[^>]+>[^)]+\)')

def normalize_path(p: str) -> str:
    # Collapse any leading/trailing slashes and whitespace
    p = p.strip()
    if not p.startswith('/'):
        p = '/' + p
    # Replace Django path-converters with :PARAM
    p = BE_PARAM_RX.sub(':PARAM', p)
    # Remove any leftover $ from re_path patterns
    p = p.replace('$', '')
    # Normalize trailing slash
    if len(p) > 1 and p.endswith('/'):
        p = p[:-1]
    return p

backend_rows: list[dict] = []
with open(IN_ENDPOINTS, newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        r['norm_path'] = normalize_path(r['url_path'])
        backend_rows.append(r)

# Map: normalized path -> list of (row index)
be_by_norm: dict[str, list[int]] = defaultdict(list)
for i, r in enumerate(backend_rows):
    be_by_norm[r['norm_path']].append(i)

print(f"Backend endpoints: {len(backend_rows)}", file=sys.stderr)

# ------------------------------------------------------------------
# B) Walk frontend and extract call sites
# ------------------------------------------------------------------
# Target directories in the FE repo
FE_DIRS = [os.path.join(FE_ROOT, "src", d) for d in
           ("service", "pages", "components", "lib", "utils", "context")]

# Call-site patterns — we handle:
#  1. Template literals starting with ${api_url} or `${api_url}/...`
#  2. axios.<m>( '<path>' ) / .get(`${api_url}/...`) etc.
#  3. fetch("/api/...") or fetch(`/api/...`)
#  4. api.<m>(`...`)  (the `api` object in many services)
# To be robust, we extract the RAW argument text, then clean it.

CALL_RX = re.compile(
    r'(?P<verb>axios\s*\.\s*(?P<method1>get|post|put|delete|patch)'
    r'|api\s*\.\s*(?P<method2>get|post|put|delete|patch)'
    r'|fetch)\s*\(\s*'
    r'(?P<q>[`\'"])(?P<raw>[^`\'"]*?)(?P=q)',
    re.IGNORECASE,
)

# Also catch: `${api_url}/...` without explicit call wrapper, in case they
# build URLs in one place and pass them later.
TEMPLATE_ONLY_RX = re.compile(
    r'`\$\{\s*api_url\s*\}(?P<raw>[^`]*)`',
)

def template_literal_to_template(raw: str) -> tuple[str | None, bool]:
    """
    Given the raw contents of a JS template literal (without surrounding
    backticks), produce a normalized API path or return (None, False) if it
    doesn't look like a backend path.

    Returns (template_path, is_ambiguous).  Ambiguous = contains ${} at a
    position that could make the *route base* uncertain.
    """
    s = raw.strip()
    # If doesn't start with "/" and doesn't start with "?" → skip
    if not s:
        return None, False
    # Handle the case where the raw already starts with ${api_url} or ${api}
    s = re.sub(r'^\$\{[^}]+\}', '', s)
    if not s.startswith('/'):
        return None, False
    # Strip query string
    if '?' in s:
        s = s.split('?', 1)[0]
    if '#' in s:
        s = s.split('#', 1)[0]
    # Drop trailing slash
    if len(s) > 1 and s.endswith('/'):
        s = s[:-1]
    # Replace ${...} with :PARAM; flag ambiguity if the very FIRST segment is a var
    ambiguous = False
    first_seg = s.split('/', 2)[1] if len(s.split('/')) > 1 else ''
    if '${' in first_seg:
        ambiguous = True
    s = re.sub(r'\$\{[^}]+\}', ':PARAM', s)
    # Quoted concat  "  + var + "  could leave stray +; we only handle simple cases
    s = re.sub(r'[\'"]\s*\+\s*[a-zA-Z_][a-zA-Z0-9_]*\s*\+\s*[\'"]', ':PARAM', s)
    s = re.sub(r'[\'"]\s*\+\s*[a-zA-Z_][a-zA-Z0-9_]*', ':PARAM', s)
    return s, ambiguous

fe_calls: list[dict] = []
fe_files_scanned = 0

# ---- 2-pass FE scan: first collect `const X = `${api_url}/...`` base URLs ----
BASE_DECL_RX = re.compile(
    r'(?:const|let|var)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*`\$\{\s*(?:api_?url|apiUrl|API_URL)\s*\}(?P<rest>[^`]*)`'
)
# Also handle  const X = api_url + "..." + ...
BASE_CONCAT_RX = re.compile(
    r'(?:const|let|var)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?:api_?url|apiUrl|API_URL)\s*\+\s*[\'"]([^\'"]*)[\'"]'
)

base_vars: dict[str, str] = {}  # var name -> path (may contain ${...})
for root in FE_DIRS:
    if not os.path.isdir(root): continue
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in ('node_modules', '.next', '__pycache__')]
        for fn in fns:
            if not fn.endswith(('.js','.jsx','.ts','.tsx','.mjs')): continue
            try:
                text = open(os.path.join(dp, fn), encoding='utf-8', errors='ignore').read()
            except Exception: continue
            for m in BASE_DECL_RX.finditer(text):
                base_vars[m.group(1)] = m.group('rest')
            for m in BASE_CONCAT_RX.finditer(text):
                base_vars[m.group(1)] = m.group(2)
print(f"Base-URL constants collected: {len(base_vars)}", file=sys.stderr)

# Build a combined regex capturing any  `${VAR}...`  with VAR in our base_vars
if base_vars:
    VAR_CALL_RX = re.compile(
        r'(?:axios|api)\s*\.\s*(?P<method>get|post|put|delete|patch)\s*\(\s*`\$\{\s*(?P<var>'
        + '|'.join(re.escape(v) for v in base_vars.keys()) +
        r')\s*\}(?P<rest>[^`]*)`',
        re.IGNORECASE,
    )
else:
    VAR_CALL_RX = None

for root in FE_DIRS:
    if not os.path.isdir(root): continue
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in ('node_modules', '.next', '__pycache__')]
        for fn in fns:
            if not fn.endswith(('.js','.jsx','.ts','.tsx','.mjs')): continue
            path = os.path.join(dp, fn)
            fe_files_scanned += 1
            try:
                text = open(path, encoding='utf-8', errors='ignore').read()
            except Exception: continue

            for m in CALL_RX.finditer(text):
                raw = m.group('raw')
                method = (m.group('method1') or m.group('method2') or
                          ('GET' if m.group('verb').lower().startswith('fetch') else '?')).upper()
                # Strip api_url prefix if present via template — for plain-string
                # calls raw starts with '/', which is already OK.
                s = raw.strip()
                s = re.sub(r'^\$\{[^}]+\}', '', s)
                if '?' in s: s = s.split('?',1)[0]
                if not s.startswith('/'):
                    # Could be a full URL or relative; skip if not path-like
                    if s.startswith('http'):
                        continue
                    continue
                if len(s) > 1 and s.endswith('/'): s = s[:-1]
                first_seg = s.split('/',2)[1] if len(s.split('/'))>1 else ''
                ambiguous = '${' in first_seg
                # Normalize dynamic bits to :PARAM
                s_norm = re.sub(r'\$\{[^}]+\}', ':PARAM', s)
                fe_calls.append({
                    'method': method,
                    'raw': raw,
                    'norm_path': s_norm,
                    'ambiguous': ambiguous,
                    'file': os.path.relpath(path, FE_ROOT),
                })

            # Pass 2b: var-based calls  api.get(`${JOBS_BASE}/pending`)
            if VAR_CALL_RX is not None:
                for m in VAR_CALL_RX.finditer(text):
                    var = m.group('var')
                    method = m.group('method').upper()
                    base = base_vars.get(var, '')
                    rest = m.group('rest')
                    combined = base + rest
                    s = combined.strip()
                    if '?' in s: s = s.split('?',1)[0]
                    if not s.startswith('/'): continue
                    if len(s) > 1 and s.endswith('/'): s = s[:-1]
                    first_seg = s.split('/',2)[1] if len(s.split('/'))>1 else ''
                    ambiguous = '${' in first_seg
                    s_norm = re.sub(r'\$\{[^}]+\}', ':PARAM', s)
                    fe_calls.append({
                        'method': method,
                        'raw': f'`${{{var}}}{rest}` (resolved → {combined})',
                        'norm_path': s_norm,
                        'ambiguous': ambiguous,
                        'file': os.path.relpath(path, FE_ROOT),
                    })

            for m in TEMPLATE_ONLY_RX.finditer(text):
                raw = m.group('raw')
                s = raw.strip()
                if '?' in s: s = s.split('?',1)[0]
                if not s.startswith('/'): continue
                if len(s) > 1 and s.endswith('/'): s = s[:-1]
                first_seg = s.split('/',2)[1] if len(s.split('/'))>1 else ''
                ambiguous = '${' in first_seg
                s_norm = re.sub(r'\$\{[^}]+\}', ':PARAM', s)
                fe_calls.append({
                    'method': '?',
                    'raw': '`${api_url}' + raw + '`',
                    'norm_path': s_norm,
                    'ambiguous': ambiguous,
                    'file': os.path.relpath(path, FE_ROOT),
                })

print(f"Frontend files scanned: {fe_files_scanned}", file=sys.stderr)
print(f"Frontend call sites extracted: {len(fe_calls)}", file=sys.stderr)

# Write frontend calls
with open(OUT_FE_CALLS, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['method','norm_path','ambiguous','raw','file'])
    w.writeheader()
    w.writerows(fe_calls)

# ------------------------------------------------------------------
# C) Match backend endpoints to frontend calls
# ------------------------------------------------------------------
# Build index of FE norm paths for fast lookup
fe_norm_index: dict[str, list[int]] = defaultdict(list)
for i, c in enumerate(fe_calls):
    fe_norm_index[c['norm_path']].append(i)

def prefix_match(be_norm: str, fe_norm: str) -> bool:
    """True if fe_norm is the same or a sub-path under be_norm, respecting /."""
    if fe_norm == be_norm: return True
    if fe_norm.startswith(be_norm + '/'): return True
    return False

# For each backend endpoint, evaluate usage
usage_rows: list[dict] = []
for r in backend_rows:
    be = r['norm_path']
    # Exact match
    exact = fe_norm_index.get(be, [])
    # Prefix match (FE hits a deeper path that our BE pattern might catch)
    prefix_hits: list[int] = []
    if not exact:
        for fp, idxs in fe_norm_index.items():
            if prefix_match(be, fp) or prefix_match(fp, be):
                prefix_hits.extend(idxs)
    # Classify
    if exact:
        usage = 'CALLED'
        conf = 'HIGH'
        match_type = 'exact'
        hits = exact
    elif prefix_hits:
        # Any hit was from an ambiguous call?
        has_amb = any(fe_calls[i]['ambiguous'] for i in prefix_hits)
        usage = 'CALLED'
        conf = 'LOW' if has_amb else 'MED'
        match_type = 'prefix'
        hits = prefix_hits
    else:
        usage = 'UNCALLED'
        conf = 'HIGH'
        match_type = ''
        hits = []
    # Collect evidence (up to 3 FE files)
    ev_files = []
    for i in hits[:3]:
        ev_files.append(fe_calls[i]['file'])
    usage_rows.append({
        'app': r['app'],
        'http_methods': r['http_methods'],
        'url_path': r['url_path'],
        'norm_path': be,
        'view_ref': r['view_ref'],
        'view_file': r['view_file'],
        'tables_touched': r['tables_touched'],
        'usage': usage,
        'match_type': match_type,
        'confidence': conf,
        'frontend_hits': len(hits),
        'evidence_files': ' | '.join(ev_files),
    })

# Write usage CSV
with open(OUT_USAGE, 'w', newline='', encoding='utf-8') as f:
    fn = ['app','http_methods','url_path','norm_path','view_ref','view_file',
          'tables_touched','usage','match_type','confidence','frontend_hits','evidence_files']
    w = csv.DictWriter(f, fieldnames=fn)
    w.writeheader()
    w.writerows(usage_rows)

# ------------------------------------------------------------------
# D) Report
# ------------------------------------------------------------------
by_usage = Counter(r['usage'] for r in usage_rows)
by_conf = Counter((r['usage'], r['confidence']) for r in usage_rows)
by_app = defaultdict(lambda: [0,0])  # [called, uncalled]
for r in usage_rows:
    by_app[r['app']][0 if r['usage']=='CALLED' else 1] += 1

lines = ["# Step 6 — Endpoint usage vs frontend\n"]
lines.append(f"**Backend endpoints:** {len(usage_rows)}")
lines.append(f"**Frontend call sites:** {len(fe_calls)}")
lines.append(f"**Frontend files scanned:** {fe_files_scanned}\n")
lines.append(f"## Usage summary\n- CALLED: {by_usage['CALLED']}")
lines.append(f"- UNCALLED: {by_usage['UNCALLED']}\n")
lines.append(f"### By confidence\n" + "\n".join(f"- {k[0]}/{k[1]}: {v}" for k,v in sorted(by_conf.items())))
lines.append("\n## Per-app breakdown\n| app | called | uncalled | uncalled % |\n|---|---|---|---|")
for a in sorted(by_app):
    c, u = by_app[a]
    pct = (u/(c+u)*100) if (c+u) else 0
    lines.append(f"| {a} | {c} | {u} | {pct:.1f}% |")

# Top uncalled endpoints by app
lines.append("\n## Sample UNCALLED endpoints (first 30)\n")
uncalled = [r for r in usage_rows if r['usage']=='UNCALLED']
for r in uncalled[:30]:
    lines.append(f"- `{r['http_methods']} {r['url_path']}` ({r['app']}/{r['view_ref']})")

with open(OUT_REPORT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print(f"CALLED: {by_usage['CALLED']}, UNCALLED: {by_usage['UNCALLED']}", file=sys.stderr)
print(f"Wrote {OUT_USAGE}", file=sys.stderr)
print(f"Wrote {OUT_FE_CALLS}", file=sys.stderr)
print(f"Wrote {OUT_REPORT}", file=sys.stderr)
