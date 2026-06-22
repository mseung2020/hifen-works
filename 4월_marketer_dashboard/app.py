from flask import Flask, render_template, redirect, url_for, abort, request, session
import pandas as pd
import json
import os

app = Flask(__name__)
app.secret_key = os.environ.get('DASHBOARD_SECRET_KEY', 'change-this-secret-key')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

# 어드민 계정 (환경변수로 설정. 미설정 시 기본값)
ADMIN_ID = os.environ.get('DASHBOARD_ADMIN_ID', 'admin')
ADMIN_PW = os.environ.get('DASHBOARD_ADMIN_PW', 'changeme')


# ══════════════════════════════════════
# 브랜드 목록 자동 탐지
# ══════════════════════════════════════
def get_brands():
    """data/ 하위 폴더를 스캔하여 config.json이 있는 브랜드 목록 반환"""
    brands = []
    if not os.path.exists(DATA_DIR):
        return brands
    for name in sorted(os.listdir(DATA_DIR)):
        brand_dir = os.path.join(DATA_DIR, name)
        config_path = os.path.join(brand_dir, 'config.json')
        if os.path.isdir(brand_dir) and os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            brands.append({
                'id': name,
                'name': cfg.get('brand_name', name),
                'name_en': cfg.get('brand_name_en', name),
                'topic': cfg.get('topic', ''),
                'logo': cfg.get('logo', ''),
            })
    return brands


def load_brand_config(brand_id):
    """특정 브랜드의 config.json 로드"""
    config_path = os.path.join(DATA_DIR, brand_id, 'config.json')
    if not os.path.exists(config_path):
        return None
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


# ══════════════════════════════════════
# 헬퍼 함수
# ══════════════════════════════════════
def safe_float(val, default=0.0):
    try:
        v = float(val)
        return v if pd.notna(v) else default
    except (ValueError, TypeError):
        return default


def safe_int(val, default=0):
    try:
        v = float(val)
        return int(v) if pd.notna(v) else default
    except (ValueError, TypeError):
        return default


