# -*- coding: utf-8 -*-
"""brands_extra.csv 만 브랜드 참조로 사용해 라이브러리 전체 검증 → 플래그 CSV 출력"""
import csv, unicodedata

BRANDS = 'brands_extra.csv'
USERS  = 'users.csv'
LIB    = '라이브러리.csv'
OUT    = '라이브러리_검증_extra.csv'

def norm(s):
    if s is None: return ''
    s = unicodedata.normalize('NFKC', s).strip()
    return '' if s == 'NULL' else s

# 브랜드 셋 (brands_extra.csv 전용)
brand = set()
with open(BRANDS, encoding='utf-8') as f:
    for row in csv.DictReader(f):
        for v in (norm(row['brand_name_kr']), norm(row['brand_name_en'])):
            if v: brand.add(v)
        rel = norm(row['related_brands'])
        if rel:
            for item in rel.split(','):
                item = item.strip()
                if item: brand.add(item)

# 유저 셋
user = set()
with open(USERS, encoding='utf-8') as f:
    for row in csv.DictReader(f):
        for v in (norm(row['user_id']), norm(row['username'])):
            if v: user.add(v)

OUTCOLS = ['lib_id','branded_content','branded_page_name','page_id','page_url',
           'page_title','Bp','Bu','Ub','Up']

total = 0
cnt = {'Bp':0,'Bu':0,'Ub':0,'Up':0}
with open(LIB, encoding='utf-8') as fin, open(OUT,'w',encoding='utf-8',newline='') as fout:
    reader = csv.DictReader(fin)
    writer = csv.DictWriter(fout, fieldnames=OUTCOLS)
    writer.writeheader()
    for row in reader:
        total += 1
        bpn = norm(row['branded_page_name'])
        pt  = norm(row['page_title'])
        Bu = 1 if bpn in brand else 0   # branded_page_name ∈ 브랜드
        Bp = 1 if pt  in brand else 0   # page_title       ∈ 브랜드
        Ub = 1 if bpn in user  else 0   # branded_page_name ∈ 유저
        Up = 1 if pt  in user  else 0   # page_title       ∈ 유저
        for k,v in (('Bp',Bp),('Bu',Bu),('Ub',Ub),('Up',Up)):
            cnt[k]+=v
        writer.writerow({
            'lib_id': row.get('lib_id',''),
            'branded_content': row.get('branded_content',''),
            'branded_page_name': row.get('branded_page_name',''),
            'page_id': row.get('page_id',''),
            'page_url': row.get('page_url',''),
            'page_title': row.get('page_title',''),
            'Bp':Bp,'Bu':Bu,'Ub':Ub,'Up':Up,
        })

print('총 {:,}행 → {}'.format(total, OUT))
print('브랜드 참조: {} (브랜드 문자열 {:,}개)'.format(BRANDS, len(brand)))
print('-'*45)
print('Bu (branded_page_name∈브랜드): {:>6,} ({:.1f}%)'.format(cnt['Bu'],100*cnt['Bu']/total))
print('Bp (page_title∈브랜드)       : {:>6,} ({:.1f}%)'.format(cnt['Bp'],100*cnt['Bp']/total))
print('Ub (branded_page_name∈유저)  : {:>6,} ({:.1f}%)'.format(cnt['Ub'],100*cnt['Ub']/total))
print('Up (page_title∈유저)         : {:>6,} ({:.1f}%)'.format(cnt['Up'],100*cnt['Up']/total))
