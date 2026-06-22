#!/usr/bin/env python3
"""
L2 후보 풀 생성기 v3 — 광고시장 헤드라인용 LLM 인풋.
KR_ONLY=True 면 국내(country_code='KR') 시장 데이터만으로 후보 구성(글로벌 제외).
숫자=SQL이 계산, 해석=LLM. 부분일/깨진 날 자동 제외(총량<중앙값50%), D=완전 최신 공통일.
출력: 최종data/llm_input_<D>[_kr].json
"""
import duckdb, json, os, statistics

KR_ONLY = True   # ← 국내만

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "최종data")
def p(name): return os.path.join(BASE, name)
RC = "read_csv('{}', header=true, ignore_errors=true, strict_mode=false, all_varchar=true, sample_size=-1)"
con = duckdb.connect()
con.execute(f"CREATE TABLE ad AS SELECT * FROM {RC.format(p('bumper_ad.csv'))}")
con.execute(f"CREATE TABLE an AS SELECT * FROM {RC.format(p('ad_analized.csv'))}")
con.execute(f"CREATE TABLE g  AS SELECT * FROM {RC.format(p('ad_global.csv'))}")
con.execute(f"""CREATE TABLE vt AS SELECT video_id, CAST("date" AS DATE) d, MAX(TRY_CAST(views AS BIGINT)) v
  FROM {RC.format(p('bumper_video_trend.csv'))} GROUP BY video_id, CAST("date" AS DATE)""")
con.execute(f"""CREATE TABLE cpd AS SELECT channel_id, CAST("date" AS DATE) d, TRY_CAST("cost" AS DOUBLE) cst
  FROM {RC.format(p('cost_per_day.csv'))}""")
con.execute(f"""CREATE TABLE oo AS SELECT video_id, channel_id, CAST(NULLIF("start",'NULL') AS DATE) s, CAST(NULLIF("end",'NULL') AS DATE) e
  FROM {RC.format(p('on_off.csv'))}""")

def rows(sql):
    cur = con.execute(sql); cols=[c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]
def complete_days(table, measure):
    r = rows(f"SELECT d, {measure} m FROM {table} GROUP BY d ORDER BY d")
    med = statistics.median([x["m"] for x in r if x["m"] and x["m"]>0])
    return sorted([x["d"] for x in r if x["m"] and x["m"]>=0.5*med])

cost_days  = complete_days("cpd","sum(cst)")
trend_days = complete_days("vt","count(*)")
D = sorted(set(cost_days) & set(trend_days))[-1]
base_cost = [d for d in cost_days if d<D][-13:]
def lit(days): return ",".join(f"DATE '{d}'" for d in days)
COSTB = lit(base_cost); TRENDALL = lit([d for d in trend_days if d<=D])

# 매핑
con.execute("""CREATE TABLE bmap AS SELECT channel_id, brand FROM (
  SELECT channel_id, brand1 brand, row_number() OVER (PARTITION BY channel_id ORDER BY count(*) DESC) rn
  FROM ad WHERE brand1 NOT IN ('NULL','') AND brand1 IS NOT NULL GROUP BY channel_id, brand1) WHERE rn=1""")
con.execute("""CREATE TABLE vmeta AS SELECT video_id, any_value(title) title, any_value(brand) brand,
  any_value(category) category, any_value(emotion) emotion, substr(any_value(ad_story),1,160) story FROM an GROUP BY video_id""")
con.execute("""CREATE TABLE vch AS SELECT video_id, any_value(channel_id) channel_id FROM ad GROUP BY video_id""")
# KR 시장 집합
con.execute("CREATE TABLE krch AS SELECT DISTINCT channel_id FROM ad WHERE country_code='KR'")
con.execute("CREATE TABLE krvid AS SELECT DISTINCT video_id FROM ad WHERE country_code='KR'")
con.execute("""CREATE TABLE adkr AS SELECT video_id, any_value(brand1) brand, any_value(title) title
  FROM ad WHERE country_code='KR' GROUP BY video_id""")
