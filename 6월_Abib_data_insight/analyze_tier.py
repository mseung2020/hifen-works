# -*- coding: utf-8 -*-
"""아비브 크리에이터 체급 분포 분석 (vs 전체 브랜드 = 올리브영 TOP100 baseline)
- 악성 CSV(설명 필드 내 줄바꿈/따옴표 오류)는 선행 ID 패턴으로 레코드 재구성 후
  정상 파싱된 행만 사용. 디스크립션 등 자유텍스트 컬럼은 분석에 불필요해 버림.
"""
import csv, re, io

DATA = "/Users/rachel/Documents/김명승 작업실/6월_Abib_data_insight/data"

def load(path, ncols, idlen=11):
    pat = re.compile(r'^[A-Za-z0-9_\-]{%d},' % idlen)
    recs, cur = [], None
    with open(path, encoding='utf-8') as fh:
        header = next(csv.reader([fh.readline()]))
        for line in fh:
            if pat.match(line):
                if cur is not None: recs.append(cur)
                cur = line
            else:
                cur = (cur or '') + line
        if cur is not None: recs.append(cur)
    rows, dropped = [], 0
    for rec in recs:
        try:
            row = next(csv.reader([rec]))
        except Exception:
            row = []
        if len(row) == ncols:
            rows.append(row)
        else:
            dropped += 1
    return header, rows, len(recs), dropped

def to_int(x):
    x = (x or '').strip()
    if x in ('', 'NULL', 'None', 'nan'): return None
    try: return int(float(x))
    except: return None

# ---------- 체급 분류 ----------
def yt_tier(s):
    if s is None: return None
    if s < 10_000: return '나노'
    if s < 100_000: return '마이크로'
    if s < 500_000: return '미드티어'
    if s < 1_000_000: return '매크로'
    return '메가'

def ig_tier(f):
    if f is None: return None
    if f < 10_000: return '나노'
    if f < 50_000: return '마이크로'
    if f < 100_000: return '미드티어'
    if f < 200_000: return '하이티어'
    if f < 500_000: return '매크로'
    if f < 1_000_000: return '메가'
    return '셀럽'

YT_ORDER = ['나노','마이크로','미드티어','매크로','메가']
IG_ORDER = ['나노','마이크로','미드티어','하이티어','매크로','메가','셀럽']

# ---------- 전체 브랜드(TOP100) baseline : 발행량 ----------
# 출처: 목업 예시/카드뉴스_TOP100_체급별발행량.html (올리브영 TOP100 진입 브랜드, 1~6월)
TOP100_YT = {'나노':18135,'마이크로':11852,'미드티어':8182,'매크로':1511,'메가':1345}
TOP100_IG = {'나노':25347,'마이크로':14745,'미드티어':5534,'하이티어':4023,'매크로':1771,'메가':306,'셀럽':159}

def pct_dist(counts, order):
    tot = sum(counts.get(k,0) for k in order)
    return {k: (counts.get(k,0)/tot*100 if tot else 0) for k in order}, tot

def in_h1(d):  # 2026-01-01 ~ 2026-06-30
    return bool(d) and '2026-01-01' <= d[:10] <= '2026-06-30'

# ================= YouTube =================
h, rows, nrec, drop = load(f"{DATA}/아비브 유튜브.csv", 30)
ci = {c:i for i,c in enumerate(h)}
yt = []
for r in rows:
    yt.append({
        'channel_id': r[ci['channel_id']],
        'subs': to_int(r[ci['subscribers']]),
        'date': r[ci['publishDate']],
        'ppl': to_int(r[ci['product_ppl']]),
    })
yt_valid = [x for x in yt if x['subs'] is not None]
print(f"[YouTube] 재구성 {nrec} → 정상 {len(rows)} (버림 {drop}) | 구독자 유효 {len(yt_valid)}")

# ================= Instagram =================
h2, rows2, nrec2, drop2 = load(f"{DATA}/아비브 인스타.csv", 27)
ci2 = {c:i for i,c in enumerate(h2)}
ig = []
for r in rows2:
    ig.append({
        'user_id': r[ci2['user_id']],
        'followers': to_int(r[ci2['followers']]),
        'date': r[ci2['publish_date']],
        'ppl': to_int(r[ci2['product_ppl']]),
    })
ig_valid = [x for x in ig if x['followers'] is not None]
print(f"[Instagram] 재구성 {nrec2} → 정상 {len(rows2)} (버림 {drop2}) | 팔로워 유효 {len(ig_valid)}")

# ---------- 분포 계산 헬퍼 ----------
def pub_dist(data, valkey, tierfn):
    c = {}
    for x in data:
        t = tierfn(x[valkey]); c[t] = c.get(t,0)+1
    return c

def uniq_dist(data, idkey, valkey, tierfn):
    best = {}
    for x in data:
        k = x[idkey]
        if k not in best or x[valkey] > best[k]: best[k] = x[valkey]
    c = {}
    for v in best.values():
        t = tierfn(v); c[t] = c.get(t,0)+1
    return c

