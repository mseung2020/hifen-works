import csv
import re
from collections import Counter

# 불용어 목록
STOPWORDS = {
    # 브랜드명 자체
    '넘버즈인', '넘버스인', 'numbuzin',
    # 광고 공시 표기
    '광고', '유료광고', '제작지원', '협찬', '제품제공', '소정의', '대가',
    'ad', 'pr', 'sponsored',
    # 해시태그 일반어
    'fyp', 'foryou', '릴스', '인스타그램', '인스타',
    # 지시어/대명사
    '이거', '저거', '그거', '이것', '저것', '그것', '여기', '거기',
    '이건', '저건', '그건',
    # 부사/감탄사
    '진짜', '정말', '너무', '완전', '그냥', '이제', '아직', '벌써',
    '되게', '엄청', '약간', '거의', '조금', '좀', '바로', '요즘',
    '특히', '그대로', '같이', '지금', '이번', '이번에',
    # 조사 결합형 (형태소 분석 없이 자주 나오는 것)
    '피부가', '피부를', '피부에', '피부의',
    '있어요', '있는데', '없이', '없어요',
    '제가', '저는', '저도',
    # 일반 동사/형용사 어간
    '있는', '없는', '하는', '이런', '저런', '그런',
    # 숫자 단위 단독
    '개', '원', '번', '명',
    # 기타 의미없는 단어
    '것', '수', '때', '후', '전', '중', '등', '및', '또', '더',
    # 크리에이터 닉네임
    '망곰',
    # 해시태그 복합어
    '화잘먹',
    # 연결어/접속어
    '그래서', '그리고', '하지만', '그런데', '근데', '그러면', '그러니까',
    '함께', '다들', '분들', '이상', '이하',
    # 조사 결합형 추가
    '피부결이', '느낌이', '사용하고', '사용해',
    # 시간 부사
    '전에', '오늘', '내일', '어제', '매일',
    # 범용 단어 (어느 광고에나 나오는 것)
    '시간', '제품', '사용', '쓰면', '유명한',
    # 프로모션 공지성 (브랜드 언어 특성 아님)
    '할인', '기간', '최대', '단독', '증정', '출시', '마켓', '공식몰',
    '기획세트', '리필', '구매',
}

# 동의어 통합 (key → 대표어로 치환)
SYNONYMS = {
    '올영': '올리브영',
    '올영라': '올리브영',
    '쫀쫀': '쫀쫀함',
    '보들보들': '보들보들',
}

def extract_korean_words(text):
    words = re.findall(r'[가-힣]{2,}', text)
    return [SYNONYMS.get(w, w) for w in words]

def main():
    rows = []
    with open('data/분석대상_한국어_좋아요100이상.csv', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    all_words = []
    for r in rows:
        caption = r.get('caption_full') or ''
        words = extract_korean_words(caption)
        filtered = [w for w in words if w not in STOPWORDS]
        all_words.extend(filtered)

    counter = Counter(all_words)
    top100 = counter.most_common(100)

    print(f"총 단어 수 (중복 포함): {len(all_words):,}")
    print(f"고유 단어 수: {len(counter):,}")
    print("\n=== 상위 50개 단어 ===")
    for word, count in top100[:50]:
        print(f"{word}: {count}")

    # CSV 저장
    with open('data/word_frequency.csv', 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['word', 'count'])
        writer.writerows(top100)

    print("\n저장 완료: data/word_frequency.csv")

if __name__ == '__main__':
    main()
