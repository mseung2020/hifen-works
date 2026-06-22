import csv
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), 'data', '분석대상_한국어_좋아요100이상.csv')
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), 'data', 'dify_input_captions.txt')

rows = []
with open(DATA_PATH, encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for r in reader:
        rows.append(r)

rows.sort(key=lambda x: int(x.get('likes', 0) or 0), reverse=True)
top50 = rows[:50]

lines = []
for i, r in enumerate(top50, 1):
    likes = r.get('likes', '0')
    caption = (r.get('caption_full') or '').strip()
    lines.append(f"[{i}] 좋아요 {likes}개")
    lines.append(caption)
    lines.append("")

result = "\n".join(lines)

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    f.write(result)

print(f"저장 완료: {OUTPUT_PATH}")
print(f"총 {len(top50)}개 캡션 / {len(result):,}자")
print("→ dify_input_captions.txt 내용을 Dify 워크플로우 입력창에 붙여넣으세요.")