def format_number(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(int(n))


def format_subs_kr(subs):
    if subs >= 10_000:
        man = subs / 10_000
        if man >= 100:
            return f"{man:.0f}만"
        elif man == int(man):
            return f"{int(man)}만"
        else:
            return f"{man:.1f}만"
    return f"{subs:,}"


# ══════════════════════════════════════
# 브랜드 데이터 로드 & 가공
# ══════════════════════════════════════
def load_data(brand_id):
    """특정 브랜드의 CSV를 로드하고 대시보드용 데이터로 가공"""

    CFG = load_brand_config(brand_id)
    if not CFG:
        return None

    BRAND_NAME = CFG['brand_name']
    BRAND_ID_MAP = {int(k): v for k, v in CFG.get('oly_brand_id_map', {}).items()}
    TOP_COMPETITORS = list(BRAND_ID_MAP.values())
    brand_data_dir = os.path.join(DATA_DIR, brand_id)

    def csv_path(filename):
        return os.path.join(brand_data_dir, filename)

    # ── CSV 로드 ──
    lily = pd.read_csv(csv_path(CFG['base_csv']), on_bad_lines='skip')
    brand = pd.read_csv(csv_path('brand_all_videos.csv'), on_bad_lines='skip')
    yt_info = pd.read_csv(csv_path('youtuber_info.csv'), on_bad_lines='skip')
    yt_stats = pd.read_csv(csv_path('youtuber_stats.csv'), on_bad_lines='skip')
    demo = pd.read_csv(csv_path('demography.csv'), on_bad_lines='skip')
    oly_score_df = pd.read_csv(csv_path('oliveyoung_brand_score.csv'), on_bad_lines='skip')
    oly_rank_df = pd.read_csv(csv_path('oliveyoung_product_rank.csv'), on_bad_lines='skip')
    oly_info_df = pd.read_csv(csv_path('oliveyoung_product_info.csv'))

    lily_channels = set(lily['channel_id'].unique())
    data = {}

    # ── config 정보 전달 ──
    data['brand_name'] = BRAND_NAME
    data['brand_id'] = brand_id
    data['brand_name_en'] = CFG.get('brand_name_en', '')
    data['topic'] = CFG.get('topic', '')
    data['logo'] = f'/data/{brand_id}/{CFG.get("logo", "")}'
    data['cta_link'] = CFG.get('cta_link', '')
    data['competitors_alert_top3'] = CFG.get('competitors_alert_top3', [])

    # ════════════════════════════════════════
    # 1. KPI 기본 지표
    # ════════════════════════════════════════
    data['total_videos'] = int(len(lily))
    data['total_views'] = int(lily['views'].sum())
    data['total_views_fmt'] = format_number(data['total_views'])
    data['total_creators'] = int(lily['channel_id'].nunique())

    ads_count = int((lily['ads_yn'] == 1).sum())
    organic_count = int((lily['ads_yn'] == 0).sum())
    data['ads_count'] = ads_count
    data['organic_count'] = organic_count
    data['ads_pct'] = round(ads_count / max(len(lily), 1) * 100, 1)
    data['organic_pct'] = round(organic_count / max(len(lily), 1) * 100, 1)

    stats_in_lily = yt_stats[yt_stats['channel_id'].isin(lily_channels)]
    avg_eng = stats_in_lily['engagement_rate'].dropna().mean()
    data['avg_engagement'] = round(safe_float(avg_eng), 2)

    # ════════════════════════════════════════
    # 2. 경쟁사 분석
    # ════════════════════════════════════════
    brand_valid = brand[brand['brand1'].notna() & (brand['brand1'] != 'NULL')].copy()

    brand_counts_sr = brand_valid['brand1'].value_counts()
    brand_counts_list = []
    brand_rank = None
    for i, (name, count) in enumerate(brand_counts_sr.items()):
        is_self = (name == BRAND_NAME)
        if i < 20 or is_self:
            brand_counts_list.append({
                'name': str(name), 'count': int(count), 'is_self': is_self
            })
        if is_self:
            brand_rank = i + 1

    data['brand_counts'] = brand_counts_list
    data['brand_rank'] = brand_rank or 0

    overlap_targets = CFG.get('competitors_heatmap', [])
    brand_channel_map = {}
    for b in overlap_targets:
        brand_channel_map[b] = set(brand_valid[brand_valid['brand1'] == b]['channel_id'].unique())

    lily_overlap = {}
    for b in overlap_targets:
        lily_overlap[b] = int(len(lily_channels & brand_channel_map[b]))
    data['lily_overlap'] = lily_overlap

    heatmap_brands = [BRAND_NAME] + overlap_targets
    hm_channel_sets = {BRAND_NAME: lily_channels}
    for b in overlap_targets:
        hm_channel_sets[b] = brand_channel_map[b] & lily_channels

    heatmap = []
    for b1 in heatmap_brands:
        row = []
        for b2 in heatmap_brands:
            if b1 == b2:
                row.append(0)
            else:
                row.append(int(len(hm_channel_sets.get(b1, set()) & hm_channel_sets.get(b2, set()))))
        heatmap.append(row)
    data['heatmap'] = heatmap
    data['heatmap_brands'] = heatmap_brands

    alert_top3 = CFG.get('competitors_alert_top3', [])
    top3_channels = set()
    for b in alert_top3:
        top3_channels |= brand_channel_map.get(b, set())
    data['overlap_top3_count'] = int(len(lily_channels & top3_channels))

    # ════════════════════════════════════════
    # 2-B. 절대적 시장 순위 (brand_logo_beauty 기반)
    # ════════════════════════════════════════
    brand_logo = pd.read_csv(csv_path('brand_logo_beauty.csv'), on_bad_lines='skip')
    brand_logo = brand_logo.dropna(subset=['brand_videos'])
    brand_logo = brand_logo.sort_values('brand_videos', ascending=False).reset_index(drop=True)

    abs_rank_list = []
    abs_my_rank = None
    for i, (_, row) in enumerate(brand_logo.iterrows()):
        name_kr = str(row.get('brand_name_kr', ''))
        vids = safe_int(row.get('brand_videos'))
        is_self = (name_kr == BRAND_NAME)
        if i < 15 or is_self:
            abs_rank_list.append({
                'name': name_kr, 'count': vids, 'is_self': is_self, 'rank': i + 1
            })
        if is_self:
            abs_my_rank = i + 1

    data['abs_rank'] = abs_rank_list
    data['abs_my_rank'] = abs_my_rank or 0
    data['abs_total_brands'] = int(len(brand_logo))

    # ════════════════════════════════════════
    # 3. 크리에이터 분석
    # ════════════════════════════════════════
    lily_per_ch = lily.groupby('channel_id').size().reset_index(name='lily_videos')

    ch_brands = brand_valid.groupby('channel_id')['brand1'].apply(
        lambda x: list(set(x))
    ).reset_index(name='all_brands')

    creator = yt_info.merge(yt_stats, on='channel_id', how='left', suffixes=('', '_st'))
    creator = creator.merge(lily_per_ch, on='channel_id', how='left')
    creator = creator.merge(ch_brands, on='channel_id', how='left')
    creator['lily_videos'] = creator['lily_videos'].fillna(0).astype(int)

    def _competing(brands):
        if not isinstance(brands, list):
            return []
        return [b for b in brands if b in TOP_COMPETITORS][:5]

    creator['competing_names'] = creator['all_brands'].apply(_competing)
    creator['competing_count'] = creator['competing_names'].apply(len)

    creator_sorted = creator.sort_values('subscribers', ascending=False).head(20)

    top_creators = []
    for _, r in creator_sorted.iterrows():
        subs = safe_int(r.get('subscribers'))
        avg_v = safe_float(r.get('average_views'))
        eng = safe_float(r.get('engagement_rate'))
        growth = safe_float(r.get('subs_growth_3_months'))

        tags = []
        for t in ['Main_tag1', 'Main_tag2']:
            val = r.get(t)
            if pd.notna(val) and str(val).strip():
                tags.append(str(val).strip())

        top_creators.append({
            'name': str(r.get('title', '')),
            'channel_id': str(r.get('channel_id', '')),
            'subscribers': subs,
            'subscribers_fmt': format_subs_kr(subs),
            'avg_views': avg_v,
            'avg_views_fmt': format_number(avg_v),
            'engagement_rate': round(eng, 2),
            'thumbnail': str(r.get('thumbnail', '')),
            'tags': tags,
            'competing_names': r.get('competing_names', []) if isinstance(r.get('competing_names'), list) else [],
            'competing_count': safe_int(r.get('competing_count')),
            'lily_videos': safe_int(r.get('lily_videos')),
            'subs_growth': round(growth, 1),
        })
    data['top_creators'] = top_creators

    # ════════════════════════════════════════
    # 4. 시청자 인구통계
    # ════════════════════════════════════════
    f_cols = ['F13_17', 'F18_24', 'F25_34', 'F35_44', 'F45_54', 'F55_64', 'F65']
    m_cols = ['M13_17', 'M18_24', 'M25_34', 'M35_44', 'M45_54', 'M55_64', 'M65']

    f_avg = demo[f_cols].mean()
    m_avg = demo[m_cols].mean()
    total_demo = f_avg.sum() + m_avg.sum()

    data['female_pct'] = round(f_avg.sum() / max(total_demo, 0.01) * 100, 1)
    data['male_pct'] = round(m_avg.sum() / max(total_demo, 0.01) * 100, 1)

    age_labels = ['13-17', '18-24', '25-34', '35-44', '45-54', '55-64', '65+']
    age_dist = []
    for i, label in enumerate(age_labels):
        f_val = round(float(f_avg.iloc[i]), 1)
        m_val = round(float(m_avg.iloc[i]), 1)
        age_dist.append({
            'label': label, 'female': f_val, 'male': m_val,
            'total': round(f_val + m_val, 1)
        })
    data['age_distribution'] = age_dist

    # ════════════════════════════════════════
    # 5. 올리브영 브랜드 스코어
    # ════════════════════════════════════════
    oly_score_df['brand_id'] = oly_score_df['brand'].apply(lambda x: safe_int(x))
    oly_score_df['brand_name'] = oly_score_df['brand_id'].map(BRAND_ID_MAP)
    oly_named = oly_score_df[oly_score_df['brand_name'].notna()].copy()
    oly_named = oly_named.sort_values('date')

    chart_brands = CFG.get('oly_chart_brands', [])
    score_trend = {}
    for bn in chart_brands:
        rows = oly_named[oly_named['brand_name'] == bn]
        scores = []
        for _, row in rows.iterrows():
            scores.append({
                'date': str(row['date']),
                'score': round(safe_float(row['brand_score']), 2)
            })
        score_trend[bn] = scores
    data['oly_score_trend'] = score_trend
    data['oly_chart_brands'] = chart_brands

    my_scores = oly_named[oly_named['brand_name'] == BRAND_NAME]
    data['oly_latest_score'] = round(safe_float(my_scores.iloc[-1]['brand_score']), 1) if len(my_scores) > 0 else 0

    top_comp = chart_brands[1] if len(chart_brands) > 1 else None
    if top_comp:
        comp_scores = oly_named[oly_named['brand_name'] == top_comp]
        data['oly_top_comp_name'] = top_comp
        data['oly_top_comp_score'] = round(safe_float(comp_scores.iloc[-1]['brand_score']), 1) if len(comp_scores) > 0 else 0
    else:
        data['oly_top_comp_name'] = ''
        data['oly_top_comp_score'] = 0

    # ════════════════════════════════════════
    # 6. 올리브영 제품 순위
    # ════════════════════════════════════════
    oly_product_brand = CFG.get('oly_product_brand_name', BRAND_NAME)
    my_products = oly_info_df[oly_info_df['brand'] == oly_product_brand].copy()
    latest_date = oly_rank_df['date'].max()

    # rank 컬럼명 통일 (product_rank → rank)
    if 'product_rank' in oly_rank_df.columns and 'rank' not in oly_rank_df.columns:
        oly_rank_df = oly_rank_df.rename(columns={'product_rank': 'rank'})
    oly_rank_df['rank'] = pd.to_numeric(oly_rank_df['rank'], errors='coerce')

    latest_all = oly_rank_df[
        (oly_rank_df['date'] == latest_date) & (oly_rank_df['category'] == '전체')
    ][['product_id', 'rank', 'score', 'momentum_direction', 'rank_avg_7d']]

    lp = my_products.merge(latest_all, on='product_id', how='inner')
    lp = lp.sort_values('rank')

    dates_sorted = sorted(oly_rank_df['date'].unique())
    if len(dates_sorted) >= 2:
        prev_date = dates_sorted[-2]
        prev_ranks = oly_rank_df[
            (oly_rank_df['date'] == prev_date) & (oly_rank_df['category'] == '전체')
        ][['product_id', 'rank']].rename(columns={'rank': 'prev_rank'})
        lp = lp.merge(prev_ranks, on='product_id', how='left')
        lp['rank_change'] = pd.to_numeric(lp['prev_rank'], errors='coerce') - pd.to_numeric(lp['rank'], errors='coerce')
    else:
        lp['rank_change'] = 0

    oly_products = []
    for _, row in lp.head(10).iterrows():
        oly_products.append({
            'name': str(row.get('product', '')),
            'category': str(row.get('category_x', row.get('category', ''))),
            'rank': safe_int(row.get('rank', 999)),
            'rank_change': safe_int(row.get('rank_change')),
            'image': str(row.get('image', '')),
            'momentum': str(row.get('momentum_direction', ''))
        })
    data['oly_products'] = oly_products
    data['oly_enabled'] = CFG.get('oly_enabled', True)

    # ════════════════════════════════════════
    # 7. 월별 트렌드
    # ════════════════════════════════════════
    lily_c = lily.copy()
    lily_c['parsed_date'] = pd.to_datetime(
        lily_c['publishDate'].astype(str).str.strip(),
        format='%Y. %m. %d', errors='coerce'
    )
    mask = lily_c['parsed_date'].isna()
    if mask.any():
        lily_c.loc[mask, 'parsed_date'] = pd.to_datetime(
            lily_c.loc[mask, 'publishDate'].astype(str).str.strip(),
            format='%Y-%m-%d', errors='coerce'
        )
    lily_c = lily_c.dropna(subset=['parsed_date'])
    lily_c['month'] = lily_c['parsed_date'].dt.to_period('M').astype(str)

    monthly = lily_c.groupby('month').agg(
        count=('video_id', 'count'),
        views=('views', 'sum')
    ).reset_index().sort_values('month')

    data['monthly_trend'] = [
        {'month': str(r['month']), 'count': int(r['count']), 'views': int(r['views'])}
        for _, r in monthly.iterrows()
    ]

    # ════════════════════════════════════════
    # 8. 상위 영상 목록
    # ════════════════════════════════════════
    top_vids = lily.nlargest(10, 'views')
    top_videos = []
    for _, r in top_vids.iterrows():
        top_videos.append({
            'title': str(r.get('video_title', '')),
            'channel': str(r.get('channel_title', '')),
            'views': safe_int(r.get('views')),
            'views_fmt': format_number(safe_int(r.get('views'))),
            'likes': safe_int(r.get('likes')),
            'comments': safe_int(r.get('comments')),
            'ads': safe_int(r.get('ads_yn')),
            'date': str(r.get('publishDate', '')),
        })
    data['top_videos'] = top_videos

    return data


# ══════════════════════════════════════
# 라우트
# ══════════════════════════════════════

@app.route('/')
def home():
    """첫 번째 브랜드 페이지로 이동"""
    brands = get_brands()
    if brands:
        return redirect(url_for('brand_page', brand_id=brands[0]['id']))
    return redirect(url_for('admin_login'))


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """어드민 로그인"""
    error = None
    if request.method == 'POST':
        uid = request.form.get('uid', '')
        pw = request.form.get('pw', '')
        if uid == ADMIN_ID and pw == ADMIN_PW:
            session['admin'] = True
            return redirect(url_for('admin'))
        else:
            error = '아이디 또는 비밀번호가 올바르지 않습니다.'
    return render_template('login.html', error=error)


@app.route('/admin')
def admin():
    """어드민 페이지 — 브랜드 선택 (로그인 필요)"""
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    brands = get_brands()
    return render_template('admin.html', brands=brands)


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))


@app.route('/brand/<brand_id>')
def brand_page(brand_id):
    """브랜드별 대시보드"""
    data = load_data(brand_id)
    if data is None:
        abort(404)
    return render_template('index.html', data=data, brand_id=brand_id)


@app.route('/data/<brand_id>/<path:filename>')
def brand_static(brand_id, filename):
    """브랜드별 정적 파일 (로고 등) 서빙"""
    brand_dir = os.path.join(DATA_DIR, brand_id)
    from flask import send_from_directory
    return send_from_directory(brand_dir, filename)


if __name__ == '__main__':
    app.run(debug=True, port=5001)
