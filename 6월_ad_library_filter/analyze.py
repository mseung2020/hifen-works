# -*- coding: utf-8 -*-
import csv

def norm(s):
    if s is None:
        return ''
    s = s.strip()
    if s == 'NULL':
        return ''
    return s

# ---------------- 브랜드 테이블 적재 ----------------
brand_kr = set()
brand_en = set()
brand_related = set()
with open('brands.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        kr = norm(row['brand_name_kr'])
        en = norm(row['brand_name_en'])
        rel = norm(row['related_brands'])
        if kr: brand_kr.add(kr)
        if en: brand_en.add(en)
        if rel:
            for item in rel.split(','):
                item = item.strip()
                if item:
                    brand_related.add(item)

def find_in_brands(v):
    """우선순위 kr -> en -> related. 포착된 컬럼명 반환, 없으면 None"""
    if not v:
        return None
    if v in brand_kr: return 'brand_name_kr'
    if v in brand_en: return 'brand_name_en'
    if v in brand_related: return 'related_brands'
    return None

# ---------------- 유저 테이블 적재 ----------------
user_id_set = set()
username_set = set()
with open('users.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        uid = norm(row['user_id'])
        un = norm(row['username'])
        if uid: user_id_set.add(uid)
        if un: username_set.add(un)

def find_in_users(v):
    """우선순위 user_id -> username. 포착된 컬럼명 반환, 없으면 None"""
    if not v:
        return None
    if v in user_id_set: return 'user_id'
    if v in username_set: return 'username'
    return None

# ---------------- 라이브러리 분석 ----------------
total = 0
bpn_present = 0
pt_present = 0

# Stat1: branded_page_name -> brands
bpn_brand_col = {'brand_name_kr':0, 'brand_name_en':0, 'related_brands':0}
bpn_brand_hit = 0

# Stat2: page_title -> users
pt_user_col = {'user_id':0, 'username':0}
pt_user_hit = 0

# 미포착(primary 기준 행단위: bpn이 brands에 있고 AND pt가 users에 있으면 포착)
fully_primary = 0
uncaptured_rows = []   # (bpn, pt, bpn_primary_ok, pt_primary_ok)

with open('라이브러리.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        total += 1
        bpn = norm(row['branded_page_name'])
        pt = norm(row['page_title'])
        if bpn: bpn_present += 1
        if pt: pt_present += 1

        bcol = find_in_brands(bpn)
        if bcol:
            bpn_brand_hit += 1
            bpn_brand_col[bcol] += 1

        ucol = find_in_users(pt)
        if ucol:
            pt_user_hit += 1
            pt_user_col[ucol] += 1

        bpn_primary_ok = bcol is not None
        pt_primary_ok = ucol is not None

        if bpn_primary_ok and pt_primary_ok:
            fully_primary += 1
        else:
            uncaptured_rows.append((bpn, pt, bpn_primary_ok, pt_primary_ok))

# ---------------- 미포착 행 역방향 분석 ----------------
# 미포착 행에 한하여: branded_page_name -> users, page_title -> brands
rev_bpn_in_users = 0   # branded_page_name 가 유저 쪽에서 포착
rev_pt_in_brands = 0   # page_title 가 브랜드 쪽에서 포착

# 각 필드의 "최종 포착" = primary OR reverse
both_captured = 0      # 두 필드 모두 최종 포착
one_captured = 0       # 한 필드만 최종 포착
none_captured = 0      # 두 필드 모두 최종 실패

# 최종 필드 단위 실패 수
final_field_fail = 0

for bpn, pt, bpn_primary_ok, pt_primary_ok in uncaptured_rows:
    # branded_page_name 최종 포착: brands(primary) or users(reverse)
    bpn_rev = (not bpn_primary_ok) and (find_in_users(bpn) is not None)
    if bpn_rev:
        rev_bpn_in_users += 1
    bpn_final = bpn_primary_ok or bpn_rev

    # page_title 최종 포착: users(primary) or brands(reverse)
    pt_rev = (not pt_primary_ok) and (find_in_brands(pt) is not None)
    if pt_rev:
        rev_pt_in_brands += 1
    pt_final = pt_primary_ok or pt_rev

    captured_cnt = (1 if bpn_final else 0) + (1 if pt_final else 0)
    if captured_cnt == 2:
        both_captured += 1
    elif captured_cnt == 1:
        one_captured += 1
    else:
        none_captured += 1

    final_field_fail += (0 if bpn_final else 1) + (0 if pt_final else 1)

# ---------------- 출력 ----------------
print('='*60)
print('라이브러리 총 행수: {:,}'.format(total))
print('  - branded_page_name 값 있는 행: {:,}'.format(bpn_present))
print('  - page_title 값 있는 행: {:,}'.format(pt_present))
print()
print('[1] branded_page_name → 브랜드 테이블 포착')
print('  총 {:,}건 중 {:,}건 포착 ({:.1f}%)'.format(total, bpn_brand_hit, 100*bpn_brand_hit/total))
print('  - brand_name_kr  : {:,}'.format(bpn_brand_col['brand_name_kr']))
print('  - brand_name_en  : {:,}'.format(bpn_brand_col['brand_name_en']))
print('  - related_brands : {:,}'.format(bpn_brand_col['related_brands']))
print('  (우선순위 kr→en→related 로 행당 1건만 집계)')
print()
print('[2] page_title → 유저 테이블 포착')
print('  총 {:,}건 중 {:,}건 포착 ({:.1f}%)'.format(total, pt_user_hit, 100*pt_user_hit/total))
print('  - user_id  : {:,}'.format(pt_user_col['user_id']))
print('  - username : {:,}'.format(pt_user_col['username']))
print('  - 미포착   : {:,}'.format(total - pt_user_hit))
print()
print('[행단위 1차 포착] branded_page_name(브랜드) AND page_title(유저) 둘다 포착: {:,}'.format(fully_primary))
print('[행단위 1차 미포착] (둘 중 하나라도 실패): {:,}'.format(len(uncaptured_rows)))
print()
print('[3] 1차 미포착 {:,}행에 한하여 역방향 포착'.format(len(uncaptured_rows)))
print('  - branded_page_name 가 유저 쪽에서 포착: {:,}'.format(rev_bpn_in_users))
print('  - page_title 가 브랜드 쪽에서 포착: {:,}'.format(rev_pt_in_brands))
print()
print('[4] 1차 미포착 행의 최종 결과 (각 필드 = 1차 OR 역방향)')
print('  - 두 필드 모두 최종 포착: {:,}'.format(both_captured))
print('  - 한 필드만 포착 / 나머지 실패: {:,}'.format(one_captured))
print('  - 두 필드 모두 미포착: {:,}'.format(none_captured))
print('  - 최종 완전 미포착 행(=둘다 실패): {:,}'.format(none_captured))
print('='*60)
