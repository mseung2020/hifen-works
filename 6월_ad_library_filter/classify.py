# -*- coding: utf-8 -*-
import csv

def norm(s):
    if s is None: return ''
    s = s.strip()
    return '' if s == 'NULL' else s

# 브랜드 테이블
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

# 유저 테이블
user = set()
with open('users.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        for v in (norm(row['user_id']), norm(row['username'])):
            if v: user.add(v)

# 분류
buckets = {
    'correct'   : 0,  # 정상 (그대로 둠)
    'reversed'  : 0,  # 반대 (스왑 필요)
    'ambiguous' : 0,  # 점수 동점 & 둘 다 매칭 신호 있음 (판별 불가)
    'unmatched' : 0,  # 어느 쪽도 매칭 신호 없음
}

with open('라이브러리.csv', encoding='utf-8') as f:
    total = 0
    for row in csv.DictReader(f):
        total += 1
        bpn = norm(row['branded_page_name'])
        pt  = norm(row['page_title'])

        b_in_brand = bpn in brand
        b_in_user  = bpn in user
        p_in_brand = pt in brand
        p_in_user  = pt in user

        correct_score  = (1 if b_in_brand else 0) + (1 if p_in_user  else 0)
        reversed_score = (1 if b_in_user  else 0) + (1 if p_in_brand else 0)

        if correct_score == 0 and reversed_score == 0:
            buckets['unmatched'] += 1
        elif correct_score > reversed_score:
            buckets['correct'] += 1
        elif reversed_score > correct_score:
            buckets['reversed'] += 1
        else:  # 동점 (둘 다 1 이상)
            buckets['ambiguous'] += 1

print('총 행수: {:,}'.format(total))
print('-'*40)
print('정상 (그대로)        : {:,} ({:.1f}%)'.format(buckets['correct'],   100*buckets['correct']/total))
print('반대 (스왑 필요)     : {:,} ({:.1f}%)'.format(buckets['reversed'],  100*buckets['reversed']/total))
print('판별불가 (동점)      : {:,} ({:.1f}%)'.format(buckets['ambiguous'], 100*buckets['ambiguous']/total))
print('미매칭 (단서 없음)   : {:,} ({:.1f}%)'.format(buckets['unmatched'], 100*buckets['unmatched']/total))