# ================= 출력 =================
def table(title, order, data, idkey, valkey, tierfn, base):
    print("\n" + "="*74)
    print(title)
    print("="*74)
    abib_pub = pub_dist(data, valkey, tierfn)
    abib_uniq = uniq_dist(data, idkey, valkey, tierfn)
    ap, atot = pct_dist(abib_pub, order)
    au, autot = pct_dist(abib_uniq, order)
    bp, btot = pct_dist(base, order)
    print(f"{'체급':<8}{'아비브발행':>9}{'아비브%':>9}{'전체%':>9}{'차이pp':>9}{'│유니크':>9}{'유니크%':>9}")
    print("-"*74)
    for k in order:
        diff = ap[k]-bp[k]
        print(f"{k:<8}{abib_pub.get(k,0):>9}{ap[k]:>8.1f}%{bp[k]:>8.1f}%{diff:>+8.1f}{abib_uniq.get(k,0):>9}{au[k]:>8.1f}%")
    print("-"*74)
    print(f"{'합계':<8}{atot:>9}{'100.0%':>9}{'100.0%':>9}{'':>9}{autot:>9}")

# --- 전체 기간 ---
table("YouTube · 전체 기간 (n=%d) · 발행량 기준" % len(yt_valid),
      YT_ORDER, yt_valid, 'channel_id', 'subs', yt_tier, TOP100_YT)
table("Instagram · 전체 기간 (n=%d) · 발행량 기준" % len(ig_valid),
      IG_ORDER, ig_valid, 'user_id', 'followers', ig_tier, TOP100_IG)

# --- 2026 1~6월 (baseline과 동일 기간, 사과 대 사과) ---
yt_h1 = [x for x in yt_valid if in_h1(x['date'])]
ig_h1 = [x for x in ig_valid if in_h1(x['date'])]
table("YouTube · 2026년 1~6월 (n=%d) · baseline 동일기간 ★" % len(yt_h1),
      YT_ORDER, yt_h1, 'channel_id', 'subs', yt_tier, TOP100_YT)
table("Instagram · 2026년 1~6월 (n=%d) · baseline 동일기간 ★" % len(ig_h1),
      IG_ORDER, ig_h1, 'user_id', 'followers', ig_tier, TOP100_IG)

# ============================================================
#  유가 / 무가 분석  (유가 = product_ppl==1, 무가 = 0 또는 NULL)
# ============================================================
# baseline 세그먼트 (무가, 유가)  출처: 카드뉴스_TOP100_체급별발행량.html
TOP100_YT_SEG = {'나노':(14742,3393),'마이크로':(9093,2759),'미드티어':(5953,2229),'매크로':(924,587),'메가':(1041,304)}
TOP100_IG_SEG = {'나노':(16410,8937),'마이크로':(5316,9429),'미드티어':(1697,3837),'하이티어':(1297,2726),'매크로':(541,1230),'메가':(99,207),'셀럽':(45,114)}

def is_paid(x):
    return x['ppl'] == 1   # NULL/0 = 무가

def paid_overall(data):
    paid = sum(1 for x in data if is_paid(x)); tot = len(data)
    return paid, tot, (paid/tot*100 if tot else 0)

def base_overall(seg):
    free = sum(v[0] for v in seg.values()); paid = sum(v[1] for v in seg.values())
    tot = free+paid
    return paid, tot, paid/tot*100

def paid_table(title, order, data, valkey, tierfn, seg):
    print("\n" + "="*74)
    print(title)
    print("="*74)
    # per-tier
    cnt = {k:[0,0] for k in order}  # [tot, paid]
    for x in data:
        t = tierfn(x[valkey]); cnt[t][0]+=1
        if is_paid(x): cnt[t][1]+=1
    print(f"{'체급':<8}{'아비브n':>8}{'유가':>6}{'아비브유가%':>11}{'전체유가%':>10}{'차이pp':>9}")
    print("-"*74)
    for k in order:
        tot,paid = cnt[k]
        ap = paid/tot*100 if tot else 0
        bf,bp = seg[k]; bpct = bp/(bf+bp)*100
        print(f"{k:<8}{tot:>8}{paid:>6}{ap:>10.1f}%{bpct:>9.1f}%{ap-bpct:>+8.1f}")
    print("-"*74)
    ap_n, ap_t, ap_pct = paid_overall(data)
    bp_n, bp_t, bp_pct = base_overall(seg)
    print(f"{'전체':<8}{ap_t:>8}{ap_n:>6}{ap_pct:>10.1f}%{bp_pct:>9.1f}%{ap_pct-bp_pct:>+8.1f}")
    print(f"  → 아비브 유가 {ap_pct:.1f}% / 무가 {100-ap_pct:.1f}%   |   전체 유가 {bp_pct:.1f}% / 무가 {100-bp_pct:.1f}%")

paid_table("YouTube · 유가/무가 · 2026년 1~6월 ★", YT_ORDER, yt_h1, 'subs', yt_tier, TOP100_YT_SEG)
paid_table("YouTube · 유가/무가 · 전체기간", YT_ORDER, yt_valid, 'subs', yt_tier, TOP100_YT_SEG)
paid_table("Instagram · 유가/무가 · 2026년 1~6월 ★", IG_ORDER, ig_h1, 'followers', ig_tier, TOP100_IG_SEG)
paid_table("Instagram · 유가/무가 · 전체기간", IG_ORDER, ig_valid, 'followers', ig_tier, TOP100_IG_SEG)