# 채널→대표 KR 광고 크리에이티브
KRC = "AND a.country_code='KR'" if KR_ONLY else ""
con.execute(f"""CREATE TABLE chcre AS SELECT channel_id, title, story FROM (
  SELECT a.channel_id, a.title, (SELECT any_value(ad_story) FROM an WHERE an.video_id=a.video_id) story,
    row_number() OVER (PARTITION BY a.channel_id ORDER BY TRY_CAST(a.views AS BIGINT) DESC NULLS LAST) rn
  FROM ad a WHERE a.title NOT IN ('NULL','') {KRC}) WHERE rn=1""")
con.execute(f"""CREATE TABLE rate AS SELECT video_id, d, v, (v-LAG(v) OVER w)*1.0/NULLIF(date_diff('day',LAG(d) OVER w,d),0) r
  FROM vt WHERE d IN ({TRENDALL}) WINDOW w AS (PARTITION BY video_id ORDER BY d)""")

# KR_ONLY 필터 조각
CH = "AND channel_id IN (SELECT channel_id FROM krch)" if KR_ONLY else ""
VID = "AND video_id IN (SELECT video_id FROM krvid)" if KR_ONLY else ""

out = {
  "report_date": str(D), "domain": "YouTube 범퍼(인스트림) 광고 시장",
  "market_scope": "KR ONLY (국내 시장 노출 광고만)" if KR_ONLY else "KR + GLOBAL",
  "data_quality": {"effective_day": str(D), "baseline_cost_days": [str(d) for d in base_cost]},
  "field_notes": {"cost.*":"일 광고비(단위 미확정; 배율·증감이 핵심)",
    "creative/ad_story":"그 광고주 대표 광고 제목/장면 — 제품·작품명은 여기서만",
    "accel_x":"오늘 조회증가속도/직전 평균(baseline≈최근 2주)", "today_per_day":"정상화 1일 신규 조회수"},
  "task_for_llm":"candidates 만 근거로 마케터 후킹 1줄 헤드라인 10개. 모두 국내(KR) 광고. 브랜드·제품명 노골(입력에 있을 때만, 없으면 궁금증 갭). 순위·최상급은 리스트 1위일 때만. 한 브랜드 1회. 숫자 밖 창작 금지. 한국어 ~40자.",
  "candidates": {}
}
C = out["candidates"]

C["cost_movers"] = rows(f"""
  WITH agg AS (SELECT channel_id, MAX(CASE WHEN d=DATE '{D}' THEN cst END) today,
      AVG(CASE WHEN d IN ({COSTB}) THEN cst END) base, COUNT(CASE WHEN d IN ({COSTB}) THEN 1 END) base_days
    FROM cpd WHERE 1=1 {CH} GROUP BY channel_id)
  SELECT COALESCE(b.brand,'(미상)') brand, CAST(round(today) AS BIGINT) today, CAST(round(base) AS BIGINT) baseline,
    CAST(round(today-base) AS BIGINT) delta,
    CASE WHEN base IS NULL OR base<1 THEN NULL ELSE round(100.0*(today-base)/base) END delta_pct,
    base_days, (base IS NULL OR base<1) is_new, substr(cre.title,1,55) creative, substr(cre.story,1,150) ad_story
  FROM agg a LEFT JOIN bmap b USING(channel_id) LEFT JOIN chcre cre USING(channel_id)
  WHERE today IS NOT NULL AND today>20000 ORDER BY abs(today-COALESCE(base,0)) DESC LIMIT 50""")

C["view_accel"] = rows(f"""
  WITH agg AS (SELECT video_id, MAX(CASE WHEN d=DATE '{D}' THEN r END) today_rate,
      AVG(CASE WHEN d<DATE '{D}' THEN r END) base_rate, COUNT(CASE WHEN d<DATE '{D}' THEN r END) nd
    FROM rate GROUP BY video_id)
  SELECT COALESCE(k.brand,'?') brand, substr(COALESCE(k.title,'?'),1,45) title,
    substr((SELECT any_value(ad_story) FROM an WHERE an.video_id=k.video_id),1,120) ad_story,
    CAST(today_rate AS BIGINT) today_per_day, round(today_rate/NULLIF(base_rate,0),1) accel_x
  FROM agg JOIN adkr k USING(video_id)
  WHERE today_rate>=10000 AND base_rate>=1500 AND nd>=4 ORDER BY accel_x DESC LIMIT 30""")

