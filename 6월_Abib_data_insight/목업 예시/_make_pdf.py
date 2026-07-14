#!/usr/bin/env python3
# 카드뉴스 앞면(넘겨보는 페이지)만 21장 캡처 -> PDF (+ PNG들)
import os, glob
from playwright.sync_api import sync_playwright
from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(BASE, "카드뉴스_통합_TOP발행량_아비브_추가 1.html")
OUTDIR = os.path.join(BASE, "_pages")
PDF  = os.path.join(BASE, "카드뉴스_통합_TOP발행량_아비브.pdf")
os.makedirs(OUTDIR, exist_ok=True)
for f in glob.glob(os.path.join(OUTDIR, "*.png")):
    os.remove(f)

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    page = browser.new_page(viewport={"width":1920,"height":1080}, device_scale_factor=2)
    page.goto("file://" + SRC)
    # 폰트/렌더 안정화
    page.wait_for_timeout(800)
    # 모서리 둥근 것/스크롤 자국 제거해서 깔끔한 직사각형 페이지로
    page.add_style_tag(content=".face{border-radius:0!important;} .track{border-radius:0!important;}")
    # 앞면만: .inner 의 첫 번째 face (back 제외)
    faces = page.query_selector_all(".card .inner > .face:not(.back)")
    print("front faces:", len(faces))
    paths = []
    for i, face in enumerate(faces, 1):
        face.scroll_into_view_if_needed()
        page.wait_for_timeout(120)
        out = os.path.join(OUTDIR, f"page_{i:02d}.png")
        face.screenshot(path=out)
        paths.append(out)
    browser.close()

# PNG -> 단일 PDF (흰 배경으로 합성)
imgs = []
for p in sorted(paths):
    im = Image.open(p).convert("RGBA")
    bg = Image.new("RGBA", im.size, (255,255,255,255))
    bg.alpha_composite(im)
    imgs.append(bg.convert("RGB"))

imgs[0].save(PDF, save_all=True, append_images=imgs[1:], resolution=150.0)
print("PDF:", PDF, "pages:", len(imgs))
