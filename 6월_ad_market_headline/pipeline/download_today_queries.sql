-- =====================================================================
--  오늘자 광고시장 헤드라인 — 최종 인풋 데이터 다운로드 쿼리 (MySQL)
--  작성 2026-06-02 · 범위: 범퍼광고 클러스터 11개 테이블 · KR + 글로벌 병행
-- ---------------------------------------------------------------------
--  설계 원칙
--   1) "오늘치" = DB의 최신 스냅샷 날짜 D (= 각 시계열 테이블의 MAX(date)).
--   2) 헤드라인은 "오늘 vs 직전" 델타가 핵심 → 시계열 테이블은 단일 1일이
--      아니라 [D 포함 최근 WIN일] 윈도우로 받는다 (델타·이상치 계산용).
--   3) 차원/스냅샷 테이블(메타·분석·scene·on_off)은 윈도우 내 '활동한'
--      video_id / channel_id 로 스코프를 좁혀 받는다 (불필요 행 방지).
--   4) 각 쿼리는 독립 실행 가능. 결과를 그대로 data/<테이블>.csv 로 저장.
--   ※ 윈도우 길이 조정: 아래 INTERVAL 14 DAY / 8 WEEK 숫자만 바꾸면 됨.
--     (D-1 단일 비교만 원하면 14 DAY를 1 DAY로)
-- =====================================================================


-- =====================================================================
-- [A] 시계열 — 광고비 / 추세 (윈도우로 받음: 델타 계산의 핵심 재료)
-- =====================================================================

-- A1. 채널 일별 광고비  → data/YT_bumper_cost_per_day.csv
SELECT *
FROM YT_bumper_cost_per_day
WHERE date >= (SELECT MAX(date) FROM YT_bumper_cost_per_day) - INTERVAL 14 DAY
ORDER BY date DESC, cost DESC;

-- A2. 채널 세분 일별 광고비(가로/세로 × b/s/ns/a)  → data/YT_brand_bumper_cost_per_day.csv
SELECT *
FROM YT_brand_bumper_cost_per_day
WHERE date >= (SELECT MAX(date) FROM YT_brand_bumper_cost_per_day) - INTERVAL 14 DAY
ORDER BY date DESC;

-- A3. 채널 주별 광고비(주간 베이스라인)  → data/YT_bumper_cost_per_week.csv
SELECT *
FROM YT_bumper_cost_per_week
WHERE date >= (SELECT MAX(date) FROM YT_bumper_cost_per_week) - INTERVAL 8 WEEK
ORDER BY date DESC, cost DESC;

-- A4. 영상 일별 추세(조회/댓글/좋아요)  → data/YT_bumper_video_trend.csv
SELECT *
FROM YT_bumper_video_trend
WHERE date >= (SELECT MAX(date) FROM YT_bumper_video_trend) - INTERVAL 14 DAY
ORDER BY date DESC, views DESC;

-- A5. 브랜드/영상 추세  → data/YT_brand_video_trend.csv
SELECT *
FROM YT_brand_video_trend
WHERE date >= (SELECT MAX(date) FROM YT_brand_video_trend) - INTERVAL 14 DAY
ORDER BY date DESC, views DESC;


-- =====================================================================
-- [B] 캠페인 상태 — 오늘 켜짐/꺼짐 (이벤트 시점 기준 윈도우)
-- =====================================================================

-- B1. 캠페인 on/off  → data/YT_bumper_on_off.csv
--     최근 윈도우 안에서 시작(start)·종료(end)된 캠페인 + 현재 켜진 캠페인.
SELECT *
FROM YT_bumper_on_off
WHERE start >= (SELECT MAX(date) FROM YT_bumper_video_trend) - INTERVAL 14 DAY
   OR end   >= (SELECT MAX(date) FROM YT_bumper_video_trend) - INTERVAL 14 DAY
   OR is_on = 1
ORDER BY GREATEST(COALESCE(start,'1900-01-01'), COALESCE(end,'1900-01-01')) DESC;


-- =====================================================================
-- [C] 차원/메타 — KR 광고 (윈도우 내 활동 영상/채널로 스코프 축소)
-- =====================================================================
--  '활동' 정의: 최근 윈도우의 video_trend에 등장한 video_id
--               OR cost_per_day에 등장한 channel_id
--               OR 현재 on_air 중인 광고

