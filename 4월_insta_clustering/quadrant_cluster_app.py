from flask import Flask, render_template, jsonify, request, send_file, abort
import pandas as pd
import os
import re
import time
import requests

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
THUMB_CACHE_DIR = os.path.join(BASE_DIR, '.thumb_cache')

SHORTCODE_RE = re.compile(r'^[A-Za-z0-9_-]{1,32}$')
OG_IMAGE_RE = re.compile(
    r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
MISS_TTL_SEC = 24 * 3600

THUMB_PAGE_UA = 'facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)'
THUMB_IMG_UA = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
)

# 통합 데이터 파일 (7개 카테고리 전체)
ALL_DATA_FILE = 'real data_all2.csv'

CATEGORIES = [
    '맛집/푸드',
    '뷰티(메이크업/헤어)',
    '엔터/아이돌/연예',
    '운동/피트니스',
    '패션/룩',
    '육아/키즈',
    '카페/핫플',
]

_STAT_COLS = [
    'cluster_id', 'cluster_name', 'analysis_date', 'topic',
    'topic_total_post_count', 'topic_total_dm_count',
    'cluster_post_share', 'cluster_dm_share', 'dm_per_views', 'dm_per_likes',
    'cluster_post_count', 'cluster_dm_send_count', 'cluster_views', 'cluster_likes',
    'cluster_name_reason', 'top1_post_id', 'top2_post_id', 'top3_post_id',
]

_all_df = None   # 전체 CSV를 한 번만 로드
_cat_cache = {}  # category_name -> {'df': DataFrame, 'kw_map': dict}


def _get_all_df():
    global _all_df
    if _all_df is None:
        _all_df = pd.read_csv(os.path.join(BASE_DIR, ALL_DATA_FILE), low_memory=False)
        _all_df['cluster_id'] = _all_df['cluster_id'].astype(str)
    return _all_df


def load_category(cat_name):
    if cat_name in _cat_cache:
        return _cat_cache[cat_name]

    all_df = _get_all_df()
    topic_df = all_df[all_df['topic'] == cat_name]
    if topic_df.empty:
        return None

    # 키워드 중복 제거 후 cluster_id → keywords 매핑
    kw_df = topic_df.drop_duplicates(subset=['cluster_id', 'sub_keyword'])
    kw_map = kw_df.groupby('cluster_id')['sub_keyword'].apply(list).to_dict()

    df = (
        topic_df[_STAT_COLS]
        .drop_duplicates(subset=['cluster_id'])
        .sort_values('analysis_date', ascending=False)
        .drop_duplicates(subset=['cluster_name'], keep='first')
        .reset_index(drop=True)
    )

    _cat_cache[cat_name] = {'df': df, 'kw_map': kw_map}
    return _cat_cache[cat_name]


def build_clusters(cat_name):
    cat = load_category(cat_name)
    if not cat or cat['df'].empty:
        return {'clusters': [], 'total_dm': 0, 'total_posts': 0, 'analysis_date': ''}

    df = cat['df']
    kw_map = cat['kw_map']

    analysis_date = str(df['analysis_date'].iloc[0]) if 'analysis_date' in df.columns else ''
    total_dm = int(df['topic_total_dm_count'].iloc[0]) if 'topic_total_dm_count' in df.columns else int(df['cluster_dm_send_count'].sum())
    total_posts = int(df['topic_total_post_count'].iloc[0]) if 'topic_total_post_count' in df.columns else int(df['cluster_post_count'].sum())

    clusters = []
    for _, row in df.iterrows():
        top_posts = []
        for col in ['top1_post_id', 'top2_post_id', 'top3_post_id']:
            pid = str(row.get(col, '')).strip()
            if pid and pid not in ('nan', ''):
                top_posts.append({'post_id': pid, 'url': f'https://www.instagram.com/p/{pid}/'})

        cid = str(row['cluster_id'])
        clusters.append({
            'cluster_id': cid,
            'label': str(row['cluster_name']),
            'sub_label': str(row.get('cluster_name_reason', '')),
            'keywords': kw_map.get(cid, []),
            'post_count': int(row['cluster_post_count']),
            'total_dm': int(row['cluster_dm_send_count']),
            'total_views': int(row['cluster_views']),
            'total_likes': int(row['cluster_likes']),
            'dm_per_view': float(row['dm_per_views']),
            'dm_per_like': float(row['dm_per_likes']),
            'dm_share': float(row['cluster_dm_share']),
            'post_share': float(row['cluster_post_share']),
            'top_posts': top_posts,
        })

    clusters.sort(key=lambda x: x['post_count'], reverse=True)
    return {
        'clusters': clusters,
        'total_dm': total_dm,
        'total_posts': total_posts,
        'analysis_date': analysis_date,
    }


@app.route('/')
def index():
    return render_template('quadrant.html')


@app.route('/api/topics')
def api_topics():
    return jsonify({'topics': CATEGORIES})


@app.route('/api/cluster')
def api_cluster():
    topic = request.args.get('topic', '')
    if not topic:
        topic = CATEGORIES[0]['name']

    result = build_clusters(topic)
    result['available'] = True
    result['topic'] = topic
    return jsonify(result)


@app.route('/thumb/<post_id>')
def api_thumb(post_id):
    if not SHORTCODE_RE.match(post_id):
        abort(400)
    os.makedirs(THUMB_CACHE_DIR, exist_ok=True)
    jpg_path = os.path.join(THUMB_CACHE_DIR, f'{post_id}.jpg')
    miss_path = os.path.join(THUMB_CACHE_DIR, f'{post_id}.miss')

    if os.path.exists(jpg_path):
        resp = send_file(jpg_path, mimetype='image/jpeg')
        resp.headers['Cache-Control'] = 'public, max-age=86400'
        return resp
    if os.path.exists(miss_path) and time.time() - os.path.getmtime(miss_path) < MISS_TTL_SEC:
        abort(404)

    try:
        page_headers = {
            'User-Agent': THUMB_PAGE_UA,
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml',
        }
        post_url = f'https://www.instagram.com/p/{post_id}/'
        r = requests.get(post_url, headers=page_headers, timeout=8)
        if r.status_code != 200:
            raise RuntimeError(f'post status {r.status_code}')
        m = OG_IMAGE_RE.search(r.text)
        if not m:
            raise RuntimeError('no og:image')
        img_url = m.group(1).replace('&amp;', '&')
        img_r = requests.get(img_url, headers={'User-Agent': THUMB_IMG_UA}, timeout=10)
        if img_r.status_code != 200:
            raise RuntimeError(f'img status {img_r.status_code}')
        with open(jpg_path, 'wb') as f:
            f.write(img_r.content)
        resp = send_file(jpg_path, mimetype='image/jpeg')
        resp.headers['Cache-Control'] = 'public, max-age=86400'
        return resp
    except Exception as e:
        try:
            with open(miss_path, 'w') as f:
                f.write(str(e)[:200])
        except Exception:
            pass
        abort(404)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5078))
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(host='0.0.0.0', port=port, debug=debug)