C["top_exposed"] = rows(f"""
  SELECT COALESCE(k.brand,'?') brand, substr(COALESCE(k.title,'?'),1,45) title, CAST(r AS BIGINT) today_per_day
  FROM rate JOIN adkr k USING(video_id) WHERE d=DATE '{D}' AND r>0 ORDER BY r DESC LIMIT 25""")

C["industry_cpm"] = rows(f"""SELECT industry, TRY_CAST(bumper AS INT) bumper, TRY_CAST(average AS INT) average, TRY_CAST(vtr AS DOUBLE) vtr
  FROM {RC.format(p('cpm_by_industry.csv'))} ORDER BY bumper DESC""")

C["category_rollup"] = rows(f"""
  WITH agg AS (SELECT video_id, MAX(CASE WHEN d=DATE '{D}' THEN r END) today_rate, AVG(CASE WHEN d<DATE '{D}' THEN r END) base_rate
    FROM rate WHERE 1=1 {VID} GROUP BY video_id),
  tagged AS (SELECT a.video_id, today_rate, base_rate, trim(lower(unnest(string_split(m.category, ',')))) tag
    FROM agg a JOIN vmeta m USING(video_id) WHERE m.category NOT IN ('NULL','') AND today_rate>0)
  SELECT tag, count(*) n_videos, CAST(sum(today_rate) AS BIGINT) total_today_views,
    sum(CASE WHEN today_rate/NULLIF(base_rate,0)>=1.5 THEN 1 ELSE 0 END) n_accelerating
  FROM tagged WHERE length(tag)>=3 GROUP BY tag HAVING count(*)>=3 ORDER BY total_today_views DESC LIMIT 20""")

con.execute(f"""CREATE TABLE ccost AS SELECT channel_id, MAX(CASE WHEN d=DATE '{D}' THEN cst END) today,
  AVG(CASE WHEN d IN ({COSTB}) THEN cst END) base FROM cpd GROUP BY channel_id""")
C["spotlight"] = rows(f"""
  WITH agg AS (SELECT video_id, MAX(CASE WHEN d=DATE '{D}' THEN r END) tr, AVG(CASE WHEN d<DATE '{D}' THEN r END) br, COUNT(CASE WHEN d<DATE '{D}' THEN r END) nd
    FROM rate WHERE video_id IN (SELECT video_id FROM vmeta WHERE story IS NOT NULL AND story<>'NULL') {VID} GROUP BY video_id),
  ranked AS (SELECT *, tr/NULLIF(br,0) ax, row_number() OVER (ORDER BY tr/NULLIF(br,0) DESC) rk_accel, row_number() OVER (ORDER BY tr DESC) rk_exp FROM agg WHERE tr>=10000 AND nd>=4)
  SELECT COALESCE(NULLIF(m.brand,'NULL'), bm.brand, '?') brand, substr(m.title,1,40) title,
    round(ax,1) accel_x, CAST(tr AS BIGINT) today_per_day,
    CASE WHEN cc2.base>=1 THEN round(100.0*(cc2.today-cc2.base)/cc2.base) END cost_delta_pct,
    m.emotion, m.category, m.story
  FROM ranked r JOIN vmeta m USING(video_id) LEFT JOIN vch vh USING(video_id)
  LEFT JOIN ccost cc2 ON cc2.channel_id=vh.channel_id LEFT JOIN bmap bm ON bm.channel_id=vh.channel_id
  WHERE (rk_accel<=12 AND r.br>=1500) OR rk_exp<=12 ORDER BY tr DESC LIMIT 18""")

