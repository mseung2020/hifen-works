"""
Step 5: Extract API endpoints per app.

Strategy:
  1) Parse each app's urls.py (and nested urls*.py) with AST to collect
     path(...) / re_path(...) entries.  For each entry capture:
       - URL pattern (raw)
       - View reference name (function or CBV as_view())
       - include() chains (mounted under parent prefix from project urls.py)
  2) Walk the project root's urls.py to establish app prefix mapping
     (already known from Step 3, but re-derived here for robustness).
  3) For each view reference, locate the view definition in the app's
     views.py (or views/*.py module) and:
       - Determine HTTP methods handled:
           • function views with @api_view([...]) → decorator's list
           • CBVs subclassing APIView/ViewSet/GenericAPIView/etc. →
             methods defined: get/post/put/patch/delete
           • Any ViewSet gets the standard set based on ModelViewSet base
       - Scan the view file for referenced model classes
         (using the Step 4 ModelName -> db_table map), plus raw SQL
         patterns (FROM/INSERT/UPDATE/DELETE) to capture tables touched.
  4) Emit rows:
       app, http_methods, url_path, view_ref, view_file, tables_touched,
       confidence

Outputs:
  - api_endpoints.csv
  - endpoints_report.md  (summary)
"""
from __future__ import annotations
import ast, csv, os, re, sys, json
from collections import defaultdict, Counter

ROOT = "/Users/rachel/Documents/김명승 작업실/ugwanggiAPI-main"
BRANCH = os.path.join(ROOT, "ugwanggiAPI-main")
FINAL = os.path.join(ROOT, "hifen_scheme_table_usage_final_boosted.csv")
OUT = os.path.join(ROOT, "api_endpoints.csv")
OUT_REPORT = os.path.join(ROOT, "endpoints_report.md")

APPS = [
    'admin','ads','aichat','aitools','amore','archive','brand','creators_insights',
    'express','instagram','instagram_admin','keywords','kpi','monitoring',
    'oliveyoung','partner','partner_admin','partner_instagram','preview','search',
    'subscribe','survey','tiktok','trends','user','youtube','youtube_shopping',
]

