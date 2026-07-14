# -*- coding: utf-8 -*-
import csv
from collections import Counter

def norm(s):
    if s is None: return ''
    s = s.strip()
    return '' if s == 'NULL' else s

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

user = set()
with open('users.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        for v in (norm(row['user_id']), norm(row['username'])):
            if v: user.add(v)

amb_patterns = Counter()
amb_examples = {}

with open('라이브러리.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        bpn = norm(row['branded_page_name'])
        pt  = norm(row['page_title'])
        b_in_brand = bpn in brand
        b_in_user  = bpn in user
        p_in_brand = pt in brand
        p_in_user  = pt in user
        correct  = (1 if b_in_brand else 0) + (1 if p_in_user else 0)
        reversed_= (1 if b_in_user  else 0) + (1 if p_in_brand else 0)
        if correct >= 1 and correct == reversed_:
            # 패턴 키: bpn이 (B/U/BU), pt가 (B/U/BU)
            def tag(in_b, in_u):
                if in_b and in_u: return 'BU'
                if in_b: return 'B'
                if in_u: return 'U'
                return '-'
            key = 'bpn={} / pt={}'.format(tag(b_in_brand,b_in_user), tag(p_in_brand,p_in_user))
            amb_patterns[key]+=1
            if key not in amb_examples:
                amb_examples[key] = (bpn, pt)

print('판별불가(동점) 세부 패턴:')
print('  (B=브랜드만, U=유저만, BU=양쪽다)')
for k,c in amb_patterns.most_common():
    ex = amb_examples[k]
    print('  {:18s}: {:>5,}   예) bpn={!r}  pt={!r}'.format(k, c, ex[0], ex[1]))
