#!/usr/bin/env python3
"""hifen_user_guide.html → 이미지 base64 임베드 단일 파일 빌드.

사용법:  python3 build_standalone.py
출력:    hifen_user_guide_standalone.html
원본(hifen_user_guide.html)을 수정한 뒤 이 스크립트를 다시 돌리면 동기화됩니다.
"""
import base64, os

SRC = 'hifen_user_guide.html'
OUT = 'hifen_user_guide_standalone.html'
IMGDIR = '유저 관련 화면 사진'

with open(SRC, encoding='utf-8') as f:
    html = f.read()

# 폴더의 모든 png → base64 data URI
img_data = {}
for fn in sorted(os.listdir(IMGDIR)):
    if fn.lower().endswith('.png'):
        with open(os.path.join(IMGDIR, fn), 'rb') as imgf:
            b64 = base64.b64encode(imgf.read()).decode('ascii')
        img_data[fn[:-4]] = f'data:image/png;base64,{b64}'

def jstr(s):
    return '"' + s.replace('"', '\\"') + '"'
entries = ',\n'.join(f'  {jstr(k)}: {jstr(v)}' for k, v in img_data.items())
img_data_js = 'const IMG_DATA = {\n' + entries + '\n};\n'

# IMG_DIR 선언 뒤에 IMG_DATA 삽입
marker = "const IMG_DIR = '유저 관련 화면 사진/';"
assert marker in html, "IMG_DIR marker not found"
html = html.replace(marker, marker + '\n' + img_data_js, 1)

# 이미지 src 참조 3곳 치환
replacements = [
    ("document.getElementById('guideImg').src = IMG_DIR + imgName + '.png';",
     "document.getElementById('guideImg').src = IMG_DATA[imgName] || '';"),
    ('<div class="flow-thumb"><img src="${IMG_DIR}${scr.img}.png"></div>',
     '<div class="flow-thumb"><img src="${IMG_DATA[scr.img]||\'\'}"></div>'),
    ('<div class="flow-thumb"><img src="${IMG_DIR}${f.img}.png"></div>',
     '<div class="flow-thumb"><img src="${IMG_DATA[f.img]||\'\'}"></div>'),
]
for old, new in replacements:
    assert old in html, f"치환 대상 없음: {old[:50]}"
    html = html.replace(old, new, 1)

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"생성 완료: {OUT}")
print(f"임베드 이미지: {len(img_data)}장 · 파일 크기: {os.path.getsize(OUT)/1024/1024:.1f} MB")