C["brand_spend_rollup"] = rows(f"""
  WITH agg AS (SELECT channel_id, MAX(CASE WHEN d=DATE '{D}' THEN cst END) today, AVG(CASE WHEN d IN ({COSTB}) THEN cst END) base
    FROM cpd WHERE 1=1 {CH} GROUP BY channel_id)
  SELECT COALESCE(b.brand,'(미상)') brand, CAST(round(sum(today)) AS BIGINT) today_total,
    CAST(round(sum(base)) AS BIGINT) baseline_total, any_value(substr(cre.title,1,55)) sample_creative
  FROM agg a LEFT JOIN bmap b USING(channel_id) LEFT JOIN chcre cre USING(channel_id)
  WHERE today IS NOT NULL GROUP BY 1 ORDER BY today_total DESC LIMIT 25""")

C["campaign_flow_daily"] = rows(f"""
  SELECT dt, sum(started) started, sum(ended) ended FROM (
    SELECT s dt,1 started,0 ended FROM oo WHERE s BETWEEN DATE '{D}'-INTERVAL 14 DAY AND DATE '{D}' {CH}
    UNION ALL SELECT e,0,1 FROM oo WHERE e BETWEEN DATE '{D}'-INTERVAL 14 DAY AND DATE '{D}' {CH})
  WHERE dt IS NOT NULL GROUP BY dt ORDER BY dt DESC""")
C["campaign_started_brands_3d"] = rows(f"""
  SELECT COALESCE(b.brand,'(미상)') brand, count(*) n, any_value(substr(cre.title,1,50)) sample_creative
  FROM oo LEFT JOIN bmap b USING(channel_id) LEFT JOIN chcre cre USING(channel_id)
  WHERE s BETWEEN DATE '{D}'-INTERVAL 3 DAY AND DATE '{D}' {CH} GROUP BY 1 ORDER BY n DESC LIMIT 15""")
C["campaign_ended_brands_3d"] = rows(f"""
  SELECT COALESCE(b.brand,'(미상)') brand, count(*) n FROM oo LEFT JOIN bmap b USING(channel_id)
  WHERE e BETWEEN DATE '{D}'-INTERVAL 3 DAY AND DATE '{D}' {CH} GROUP BY 1 ORDER BY n DESC LIMIT 15""")

# 한국향(한글 텍스트) 필터 — country_code='KR'만으론 글로벌 브랜드의 KR 캠페인이 남아서,
# 브랜드/크리에이티브/제목에 한글이 있는 '로컬 광고'만 남긴다.
KR_KOREAN_TEXT = True
if KR_ONLY and KR_KOREAN_TEXT:
    import re
    KO = re.compile('[가-힣]')
    def ko(r, fields): return any(KO.search(str(r.get(f) or '')) for f in fields)
    C["cost_movers"]                = [r for r in C["cost_movers"]                if ko(r, ["brand","creative","ad_story"])]
    C["brand_spend_rollup"]         = [r for r in C["brand_spend_rollup"]         if ko(r, ["brand","sample_creative"])]
    C["view_accel"]                 = [r for r in C["view_accel"]                 if ko(r, ["brand","title","ad_story"])]
    C["top_exposed"]                = [r for r in C["top_exposed"]                if ko(r, ["brand","title"])]
    C["spotlight"]                  = [r for r in C["spotlight"]                  if ko(r, ["brand","title","story"])]
    C["campaign_started_brands_3d"] = [r for r in C["campaign_started_brands_3d"] if ko(r, ["brand","sample_creative"])]
    C["campaign_ended_brands_3d"]   = [r for r in C["campaign_ended_brands_3d"]   if ko(r, ["brand"])]
    # category_rollup(영문 태그)·industry_cpm·campaign_flow_daily 는 그대로 유지

suffix = "_kr" if KR_ONLY else ""
outpath = p(f"llm_input_{D}{suffix}.json")
with open(outpath,"w",encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1, default=str)
print("D =", D, "| KR_ONLY =", KR_ONLY)
for k,v in C.items(): print(f"  {k}: {len(v)} rows")
print("written:", outpath, "(", round(os.path.getsize(outpath)/1024,1), "KB )")
