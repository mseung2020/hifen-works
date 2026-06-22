"""
Step 10 bundler: combine template + data + JS into a single self-contained
index.html in core_materials/.
"""
import os, sys, json

ROOT = "/Users/rachel/Documents/김명승 작업실/ugwanggiAPI-main"
TEMPLATE_DIR = os.path.join(ROOT, "intermediate", "site_template")
CORE = os.path.join(ROOT, "core_materials")

with open(os.path.join(TEMPLATE_DIR, "index.html"), encoding="utf-8") as f:
    tpl = f.read()
with open(os.path.join(TEMPLATE_DIR, "styles.css"), encoding="utf-8") as f:
    css = f.read()
with open(os.path.join(TEMPLATE_DIR, "app.js"), encoding="utf-8") as f:
    js = f.read()
with open(os.path.join(CORE, "site_data.json"), encoding="utf-8") as f:
    data_raw = f.read()

# Compact JSON is already compact. Keep as-is.
html = tpl.replace("/*__STYLES__*/", css)
html = html.replace("/*__DATA__*/null", data_raw)
html = html.replace("/*__APP__*/", js)

out = os.path.join(CORE, "index.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html)

size = os.path.getsize(out) / 1024
print(f"Wrote {out} ({size:.1f} KB)", file=sys.stderr)