-- C1. KR 광고 메타  → data/YT_bumper_ad.csv
SELECT *
FROM YT_bumper_ad
WHERE country_code = 'KR'
  AND (
        on_air = 1
     OR video_id IN (
           SELECT DISTINCT video_id FROM YT_bumper_video_trend
           WHERE date >= (SELECT MAX(date) FROM YT_bumper_video_trend) - INTERVAL 14 DAY)
     OR channel_id IN (
           SELECT DISTINCT channel_id FROM YT_bumper_cost_per_day
           WHERE date >= (SELECT MAX(date) FROM YT_bumper_cost_per_day) - INTERVAL 14 DAY)
      )
ORDER BY views DESC;

-- ※ C2/C3 재설계 v4(2026-06-02): on_air=1 스코프는 폐기.
--   [측정] 오늘 트렌드 기준 on_air=1 커버리지: 조회수 Top500 중 88개(82% 손실),
--   떡상 Top500 중 354개(29% 손실). → on_air=1 은 '현재 캠페인 집행 중'만 잡아
--   헤드라인 후보의 맥락을 대거 누락. 커버리지를 희생할 수 없으므로 폐기.
--   대신 느림의 진짜 원인(거대 텍스트 컬럼 전송)만 제거하고 후보 유니버스
--   전체(최근 14일 트렌드 등장 영상)를 커버한다.
--   핵심: ① speech/new_speech/scenes_analized/video_description 등 블롭 제외
--         ② IN(...) 대신 JOIN (distinct 파생집합)  ③ date 필터는 함수 미적용(인덱스 사용)
--   ⚠️ analized/scene 의 video_id 에 인덱스 필수(없으면 풀스캔으로 느려짐).

-- C2. 광고 콘텐츠 AI 분석(감정/카테고리/스토리)  → 최종data/ad_analized.csv
--     스코프: 최근 14일 트렌드에 등장한 '모든' 영상 (후보 유니버스 = 손실 0).
SELECT a.video_id, a.title, a.brand, a.emotion, a.category,
       a.ad_story, a.labels, a.countries
FROM YT_bumper_ad_analized a
JOIN (
    SELECT DISTINCT video_id
    FROM YT_bumper_video_trend
    WHERE date >= (SELECT MAX(date) FROM YT_bumper_video_trend) - INTERVAL 14 DAY
) v ON v.video_id = a.video_id;

-- C3. 장면 단위 묘사(맥락용)  → 최종data/scene.csv
--     스코프: C2와 동일 유니버스. image1만(image2/3 제외).
SELECT s.video_id, s.scene_id, s.start, s.end, s.description, s.image1
FROM YT_bumper_scene s
JOIN (
    SELECT DISTINCT video_id
    FROM YT_bumper_video_trend
    WHERE date >= (SELECT MAX(date) FROM YT_bumper_video_trend) - INTERVAL 14 DAY
) v ON v.video_id = s.video_id
ORDER BY s.video_id, s.start;

-- ── (권장) 2-phase: 손실 0 + 최速 ───────────────────────────────────
--  analized/scene 는 결국 '최종 헤드라인 후보(수십~수백)'에만 쓰임.
--  ① 나머지 9개로 파이프라인을 돌려 후보 video_id 목록을 확정한 뒤
--  ② 아래처럼 그 목록만 받는다 (가장 빠르고 한 톨도 안 버림):
--     SELECT video_id,title,brand,emotion,category,ad_story,labels,countries
--     FROM YT_bumper_ad_analized
--     WHERE video_id IN ('vid1','vid2', ... /* 파이프라인이 고른 후보 */);
--  scene 도 동일하게 WHERE video_id IN (...) 로.


-- =====================================================================
-- [D] 차원/메타 — 글로벌 광고 (병행)
-- =====================================================================
--  ⚠️ 한계: 글로벌은 일별 추세 테이블이 없음(ad_global의 views/likes는 누적
--     스냅샷). 따라서 글로벌은 '오늘 떡상' 델타가 아니라 '누적 상위/신규' 류
--     스냅샷 헤드라인 재료로만 사용 가능. (델타가 필요하면 글로벌 트렌드
--     소스 별도 확보 필요 — 추후 결정.)

-- D1. 글로벌 광고 메타  → data/YT_bumper_ad_global.csv
--     스코프: 분석 완료(analized=1)된 글로벌 광고 중 조회수 상위.
--     (전수가 너무 크면 LIMIT으로 상위만. 필요시 countries 필터 추가)
SELECT *
FROM YT_bumper_ad_global
WHERE analized = 1
ORDER BY views DESC
LIMIT 500;


-- =====================================================================
-- [E] 벤치마크 — 산업별 CPM (스냅샷 전수)
-- =====================================================================

-- E1. 산업별 CPM/VTR  → data/YT_bumper_cpm_by_industry.csv
SELECT *
FROM YT_bumper_cpm_by_industry
ORDER BY average DESC;
