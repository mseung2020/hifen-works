# -*- coding: utf-8 -*-
"""
라이브러리 컬럼 오류(브랜드/유저 뒤바뀜) 감지 파이프라인
-------------------------------------------------------
입력: 라이브러리 CSV (branded_page_name, page_title 컬럼 필요)
참조: brands.csv, users.csv
출력: 행별 verdict / confidence / reason 가 붙은 검증 CSV + 요약 통계

원리
  - branded_page_name 자리에는 '브랜드', page_title 자리에는 '유저'가 와야 정상.
  - 브랜드 테이블(소규모·정제)은 신뢰 신호, 유저 테이블(대규모)은 약한(노이즈) 신호.
  - 4개 신호로 판정: Bb,Ub,Bp,Up = (bpn∈brand, bpn∈user, pt∈brand, pt∈user)
"""
import csv, sys, unicodedata

BRANDS = 'brands.csv'
USERS  = 'users.csv'

def norm(s):
    """비교용 정규화: NFKC + 앞뒤공백 제거 + NULL 처리"""
    if s is None: return ''
    s = unicodedata.normalize('NFKC', s).strip()
    return '' if s == 'NULL' else s

def load_brands(path):
    brand = set()
    with open(path, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            for v in (norm(row['brand_name_kr']), norm(row['brand_name_en'])):
                if v: brand.add(v)
            rel = norm(row['related_brands'])
            if rel:
                for item in rel.split(','):
                    item = item.strip()
                    if item: brand.add(item)
    return brand

def load_users(path):
    user = set()
    with open(path, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            for v in (norm(row['user_id']), norm(row['username'])):
                if v: user.add(v)
    return user

def classify(bpn, pt, brand, user):
    """행 1건 판정 → (verdict, confidence, reason)"""
    Bb = bpn in brand          # branded_page_name 이 브랜드?
    Ub = bpn in user           # branded_page_name 이 유저?
    Bp = pt  in brand          # page_title 가 브랜드?
    Up = pt  in user           # page_title 가 유저?

    # ── 1) 스왑(반대) 감지 : 브랜드 신호 우선 ───────────────────
    # page_title 이 브랜드이고 branded_page_name 은 브랜드가 아님 → 브랜드가 엉뚱한 칸에
    if Bp and not Bb:
        if Up:
            # page_title 이 브랜드이자 유저이기도 함 → 단정 불가
            return ('REVIEW', 'low', 'page_title가 브랜드/유저 양쪽에 존재(모호)')
        if Ub:
            # bpn=유저 & pt=브랜드 : 양방향 신호 일치 → 가장 확실한 스왑
            return ('SWAP', 'high', 'page_title=브랜드 & branded_page_name=유저 (양방향 일치)')
        return ('SWAP', 'high', 'page_title 자리에 등록된 브랜드가 있음')

    # ── 2) 정상 확정 : branded_page_name 이 브랜드, page_title 은 브랜드 아님 ──
    if Bb and not Bp:
        return ('OK', 'high', 'branded_page_name=브랜드 (정상)')

    # ── 3) 둘 다 브랜드 → 사람이 확인 ─────────────────────────
    if Bb and Bp:
        return ('REVIEW', 'low', '두 컬럼 모두 브랜드명')

    # ── 여기부터 둘 다 '브랜드 아님' : 유저 테이블(약한 신호)로 보조판단 ──
    # 4) bpn=유저, pt≠유저 → bpn 에 유저가 들어간 듯 → 스왑 의심
    if Ub and not Up:
        return ('SWAP', 'medium', 'branded_page_name가 유저 핸들 (브랜드 단서 없음)')
    # 5) pt=유저, bpn≠유저 → 정상 추정 (bpn 은 미등록 브랜드 가능성)
    if Up and not Ub:
        return ('OK', 'medium', 'page_title=유저, branded_page_name=미등록 브랜드 추정')
    # 6) 둘 다 유저 → 모호
    if Ub and Up:
        return ('REVIEW', 'low', '두 컬럼 모두 유저로 매칭(모호)')
    # 7) 아무 데도 매칭 안 됨 → 검증 불가(신규/오타/삭제)
    return ('UNVERIFIABLE', 'none', '브랜드·유저 어디에도 매칭 없음')

def main(lib_path, out_path='라이브러리_검증.csv'):
    brand = load_brands(BRANDS)
    user  = load_users(USERS)

    from collections import Counter
    vcount = Counter(); rcount = Counter()
    total = 0
    with open(lib_path, encoding='utf-8') as fin, \
         open(out_path, 'w', encoding='utf-8', newline='') as fout:
        reader = csv.DictReader(fin)
        fields = reader.fieldnames + ['verdict', 'confidence', 'reason']
        writer = csv.DictWriter(fout, fieldnames=fields)
        writer.writeheader()
        for row in reader:
            total += 1
            bpn = norm(row['branded_page_name'])
            pt  = norm(row['page_title'])
            verdict, conf, reason = classify(bpn, pt, brand, user)
            row['verdict'], row['confidence'], row['reason'] = verdict, conf, reason
            writer.writerow(row)
            vcount[verdict] += 1
            rcount[(verdict, conf)] += 1

    print('총 {:,}행 → {}'.format(total, out_path))
    print('-'*50)
    order = ['OK', 'SWAP', 'REVIEW', 'UNVERIFIABLE']
    for v in order:
        print('  {:13s}: {:>6,} ({:.1f}%)'.format(v, vcount[v], 100*vcount[v]/total))
    print('-'*50)
    print('신뢰도별:')
    for (v,c),n in sorted(rcount.items(), key=lambda x:-x[1]):
        print('  {:13s} [{:6s}]: {:>6,}'.format(v, c, n))

if __name__ == '__main__':
    lib = sys.argv[1] if len(sys.argv) > 1 else '라이브러리.csv'
    main(lib)
