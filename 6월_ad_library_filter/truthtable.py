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

combos = Counter()
examples = {}
with open('라이브러리.csv', encoding='utf-8') as f:
    total=0
    for row in csv.DictReader(f):
        total+=1
        bpn = norm(row['branded_page_name'])
        pt  = norm(row['page_title'])
        sig = (bpn in brand, bpn in user, pt in brand, pt in user)
        combos[sig]+=1
        if sig not in examples:
            examples[sig]=(bpn,pt)

def fmt(b):
    return '✔' if b else '·'

print('총 {:,}행'.format(total))
print('Bb Ub | Bp Up |  건수  | 예시')
print('-'*70)
for sig,c in sorted(combos.items(), key=lambda x:-x[1]):
    Bb,Ub,Bp,Up = sig
    ex = examples[sig]
    print(' {}  {}  |  {}  {} | {:>6,} | bpn={!r:30.30} pt={!r}'.format(
        fmt(Bb),fmt(Ub),fmt(Bp),fmt(Up), c, ex[0], ex[1]))