# ---- Load USED tables ----
used_tables: set[str] = set()
with open(FINAL, newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r.get('boosted_usage') == 'USED':
            used_tables.add(r['table'])

# ---- Build ModelName -> db_table map (repeat of Step 4's pass 1) ----
def const_str(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None

def extract_db_table(cls):
    for item in cls.body:
        if isinstance(item, ast.ClassDef) and item.name == 'Meta':
            for sub in item.body:
                if isinstance(sub, ast.Assign):
                    for tgt in sub.targets:
                        if isinstance(tgt, ast.Name) and tgt.id == 'db_table':
                            s = const_str(sub.value)
                            if s: return s
    return None

model_to_table: dict[str, str] = {}
for dp, dns, fns in os.walk(BRANCH):
    dns[:] = [d for d in dns if d not in ('__pycache__', '.git', 'migrations')]
    for fn in fns:
        if fn == 'models.py':
            path = os.path.join(dp, fn)
            try:
                tree = ast.parse(open(path, encoding='utf-8', errors='ignore').read())
            except Exception: continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    t = extract_db_table(node)
                    if t:
                        model_to_table[node.name] = t

print(f"Models mapped: {len(model_to_table)}", file=sys.stderr)

# ---- Parse project urls.py to get app prefix mapping ----
def parse_urls_file(path: str):
    try:
        tree = ast.parse(open(path, encoding='utf-8', errors='ignore').read())
    except Exception as e:
        print(f"[urls-parse] {path}: {e}", file=sys.stderr)
        return []
    entries = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            fname = None
            if isinstance(func, ast.Name): fname = func.id
            elif isinstance(func, ast.Attribute): fname = func.attr
            if fname in ('path', 're_path') and node.args:
                # First arg = url pattern (string)
                url_pat = const_str(node.args[0])
                if url_pat is None: continue
                if len(node.args) < 2: continue
                second = node.args[1]
                # Case: include('app.urls')
                if isinstance(second, ast.Call):
                    subfunc = second.func
                    subname = subfunc.id if isinstance(subfunc, ast.Name) else (subfunc.attr if isinstance(subfunc, ast.Attribute) else None)
                    if subname == 'include' and second.args:
                        target = const_str(second.args[0])
                        entries.append({'kind':'include','pattern':url_pat,'target':target})
                        continue
                    # Case: View.as_view()
                    if subname == 'as_view':
                        # second.func.value is the class
                        cls_node = subfunc.value if isinstance(subfunc, ast.Attribute) else None
                        cls_name = None
                        if isinstance(cls_node, ast.Name):
                            cls_name = cls_node.id
                        elif isinstance(cls_node, ast.Attribute):
                            cls_name = cls_node.attr
                        entries.append({'kind':'view','pattern':url_pat,'view':cls_name,'view_kind':'CBV'})
                        continue
                if isinstance(second, ast.Name):
                    entries.append({'kind':'view','pattern':url_pat,'view':second.id,'view_kind':'func'})
                    continue
                if isinstance(second, ast.Attribute):
                    entries.append({'kind':'view','pattern':url_pat,'view':second.attr,'view_kind':'func'})
                    continue
    return entries

# Find all urls.py files in apps and project
project_urls = os.path.join(BRANCH, 'ugwanggiAPI', 'urls.py')
project_entries = parse_urls_file(project_urls)
# Map: app_module_name -> URL prefix (from include())
app_prefix: dict[str, str] = {}
for e in project_entries:
    if e['kind'] == 'include' and e['target']:
        mod = e['target'].split('.')[0]
        app_prefix[mod] = '/' + e['pattern'].rstrip('/') + ('' if e['pattern'].endswith('/') else '/')
# Normalize: project urls pattern is like "search/" → "/search/"
# Use as-is leading slash
for k, v in list(app_prefix.items()):
    if not v.startswith('/'): app_prefix[k] = '/' + v

print(f"App URL prefixes: {len(app_prefix)}", file=sys.stderr)

# ---- Per app: collect endpoint rows ----
endpoint_rows: list[dict] = []

# Preload view-file text per app (views.py + views/*.py)
app_view_files: dict[str, list[tuple[str,str]]] = defaultdict(list)
app_view_trees: dict[str, list[tuple[str, ast.Module]]] = defaultdict(list)
for app in APPS:
    root = os.path.join(BRANCH, app)
    if not os.path.isdir(root): continue
    # candidate view files
    candidates = []
    for fn in os.listdir(root):
        full = os.path.join(root, fn)
        if os.path.isfile(full) and fn.startswith('views') and fn.endswith('.py'):
            candidates.append(full)
    # nested views/ package
    nested = os.path.join(root, 'views')
    if os.path.isdir(nested):
        for fn in os.listdir(nested):
            if fn.endswith('.py'):
                candidates.append(os.path.join(nested, fn))
    for cp in candidates:
        try:
            src = open(cp, encoding='utf-8', errors='ignore').read()
            tree = ast.parse(src)
            app_view_files[app].append((cp, src))
            app_view_trees[app].append((cp, tree))
        except Exception: pass

def find_view_def(app: str, name: str):
    """Return (file_path, node) for a ClassDef or FunctionDef named `name`."""
    for path, tree in app_view_trees.get(app, []):
        for node in tree.body:
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
                return (path, node)
    return (None, None)

CBV_METHOD_NAMES = {'get','post','put','patch','delete','head','options'}
API_VIEW_DECORATOR_NAMES = {'api_view'}

def http_methods_of(node) -> list[str]:
    methods: set[str] = set()
    if isinstance(node, ast.ClassDef):
        # look at decorators? Not typical. Look at base class names for hints.
        base_names = []
        for b in node.bases:
            if isinstance(b, ast.Name): base_names.append(b.id)
            elif isinstance(b, ast.Attribute): base_names.append(b.attr)
        # methods defined
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if item.name in CBV_METHOD_NAMES:
                    methods.add(item.name.upper())
        # ModelViewSet implies standard set if no methods declared
        if not methods and any('ModelViewSet' in bn or 'ViewSet' in bn for bn in base_names):
            methods.update({'GET','POST','PUT','PATCH','DELETE'})
        elif not methods:
            # pure APIView with no handlers — rare; leave empty
            pass
    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        for dec in node.decorator_list:
            # @api_view(['GET','POST'])
            if isinstance(dec, ast.Call):
                fn = dec.func.attr if isinstance(dec.func, ast.Attribute) else (dec.func.id if isinstance(dec.func, ast.Name) else None)
                if fn in API_VIEW_DECORATOR_NAMES and dec.args:
                    arg0 = dec.args[0]
                    if isinstance(arg0, ast.List):
                        for el in arg0.elts:
                            if isinstance(el, ast.Constant) and isinstance(el.value, str):
                                methods.add(el.value.upper())
            elif isinstance(dec, ast.Name) and dec.id in API_VIEW_DECORATOR_NAMES:
                pass
    return sorted(methods) if methods else ['?']

def node_src_text(src: str, node) -> str:
    # ast.get_source_segment may fail on old trees, fall back to line slicing
    try:
        seg = ast.get_source_segment(src, node)
        if seg: return seg
    except Exception: pass
    return ''

# Pattern for raw SQL table mentions
RAW_SQL_REF_RX = re.compile(
    r'\b(?:FROM|JOIN|INSERT\s+INTO|UPDATE|DELETE\s+FROM)\s+`?([A-Za-z_][A-Za-z0-9_]*)`?',
    re.IGNORECASE,
)
MODEL_OBJECTS_RX = re.compile(r'\b([A-Z][A-Za-z0-9_]+)\s*\.\s*objects\b')

def tables_touched(view_file: str, node, whole_src: str) -> set[str]:
    touched: set[str] = set()
    seg = node_src_text(whole_src, node) or whole_src
    # ORM: ModelName.objects
    for m in MODEL_OBJECTS_RX.finditer(seg):
        cls = m.group(1)
        t = model_to_table.get(cls)
        if t and t in used_tables:
            touched.add(t)
    # Raw SQL references
    for m in RAW_SQL_REF_RX.finditer(seg):
        t = m.group(1)
        if t in used_tables:
            touched.add(t)
    return touched

def resolve_urls_for_app(app: str, start_file: str, parent_prefix: str):
    """Recursively parse urls*.py for an app, handling nested include() chains."""
    entries = parse_urls_file(start_file)
    for e in entries:
        if e['kind'] == 'include':
            # Nested include (rare) — best-effort: only handle if target is within the app
            target = e['target']
            if target and target.startswith(app + '.'):
                sub_mod = target.split('.')[1]
                sub_path = os.path.join(BRANCH, app, sub_mod + '.py')
                if os.path.exists(sub_path):
                    resolve_urls_for_app(app, sub_path, parent_prefix.rstrip('/') + '/' + e['pattern'])
        else:
            url = (parent_prefix.rstrip('/') + '/' + e['pattern']).replace('//','/')
            view_name = e['view']
            view_kind = e['view_kind']
            vf, vnode = find_view_def(app, view_name)
            methods = http_methods_of(vnode) if vnode else ['?']
            if vf and vnode:
                src = dict(app_view_files[app]).get(vf, '')
                tables = tables_touched(vf, vnode, src)
            else:
                tables = set()
            endpoint_rows.append({
                'app': app,
                'http_methods': '|'.join(methods),
                'url_path': url,
                'view_ref': view_name,
                'view_kind': view_kind,
                'view_file': os.path.relpath(vf, BRANCH) if vf else '',
                'tables_touched': '|'.join(sorted(tables)),
                'table_count': len(tables),
            })

for app in APPS:
    urls_py = os.path.join(BRANCH, app, 'urls.py')
    if not os.path.exists(urls_py): continue
    prefix = app_prefix.get(app, '/' + app + '/')
    resolve_urls_for_app(app, urls_py, prefix)

# ---- Write outputs ----
with open(OUT, 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['app','http_methods','url_path','view_ref','view_kind',
                  'view_file','tables_touched','table_count']
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(endpoint_rows)

# Report
lines = ["# Step 5 — API Endpoints Report\n"]
lines.append(f"**Total endpoints:** {len(endpoint_rows)}\n")
# By app
by_app = Counter(r['app'] for r in endpoint_rows)
lines.append("\n## Endpoints per app\n| app | count |\n|---|---|")
for a, n in sorted(by_app.items(), key=lambda kv: -kv[1]):
    lines.append(f"| {a} | {n} |")

# Methods
methods_flat = Counter()
for r in endpoint_rows:
    for m in r['http_methods'].split('|'):
        methods_flat[m] += 1
lines.append("\n## HTTP method distribution\n" + ", ".join(f"{m}={n}" for m,n in methods_flat.most_common()))

# Endpoints with 0 tables touched (might be utility/health/debug)
no_table = [r for r in endpoint_rows if r['table_count'] == 0]
lines.append(f"\n## Endpoints touching 0 tables: {len(no_table)}\n")

with open(OUT_REPORT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print(f"Total endpoints: {len(endpoint_rows)}", file=sys.stderr)
print(f"By app (top 10): {by_app.most_common(10)}", file=sys.stderr)
print(f"Endpoints with 0 tables touched: {len(no_table)}", file=sys.stderr)
print(f"Wrote {OUT}", file=sys.stderr)
print(f"Wrote {OUT_REPORT}", file=sys.stderr)
