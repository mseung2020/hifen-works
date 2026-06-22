-- ============================================================
-- 릴리바이레드 마케팅 대시보드용 데이터 추출 쿼리
-- ============================================================
-- 공통 조건: 릴리바이레드 CSV에 있는 channel_id 기준
-- 아래 쿼리에서 {CHANNEL_IDS}는 릴리바이레드 CSV의 channel_id 목록으로 대체하세요
-- 또는 임시 테이블로 먼저 넣고 JOIN 하셔도 됩니다


-- ============================================================
-- [요청 1] 릴리바이레드 크리에이터들의 "모든 브랜드 협업 영상"
-- 목적: 경쟁사 자동 탐지 (같은 크리에이터가 어떤 브랜드와도 일하는지)
-- ============================================================
SELECT
    b.channel_id,
    b.channel_title,
    b.brand1,
    b.brand2,
    b.brand3,
    b.video_id,
    b.views,
    b.likes,
    b.comments,
    b.subscribers,
    b.publishDate,
    b.cpv,
    b.title
FROM brand b
WHERE b.channel_id IN ({CHANNEL_IDS});


-- ============================================================
-- [요청 2] 크리에이터 상세 통계
-- 목적: 크리에이터 성과 분석, 버블차트, 효율 매트릭스
-- ============================================================
SELECT
    ys.channel_id,
    ys.average_views,
    ys.average_views_ads,
    ys.average_views_except_short,
    ys.average_views_short,
    ys.engagement_rate,
    ys.engagement_rate_last_10,
    ys.subs_growth_3_months,
    ys.subs_growth_3_months_amount,
    ys.short_ratio,
    ys.total_videos,
    ys.trend_count,
    ys.format1_long,
    ys.format1_short,
    ys.topic1_long,
    ys.topic1_short,
    ys.topic2_long,
    ys.topic2_short
FROM youtuber_stats ys
WHERE ys.channel_id IN ({CHANNEL_IDS});


-- ============================================================
-- [요청 3] 시청자 인구통계 (성별 x 연령대)
-- 목적: 오디언스 인사이트, 인구 피라미드
-- ============================================================
SELECT
    d.channel_id,
    d.F13_17,
    d.F18_24,
    d.F25_34,
    d.F35_44,
    d.F45_54,
    d.F55_64,
    d.F65,
    d.M13_17,
    d.M18_24,
    d.M25_34,
    d.M35_44,
    d.M45_54,
    d.M55_64,
    d.M65
FROM demography d
WHERE d.channel_id IN ({CHANNEL_IDS});


-- ============================================================
-- [요청 4] 브랜드 기본 정보 (뷰티 관련)
-- 목적: 경쟁사 프로필, 브랜드 비교
-- ============================================================
SELECT
    bl.brand_logo_id,
    bl.brand_name_kr,
    bl.brand_name_en,
    bl.brand_videos,
    bl.avg_views,
    bl.one_month,
    bl.topic,
    bl.related_brands
FROM brand_logo bl
WHERE bl.topic LIKE '%beauty%'
   OR bl.topic LIKE '%makeup%'
   OR bl.topic LIKE '%cosmetic%'
   OR bl.topic LIKE '%뷰티%'
   OR bl.topic LIKE '%메이크업%'
   OR bl.topic LIKE '%화장%';
