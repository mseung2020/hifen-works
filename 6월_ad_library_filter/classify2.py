# -*- coding: utf-8 -*-
import csv

def norm(s):
    if s is None: return ''
    s = s.strip()
    return '' if s == 'NULL' else s

# 브랜드 테이블 (신뢰 축)
brand = set()
with open('brands.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        for v in (norm(row['brand_name_kr']), norm(row['brand_name_en'])):
            if v: brand.add(v)
        rel = norm(row['related_brands'])
        if rel:
            for item in rel.split(','):
                item = item.strip()
                if item: brand.add(item)

# 유저 테이블 (보조 축)
user = set()
with open('users.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        for v in (norm(row['user_id']), norm(row['username'])):
            if v: user.add(v)

buckets = {
    'normal'        : 0,  # 정상 확정: bpn=브랜드, pt≠브랜드
    'reversed'      : 0,  # 반대 확정: pt=브랜드, bpn≠브랜드
    'both_brand'    : 0,  # 둘 다 브랜드 → 수동
    'neither_brand' : 0,  # 둘 다 브랜드 아님 (유저 보조판단 대상)
}
# neither_brand 세부 (유저 보조)
nb = {'normal_guess':0, 'reversed_guess':0, 'both_user':0, 'unmatched':0}

total = 0
with open('라이브러리.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        total += 1
        bpn = norm(row['branded_page_name'])
        pt  = norm(row['page_title'])
        b_isbrand = bpn in brand
        p_isbrand = pt in brand

        if b_isbrand and not p_isbrand:
            buckets['normal'] += 1
        elif p_isbrand and not b_isbrand:
            buckets['reversed'] += 1
        elif b_isbrand and p_isbrand:
            buckets['both_brand'] += 1
        else:
            buckets['neither_brand'] += 1
            b_isuser = bpn in user
            p_isuser = pt in user
            if p_isuser and not b_isuser:
                nb['normal_guess'] += 1      # pt=유저, bpn=정체불명 → 정상 추정
            elif b_isuser and not p_isuser:
                nb['reversed_guess'] += 1     # bpn=유저, pt=정체불명 → 반대 추정
            elif b_isuser and p_isuser:
                nb['both_user'] += 1
            else:
                nb['unmatched'] += 1

print('총 행수: {:,}'.format(total))
print('='*50)
print('[브랜드 테이블 기준 1차 분류]')
print('  정상 확정 (bpn=브랜드, pt≠브랜드) : {:,}'.format(buckets['normal']))
print('  반대 확정 (pt=브랜드, bpn≠브랜드) : {:,}'.format(buckets['reversed']))
print('  둘 다 브랜드 (수동)              : {:,}'.format(buckets['both_brand']))
print('  둘 다 브랜드 아님               : {:,}'.format(buckets['neither_brand']))
print()
print('[둘 다 브랜드 아님 → 유저 테이블 보조판단]')
print('  정상 추정 (pt=유저, bpn=불명)    : {:,}'.format(nb['normal_guess']))
print('  반대 추정 (bpn=유저, pt=불명)    : {:,}'.format(nb['reversed_guess']))
print('  둘 다 유저 (수동)               : {:,}'.format(nb['both_user']))
print('  완전 미매칭                    : {:,}'.format(nb['unmatched']))
print()
print('='*50)
print('[최종 집계]')
norm_total = buckets['normal'] + nb['normal_guess']
rev_total  = buckets['reversed'] + nb['reversed_guess']
manual     = buckets['both_brand'] + nb['both_user']
unmatched  = nb['unmatched']
print('  ✅ 정상  : {:,} ({:.1f}%)'.format(norm_total, 100*norm_total/total))
print('  🔄 반대  : {:,} ({:.1f}%)'.format(rev_total, 100*rev_total/total))
print('  ❓ 수동  : {:,} ({:.1f}%)'.format(manual, 100*manual/total))
print('  ⬜ 미매칭: {:,} ({:.1f}%)'.format(unmatched, 100*unmatched/total))
