/* global d3 */
/* Ugwanggi internal architecture atlas — single-page renderer
   Reads window.SITE_DATA (injected by build_html.py). */

(function () {
  const DATA = window.SITE_DATA;
  if (!DATA) {
    document.body.innerHTML = '<p style="padding:40px;color:#b91c1c">site_data.json 이 주입되지 않았습니다.</p>';
    return;
  }
  const TABLES = DATA.tables;
  const APPS = DATA.apps;
  const ENDPOINTS = DATA.endpoints;
  const META = DATA.meta;

  // ---------- Utility ----------
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const el = (tag, attrs = {}, ...children) => {
    const node = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k === 'class') node.className = v;
      else if (k === 'html') node.innerHTML = v;
      else if (k.startsWith('on')) node.addEventListener(k.slice(2).toLowerCase(), v);
      else if (v !== undefined && v !== null) node.setAttribute(k, v);
    }
    for (const c of children) {
      if (c == null || c === false) continue;
      if (Array.isArray(c)) c.forEach(x => x != null && node.appendChild(x.nodeType ? x : document.createTextNode(String(x))));
      else node.appendChild(c.nodeType ? c : document.createTextNode(String(c)));
    }
    return node;
  };
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const pct = (n, d) => d ? Math.round((n / d) * 100) : 0;

  // ---------- Router ----------
  const ROUTES = ['home', 'services', 'tables', 'relations', 'endpoints', 'quality', 'about'];
  function navigate() {
    const raw = (location.hash || '#/home').slice(2);
    const [path, queryStr] = raw.split('?');
    const [view, ...rest] = path.split('/');
    const query = Object.fromEntries(new URLSearchParams(queryStr || ''));
    const active = ROUTES.includes(view) ? view : 'home';

    $$('#top-nav a').forEach(a => a.classList.toggle('active', a.dataset.view === active));
    $$('.view').forEach(v => v.classList.toggle('active', v.id === 'view-' + active));
    const renderer = VIEWS[active];
    if (renderer) renderer(rest, query);
  }
  window.addEventListener('hashchange', navigate);
  window.addEventListener('DOMContentLoaded', navigate);

  // ---------- Shared components ----------
  function tableChip(name, extraClass = '') {
    const a = el('a', { class: 'chip table-chip ' + extraClass, href: '#/tables/' + encodeURIComponent(name) });
    a.textContent = name;
    return a;
  }
  function appChip(name, extraClass = '') {
    const a = el('a', { class: 'chip app-chip ' + extraClass, href: '#/services?focus=' + encodeURIComponent(name) });
    a.textContent = name;
    return a;
  }
  function confBadge(level) {
    const cls = level === 'HIGH' ? 'badge-high' : level === 'MED' ? 'badge-med' : 'badge-low';
    return el('span', { class: 'badge ' + cls }, level || 'LOW');
  }
  function nextStep(text) {
    return el('div', { class: 'next-step' },
      el('span', { class: 'next-step-label' }, '다음 조치'),
      el('span', {}, text));
  }
  function evidenceLine(paths) {
    return el('div', { class: 'evidence-line' },
      el('span', { class: 'evidence-label' }, '근거'),
      el('span', { class: 'mono small' }, Array.isArray(paths) ? paths.join(' · ') : paths));
  }
  function healthDot(h) {
    const c = h === 'healthy' ? 'green' : h === 'over_developed' ? 'amber' : h === 'abandoned_or_experimental' ? 'red' : 'gray';
    return el('span', { class: 'dot ' + c });
  }
  // ============================================================
  //  Home view
  // ============================================================
  function renderHome() {
    const root = $('#view-home');
    root.innerHTML = '';

    // ── Dark hero card (Linear-style featured block) ───────────────────────
    const hero = el('div', { class: 'home-hero' });
    const heroInner = el('div', { class: 'home-hero-inner' },
      el('div', { class: 'home-hero-tagline' },
        el('span', { class: 'pulse' }),
        `Snapshot · ${META.generated_at} · closed-world`),
      el('h1', {}, '유광기의 모든 구조를\n한 장에서 색인합니다'),
      el('p', {},
        `${META.total_schema_tables}개 테이블, ${META.total_endpoints}개 엔드포인트, ${META.app_count}개 서비스를 정적 분석한 구조 참조서. 재탐색 없이 답하고, 내부 AI 학습 사료로 바로 활용 가능합니다.`),
      el('div', { class: 'hero-ctas' },
        el('a', { class: 'btn btn-primary', href: '#/services' }, '서비스 지도 열기 →'),
        el('a', { class: 'btn btn-ghost', href: '#/about' }, '전제와 한계'))
    );
    // Replace \n in h1 with <br>
    heroInner.querySelector('h1').innerHTML = heroInner.querySelector('h1').textContent.replace('\n', '<br>');
    hero.appendChild(heroInner);
    root.appendChild(hero);

    // KPI grid (Supabase-style cards)
    const used = META.used_tables, unused = META.unused_tables;
    const called = META.called_endpoints, uncalled = META.uncalled_endpoints;
    const healthDist = Object.values(APPS).reduce((acc, a) => {
      acc[a.health] = (acc[a.health] || 0) + 1; return acc;
    }, {});
    const grid = el('div', { class: 'kpi-grid' });

    const makeKpiCard = (title, num, bar, foot) => {
      const card = el('div', { class: 'kpi-card' },
        el('div', { class: 'kpi-title' }, title),
        el('div', { class: 'kpi-num' }, String(num)));
      if (bar) {
        const barEl = el('div', { class: 'kpi-bar' });
        bar.forEach(seg => {
          const s = el('span', { class: 'seg-' + seg.cls });
          s.style.width = seg.pct + '%';
          barEl.appendChild(s);
        });
        card.appendChild(barEl);
      }
      if (foot) card.appendChild(el('div', { class: 'kpi-foot' }, ...foot));
      return card;
    };

    grid.appendChild(makeKpiCard(
      '테이블',
      META.total_schema_tables,
      [
        { cls: 'green', pct: (used / META.total_schema_tables) * 100 },
        { cls: 'red',   pct: (unused / META.total_schema_tables) * 100 },
      ],
      [
        el('span', { class: 'ok' },  `↑ ${used} used`),
        el('span', { class: 'bad' }, `↓ ${unused} unused`),
      ]));

    grid.appendChild(makeKpiCard(
      'API 엔드포인트',
      META.total_endpoints,
      [
        { cls: 'green', pct: (called / META.total_endpoints) * 100 },
        { cls: 'red',   pct: (uncalled / META.total_endpoints) * 100 },
      ],
      [
        el('span', { class: 'ok' },  `↑ ${called} called`),
        el('span', { class: 'bad' }, `↓ ${uncalled} silent`),
      ]));

    const h_healthy = (healthDist.healthy || 0);
    const h_over = (healthDist.over_developed || 0);
    const h_aband = (healthDist.abandoned_or_experimental || 0);
    const h_none = (healthDist.no_api || 0);
    grid.appendChild(makeKpiCard(
      '서비스',
      META.app_count,
      [
        { cls: 'green', pct: (h_healthy / META.app_count) * 100 },
        { cls: 'amber', pct: (h_over / META.app_count) * 100 },
        { cls: 'red',   pct: (h_aband / META.app_count) * 100 },
        { cls: 'gray',  pct: (h_none / META.app_count) * 100 },
      ],
      [
        el('span', { class: 'ok' }, `● ${h_healthy} healthy`),
        el('span', {}, `● ${h_over} watch`),
        el('span', { class: 'bad' }, `● ${h_aband} abandoned`),
      ]));

    const biggestCluster = DATA.clusters.normalization_components[0];
    grid.appendChild(makeKpiCard(
      '최대 클러스터',
      biggestCluster.size,
      [{ cls: 'green', pct: (biggestCluster.size / used) * 100 }],
      [el('span', {}, 'hub · ' + biggestCluster.hub_table)]));

    root.appendChild(grid);

    // ── Dashboard 2-column: 앱 미사용률 랭킹 + 이슈 요약 ─────────────
    const dash = el('div', { class: 'grid grid-7030', style: 'margin-top: 24px;' });

    // Left: 앱 미사용률 랭킹
    const rankCard = el('div', { class: 'card', style: 'padding: 0;' });
    rankCard.appendChild(el('div', { class: 'card-header' },
      el('h3', {}, '앱 미사용률 순위'),
      el('a', { class: 'link', href: '#/endpoints' }, '전체 보기 →')));
    const rankBody = el('div', { class: 'card-body' });
    const ranked = Object.values(APPS)
      .filter(a => a.endpoints_total >= 10)
      .sort((a, b) => b.uncalled_pct - a.uncalled_pct)
      .slice(0, 7);
    ranked.forEach(a => {
      const sev = a.uncalled_pct >= 50 ? 'err' : a.uncalled_pct >= 20 ? 'warn' : 'ok';
      const row = el('a', { class: 'list-row', href: '#/endpoints' },
        el('span', { class: 'ico ' + sev }),
        el('span', { class: 'name' }, a.name),
        el('span', { class: 'meta' }, `${a.uncalled_pct}% · ${a.endpoints_uncalled}/${a.endpoints_total}`),
        el('span', { class: 'arr' }, '→'));
      rankBody.appendChild(row);
    });
    rankCard.appendChild(rankBody);
    dash.appendChild(rankCard);

    // Right: 이슈 요약
    const issueCard = el('div', { class: 'card', style: 'padding: 0;' });
    issueCard.appendChild(el('div', { class: 'card-header' },
      el('h3', {}, '발견된 이슈'),
      el('a', { class: 'link', href: '#/quality' }, '품질 뷰 →')));
    const issueBody = el('div', { class: 'card-body', style: 'padding: 14px 16px' });
    const zombie = DATA.diagnostics.zombie_models.length;
    if (zombie > 0) {
      issueBody.appendChild(el('div', { class: 'alert' },
        el('div', {},
          el('div', { class: 'alert-title' }, `유령 모델 ${zombie}건`),
          el('div', { class: 'alert-desc' }, 'Django 코드엔 있지만 DB엔 없는 테이블. 호출 시 runtime error.'),
          el('a', { class: 'alert-action', href: '#/quality' }, '품질 뷰에서 보기 →'))));
    }
    const issueCounts = [
      ['NO_MODEL 테이블', DATA.diagnostics.no_model_tables.length, 'badge-med'],
      ['비정규화 핫스팟 (SEVERE)', DATA.clusters.denormalization_hotspots.filter(h => h.hotspot_level === 'SEVERE').length, 'badge-red'],
      ['도메인 갭 (HIGH+)', DATA.clusters.domain_gaps.filter(g => g.gap_severity === 'SEVERE' || g.gap_severity === 'HIGH').length, 'badge-med'],
      ['MULTI_OWNER', DATA.diagnostics.multi_owner_tables.length, 'badge-gray'],
      ['자기참조', DATA.diagnostics.self_loops.length, 'badge-gray'],
    ];
    issueCounts.forEach(([label, n, badgeCls]) => {
      issueBody.appendChild(el('div', { class: 'count-row' },
        el('span', {}, label),
        el('span', { class: 'badge ' + badgeCls }, String(n))));
    });
    issueCard.appendChild(issueBody);
    dash.appendChild(issueCard);

    root.appendChild(dash);

    // Health distribution section
    root.appendChild(el('h2', {}, '서비스 건강 분포'));
    const healthRow = el('div', { class: 'home-health-row' });
    const buckets = [
      { name: '건강', key: 'healthy', dot: 'green', why: '프론트가 거의 모든 엔드포인트를 사용합니다.' },
      { name: '주의', key: 'over_developed', dot: 'amber', why: '엔드포인트의 20–50%가 호출되지 않습니다.' },
      { name: '방치', key: 'abandoned_or_experimental', dot: 'red', why: '엔드포인트의 50% 이상이 호출되지 않습니다.' },
    ];
    buckets.forEach(b => {
      const col = el('div', { class: 'home-health-col' });
      col.appendChild(el('h4', {},
        el('span', { class: 'dot ' + b.dot }),
        b.name + ' · ' + (healthDist[b.key] || 0) + '개 앱'
      ));
      col.appendChild(el('div', { class: 'desc' }, b.why));
      const names = Object.values(APPS).filter(a => a.health === b.key).map(a => a.name).sort();
      names.forEach(n => col.appendChild(appChip(n)));
      healthRow.appendChild(col);
    });
    root.appendChild(healthRow);

    // Headline insights
    root.appendChild(el('h2', {}, '핵심 소견'));
    const cluster1 = DATA.clusters.normalization_components[0];
    const topUncalledApp = [...Object.values(APPS)].sort((a, b) => b.endpoints_uncalled - a.endpoints_uncalled)[0];
    const zombieCount = DATA.diagnostics.zombie_models.length;

    const ins = el('div', { class: 'grid grid-3 home-insights' });
    const insCard1 = el('div', { class: 'card' },
      el('h3', {}, `${cluster1.size}개 테이블이 하나의 거대한 관계망을 이룹니다`),
      el('p', {}, `중심 테이블은 '${cluster1.hub_table}'. 전체 사용 테이블의 ${pct(cluster1.size, used)}% 가 이 네트워크에 속해 있습니다.`)
    );
    insCard1.appendChild(evidenceLine('core_materials/normalization_clusters.csv · intermediate/analyze_normalization.py'));
    ins.appendChild(insCard1);

    const insCard2 = el('div', { class: 'card' },
      el('h3', {}, `전체 API의 ${pct(uncalled, META.total_endpoints)}% 가 프론트에서 호출되지 않습니다`),
      el('p', {}, `특히 '${topUncalledApp.name}' 는 ${topUncalledApp.endpoints_total}개 중 ${topUncalledApp.endpoints_uncalled}개가 미사용입니다.`)
    );
    insCard2.appendChild(evidenceLine('core_materials/endpoint_usage.csv · intermediate/detect_unused_endpoints.py'));
    ins.appendChild(insCard2);

    const insCard3 = el('div', { class: 'card' },
      el('h3', {}, `유령 모델 ${zombieCount}건 발견`),
      el('p', {}, `코드에 Django 모델은 선언돼 있지만 실제 데이터베이스에는 해당 테이블이 없습니다. 호출 시 런타임 오류를 일으킵니다.`)
    );
    insCard3.appendChild(evidenceLine('core_materials/site_data.json → diagnostics.zombie_models · intermediate/extract_relations.py'));
    ins.appendChild(insCard3);
    root.appendChild(ins);

    // Glossary (collapsible)
    const gl = el('details', { class: 'glossary' });
    gl.appendChild(el('summary', {}, '용어 풀이 — 이 문서에서 쓰이는 말들'));
    const glBody = el('div', { class: 'glossary-body' });
    const terms = [
      ['허브 테이블', '다른 테이블들이 FK로 많이 참조하는 중심 테이블. 관계 그래프에 상위 12개를 라벨 표시.'],
      ['소유 테이블', '이 앱의 Django 모델이 선언한 테이블. db_table="..." 기준.'],
      ['소비 테이블', '이 앱이 FK · raw SQL · import로 읽거나 쓰는 타 앱의 테이블.'],
      ['유령 모델', 'Django 코드엔 모델 클래스가 있지만 실제 DB에는 해당 테이블이 없는 경우. 호출 시 런타임 오류.'],
      ['건강 · 주의 · 방치', '앱의 API 미사용률 기준 — 0~20% 건강, 20~50% 주의, 50% 이상 방치.'],
      ['HIGH · MED · LOW', '관계/판정의 신뢰도 — HIGH는 개발자가 명시한 것, MED는 코드 관찰, LOW는 참고.'],
      ['폐쇄 세계', '이 백엔드 · 프론트 · 스키마 셋 외에 다른 소비자가 없다고 보는 가정.'],
    ];
    terms.forEach(([t, d]) => glBody.appendChild(el('div', { class: 'glossary-row' },
      el('span', { class: 'glossary-term' }, t),
      el('span', { class: 'glossary-def' }, d))));
    gl.appendChild(glBody);
    root.appendChild(gl);
  }

  // ============================================================
  //  Services view
  // ============================================================
  function renderServices(args, query) {
    const root = $('#view-services');
    root.innerHTML = '';
    root.appendChild(el('h1', {}, '서비스 지도'));
    root.appendChild(el('p', { class: 'muted' },
      '노드 크기는 소유 테이블 수, 색은 서비스 건강도. 연결선은 코드 수준 의존(import) · 데이터 공유(table) · 배치(cron)를 구분해 보여줍니다.'));

    // Controls
    const ctrl = el('div', { class: 'graph-controls' });
    ctrl.appendChild(el('label', {}, '소스:'));
    const srcFilters = { imports: true, shared: true, cron: true };
    const srcLabels = [['imports', 'import', 'blue'], ['shared', '공유 테이블', 'amber'], ['cron', '크론', 'purple']];
    srcLabels.forEach(([k, lbl, dot]) => {
      const wrap = el('label', { class: 'control-group', style: 'cursor:pointer' });
      const cb = el('input', { type: 'checkbox', checked: 'checked' });
      cb.addEventListener('change', () => { srcFilters[k] = cb.checked; draw(); });
      wrap.append(cb, el('span', { class: 'dot ' + dot }), lbl);
      ctrl.appendChild(wrap);
    });
    ctrl.appendChild(el('span', { class: 'spacer' }));
    const search = el('input', { type: 'text', placeholder: '앱 이름 검색...' });
    search.addEventListener('input', () => focusApp(search.value.trim()));
    ctrl.appendChild(search);
    root.appendChild(ctrl);

    // Frame
    const frame = el('div', { class: 'graph-frame' });
    const canvas = el('div', { class: 'graph-canvas', id: 'svc-canvas' });
    const aside = el('div', { class: 'graph-aside', id: 'svc-aside' });
    frame.append(canvas, aside);
    root.appendChild(frame);

    // Build nodes/links
    const nodes = Object.values(APPS).map(a => ({
      id: a.name,
      owned: a.owned_count,
      health: a.health,
      endpoints_total: a.endpoints_total,
      endpoints_uncalled: a.endpoints_uncalled,
      uncalled_pct: a.uncalled_pct,
    }));
    const nodeById = Object.fromEntries(nodes.map(n => [n.id, n]));
    const linksAll = DATA.edges.service_edges.map(e => ({
      source: e.from_app, target: e.to_app,
      weight: e.weight, sources: e.sources,
      imports_count: e.imports_count, shared_tables_count: e.shared_tables_count, cron_count: e.cron_count,
    })).filter(l => nodeById[l.source] && nodeById[l.target]);

    // Legend
    aside.innerHTML = '';
    aside.appendChild(el('h3', {}, '색 안내'));
    [['green','건강: 프론트가 대부분 호출'], ['amber','주의: 20–50% 미사용'], ['red','방치: 50%+ 미사용'], ['gray','무관: API 없음']]
      .forEach(([c, txt]) => aside.appendChild(el('div', { class: 'legend-row' },
        el('span', { class: 'legend-swatch', style: `background: var(--${c === 'green' ? 'green' : c === 'amber' ? 'amber' : c === 'red' ? 'red' : 'gray-400'})` }),
        txt)));
    aside.appendChild(el('h3', {}, '선 안내'));
    [['imports', '파랑 — 코드 import'],['shared','주황 — 테이블 공유'],['cron','보라 — 크론 참조']]
      .forEach(([k, txt]) => aside.appendChild(el('div', { class: 'legend-row' },
        el('span', { class: 'legend-line', style: `border-top-color: var(--${k === 'imports' ? 'blue' : k === 'shared' ? 'amber' : 'purple'});` }),
        txt)));
    aside.appendChild(el('h3', {}, '사용 팁'));
    aside.appendChild(el('p', { class: 'small muted' }, '노드 클릭 시 상세를 이 패널에 표시합니다. 마우스 드래그로 노드 재배치, 휠로 확대·축소, 배경 드래그로 이동할 수 있습니다.'));
    const detailHost = el('div', { id: 'svc-detail' });
    aside.appendChild(detailHost);

    // d3 force
    const W = canvas.clientWidth || 900, H = 640;
    const svg = d3.select(canvas).append('svg').attr('viewBox', [0, 0, W, H]);
    const zoomG = svg.append('g');
    svg.call(d3.zoom().scaleExtent([0.4, 3]).on('zoom', ev => zoomG.attr('transform', ev.transform)));
    const linkLayer = zoomG.append('g').attr('class', 'links');
    const nodeLayer = zoomG.append('g').attr('class', 'nodes');

    function nodeColor(n) {
      return n.health === 'healthy' ? 'var(--green)'
           : n.health === 'over_developed' ? 'var(--amber)'
           : n.health === 'abandoned_or_experimental' ? 'var(--red)'
           : 'var(--gray-400)';
    }
    function sizeFor(n) { return 8 + Math.sqrt(n.owned) * 4; }
    function linkClass(l) {
      const srcs = l.sources;
      if (srcs.includes('SHARED_TABLE')) return 'src-shared';
      if (srcs.includes('CRON')) return 'src-cron';
      return 'src-imports';
    }

    let links = linksAll;
    let sim;
    function filterLinks() {
      return linksAll.filter(l => (
        (srcFilters.imports && l.sources.includes('IMPORTS')) ||
        (srcFilters.shared && l.sources.includes('SHARED_TABLE')) ||
        (srcFilters.cron && l.sources.includes('CRON'))
      ));
    }
    function draw() {
      links = filterLinks();
      if (sim) sim.stop();
      sim = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(links).id(d => d.id).distance(160).strength(0.25))
        .force('charge', d3.forceManyBody().strength(-650).distanceMax(450))
        .force('x', d3.forceX(W / 2).strength(0.04))
        .force('y', d3.forceY(H / 2).strength(0.04))
        .force('collide', d3.forceCollide().radius(d => sizeFor(d) + 14))
        .on('tick', ticked);

      linkLayer.selectAll('*').remove();
      const lsel = linkLayer.selectAll('line').data(links).join('line')
        .attr('class', l => 'link ' + linkClass(l))
        .attr('stroke-width', l => 1 + Math.sqrt(l.weight) * 0.6);

      nodeLayer.selectAll('*').remove();
      const gsel = nodeLayer.selectAll('g').data(nodes).join('g').attr('class', 'node')
        .call(drag(sim));
      gsel.append('circle')
        .attr('r', d => sizeFor(d))
        .attr('fill', d => nodeColor(d))
        .on('click', (ev, d) => showApp(d.id));
      gsel.append('title').text(d => `${d.id} — owned ${d.owned}, endpoints ${d.endpoints_total} (${d.uncalled_pct}% 미사용)`);
      gsel.append('text').attr('dy', d => sizeFor(d) + 12).text(d => d.id);

      function ticked() {
        lsel.attr('x1', l => l.source.x).attr('y1', l => l.source.y)
            .attr('x2', l => l.target.x).attr('y2', l => l.target.y);
        gsel.attr('transform', d => `translate(${d.x},${d.y})`);
      }
    }

    function drag(sim) {
      return d3.drag()
        .on('start', (ev, d) => { if (!ev.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
        .on('drag', (ev, d) => { d.fx = ev.x; d.fy = ev.y; })
        .on('end', (ev, d) => { if (!ev.active) sim.alphaTarget(0); d.fx = null; d.fy = null; });
    }

    function showApp(name) {
      const a = APPS[name]; if (!a) return;
      detailHost.innerHTML = '';
      detailHost.appendChild(el('h3', {}, name));
      const meta = el('div', { class: 'small muted' });
      meta.appendChild(healthDot(a.health));
      meta.appendChild(document.createTextNode(
        ` ${a.health === 'healthy' ? '건강' : a.health === 'over_developed' ? '주의' : a.health === 'abandoned_or_experimental' ? '방치' : '무관'}`));
      detailHost.appendChild(meta);
      detailHost.appendChild(el('p', { class: 'small' },
        `소유 테이블 ${a.owned_count} · 소비 테이블 ${a.consumed_count}`, el('br'),
        `엔드포인트 ${a.endpoints_total} (호출 ${a.endpoints_called} / 미호출 ${a.endpoints_uncalled})`,
        el('br'),
        `들어오는 의존 ${a.inbound_count} · 나가는 의존 ${a.outbound_count}`
      ));
      if (a.outbound_deps.length) {
        detailHost.appendChild(el('h3', {}, '이 앱이 기대는 곳'));
        const ul = el('ul', { style: 'padding-left:18px;margin:0;font-size:13px' });
        a.outbound_deps.sort((x, y) => y.weight - x.weight).forEach(d => ul.appendChild(
          el('li', {}, el('strong', {}, d.to_app), ` (${d.sources.join('·')}, w=${d.weight})`)));
        detailHost.appendChild(ul);
      }
      if (a.inbound_deps.length) {
        detailHost.appendChild(el('h3', {}, '이 앱에 기대는 곳'));
        const ul = el('ul', { style: 'padding-left:18px;margin:0;font-size:13px' });
        a.inbound_deps.sort((x, y) => y.weight - x.weight).forEach(d => ul.appendChild(
          el('li', {}, el('strong', {}, d.from_app), ` (${d.sources.join('·')}, w=${d.weight})`)));
        detailHost.appendChild(ul);
      }
    }
    function focusApp(q) {
      const lower = (q || '').toLowerCase();
      nodeLayer.selectAll('g.node').classed('highlight', d => lower && d.id.toLowerCase().includes(lower));
    }

    draw();
    if (query.focus && APPS[query.focus]) {
      showApp(query.focus);
      focusApp(query.focus);
    }
  }

  // ============================================================
  //  Tables view
  // ============================================================
  function renderTables(args, query) {
    const root = $('#view-tables');
    // Detail route (#/tables/<name>)
    if (args.length && args[0]) {
      const name = decodeURIComponent(args[0]);
      if (TABLES[name]) { openTableModal(name); }
    }

    if (root.dataset.built) return;  // build once then keep state

    root.innerHTML = '';
    root.appendChild(el('h1', {}, '테이블 탐색기'));
    root.appendChild(el('p', { class: 'muted' },
      `사용 여부, 도메인, 소유 앱, 서브카테고리 기준으로 ${META.total_schema_tables}개 테이블을 좁혀 살펴봅니다. 카드 클릭 시 상세가 열립니다.`));

    // Build filters
    const domains = {};
    const subs = {};
    Object.values(TABLES).forEach(t => {
      domains[t.domain_prefix] = (domains[t.domain_prefix] || 0) + 1;
      subs[t.subcategory] = (subs[t.subcategory] || 0) + 1;
    });
    const topDomains = Object.entries(domains).sort((a, b) => b[1] - a[1]).slice(0, 14);

    const state = {
      used: 'all',          // 'USED' | 'UNUSED' | 'all'
      domains: new Set(),   // empty = all
      subs: new Set(),
      isolated: false,
      q: '',
    };

    const layout = el('div', { class: 'tables-layout' });
    const filter = el('div', { class: 'filter-panel' });

    // Search
    filter.appendChild(el('h3', {}, '검색'));
    const input = el('input', { type: 'text', placeholder: '테이블명 일부...' });
    input.addEventListener('input', () => { state.q = input.value.toLowerCase(); renderGrid(); });
    filter.appendChild(input);

    // Used/Unused
    filter.appendChild(el('h3', {}, '사용 여부'));
    [['all', '전체'], ['USED', '사용중'], ['UNUSED', '미사용']].forEach(([v, lbl]) => {
      const r = el('input', { type: 'radio', name: 'f-used', value: v });
      if (v === 'all') r.checked = true;
      r.addEventListener('change', () => { state.used = v; renderGrid(); });
      filter.appendChild(el('label', {}, r, lbl));
    });

    // Domain
    filter.appendChild(el('h3', {}, '도메인'));
    topDomains.forEach(([d, n]) => {
      const cb = el('input', { type: 'checkbox', value: d });
      cb.addEventListener('change', () => {
        if (cb.checked) state.domains.add(d); else state.domains.delete(d);
        renderGrid();
      });
      filter.appendChild(el('label', {}, cb, `${d} `, el('span', { class: 'muted small' }, `(${n})`)));
    });

    // Subcategory
    filter.appendChild(el('h3', {}, '분류'));
    Object.keys(subs).sort().forEach(s => {
      const cb = el('input', { type: 'checkbox', value: s });
      cb.addEventListener('change', () => {
        if (cb.checked) state.subs.add(s); else state.subs.delete(s);
        renderGrid();
      });
      filter.appendChild(el('label', {}, cb, `${s} `, el('span', { class: 'muted small' }, `(${subs[s]})`)));
    });

    // Isolated
    filter.appendChild(el('h3', {}, '관계'));
    const isoCb = el('input', { type: 'checkbox' });
    isoCb.addEventListener('change', () => { state.isolated = isoCb.checked; renderGrid(); });
    filter.appendChild(el('label', {}, isoCb, '고립 테이블만'));

    // Results area
    const results = el('div');
    const meta = el('div', { class: 'tables-results-meta' });
    const grid = el('div', { class: 'tables-grid' });
    results.append(meta, grid);

    layout.append(filter, results);
    root.appendChild(layout);

    function renderGrid() {
      const q = state.q;
      const filtered = Object.values(TABLES).filter(t => {
        if (state.used !== 'all' && t.usage !== state.used) return false;
        if (state.domains.size && !state.domains.has(t.domain_prefix)) return false;
        if (state.subs.size && !state.subs.has(t.subcategory)) return false;
        if (state.isolated && !t.is_isolated) return false;
        if (q && !t.name.toLowerCase().includes(q)) return false;
        return true;
      }).sort((a, b) => a.name.localeCompare(b.name));

      meta.textContent = `${filtered.length}개 테이블`;
      grid.innerHTML = '';
      if (filtered.length === 0) {
        grid.appendChild(el('div', { class: 'empty-state', style: 'grid-column:1/-1' },
          el('h3', {}, '조건에 맞는 테이블이 없습니다'),
          el('p', {}, '필터를 조금 완화해보세요.'),
          el('button', { class: 'ghost-btn', onclick: () => {
            state.used = 'all'; state.domains.clear(); state.subs.clear();
            state.isolated = false; state.q = '';
            input.value = '';
            $$('input[name=f-used]', filter).forEach(r => r.checked = r.value === 'all');
            $$('input[type=checkbox]', filter).forEach(cb => cb.checked = false);
            renderGrid();
          }}, '필터 초기화')
        ));
        return;
      }
      const cap = filtered.slice(0, 500);
      cap.forEach(t => grid.appendChild(tableCard(t)));
      if (filtered.length > cap.length) {
        grid.appendChild(el('div', { class: 'muted small', style: 'grid-column:1/-1;padding:10px' },
          `(첫 ${cap.length}개만 표시. 필터를 더 좁혀주세요.)`));
      }
    }

    renderGrid();
    root.dataset.built = '1';
  }

  function tableCard(t) {
    const card = el('div', { class: 'table-card', onclick: () => { location.hash = '#/tables/' + encodeURIComponent(t.name); } });
    const row = el('div', { class: 'row' });
    row.appendChild(el('span', { class: 'dot ' + (t.usage === 'USED' ? 'green' : 'red') }));
    row.appendChild(el('span', { class: 'name' }, t.name));
    card.appendChild(row);

    const meta = el('div', { class: 'meta' });
    if (t.owner_app) meta.appendChild(el('span', {}, t.owner_app.split('|').join(' · ')));
    else meta.appendChild(el('span', { class: 'muted' }, '모델 없음'));
    if (t.subcategory && t.subcategory !== 'DIRECT') meta.appendChild(el('span', {}, '· ' + t.subcategory));
    card.appendChild(meta);

    card.appendChild(el('div', { class: 'stats' },
      el('span', {}, el('b', {}, String(t.columns.length)), ' 컬럼'),
      el('span', {}, el('b', {}, String(t.incoming_fks.length)), ' 피참조'),
      el('span', {}, el('b', {}, String(t.outgoing_fks.length)), ' 참조'),
      t.is_isolated ? el('span', { class: 'muted' }, '· 고립') : null,
    ));
    return card;
  }

  // Table detail modal
  function openTableModal(name) {
    const t = TABLES[name]; if (!t) return;
    const backdrop = $('#modal');
    const body = $('#modal-body');
    const header = $('#modal-header-content');
    header.innerHTML = '';
    header.appendChild(el('h2', {}, t.name));
    const hr = el('div', { class: 'row', style: 'margin-top:6px' });
    hr.appendChild(el('span', { class: 'chip ' + (t.usage === 'USED' ? 'status-used' : 'status-unused') },
      t.usage === 'USED' ? '사용중' : '미사용'));
    if (t.subcategory && t.subcategory !== 'DIRECT') hr.appendChild(el('span', { class: 'chip subtle' }, t.subcategory));
    hr.appendChild(confBadge(t.confidence));
    if (t.is_isolated) hr.appendChild(el('span', { class: 'chip subtle' }, '고립'));
    header.appendChild(hr);

    body.innerHTML = '';
    // Description
    if (t.description) body.appendChild(el('p', {}, t.description));

    // Owner / consumers
    body.appendChild(el('h3', {}, '소유·소비'));
    const ownWrap = el('div', { class: 'tag-row' });
    if (t.owner_app) (t.owner_app.split('|')).forEach(o => o && ownWrap.appendChild(el('span', { class: 'row', style: 'margin-right:12px' },
      el('span', { class: 'muted small' }, '소유: '), appChip(o))));
    else ownWrap.appendChild(el('span', { class: 'muted small' }, 'ORM 모델 없음 — raw SQL로만 접근됨'));
    body.appendChild(ownWrap);
    if (t.consumer_apps.length) {
      const csWrap = el('div', { class: 'tag-row', style: 'margin-top:6px' },
        el('span', { class: 'muted small', style: 'margin-right:4px' }, '소비: '));
      t.consumer_apps.forEach(c => csWrap.appendChild(appChip(c)));
      body.appendChild(csWrap);
    }

    // Columns table
    body.appendChild(el('h3', {}, `컬럼 (${t.columns.length})`));
    const ct = el('table', { class: 'col-table' },
      el('thead', {}, el('tr', {},
        el('th', {}, '이름'), el('th', {}, '타입'), el('th', {}, 'Null'), el('th', {}, 'Key'), el('th', {}, '기본값'), el('th', {}, '설명')
      )),
    );
    const tb = el('tbody');
    t.columns.forEach(c => tb.appendChild(el('tr', {},
      el('td', { class: 'mono' }, c.name),
      el('td', { class: 'mono muted' }, c.type),
      el('td', { class: 'small muted' }, c.nullable ? 'YES' : 'NO'),
      el('td', { class: 'small' }, c.key || ''),
      el('td', { class: 'mono small muted' }, c.default || ''),
      el('td', { class: 'small' }, c.comment || '')
    )));
    ct.appendChild(tb);
    body.appendChild(ct);

    // Cluster
    if (t.cluster) {
      body.appendChild(el('h3', {}, '소속 클러스터'));
      body.appendChild(el('p', {},
        `${t.cluster.id} · 크기 ${t.cluster.size} · 중심 테이블 `,
        tableChip(t.cluster.hub_table)
      ));
    }

    // Incoming FKs
    if (t.incoming_fks.length) {
      body.appendChild(el('h3', {}, `들어오는 참조 (${t.incoming_fks.length})`));
      const ul = el('ul', { class: 'fk-list' });
      t.incoming_fks.forEach(fk => ul.appendChild(el('li', {},
        tableChip(fk.from_table), ' · ',
        el('span', { class: 'mono small muted' }, `${fk.from_column} → ${fk.to_column}`), ' · ',
        el('span', { class: 'small muted' }, fk.relation_type)
      )));
      body.appendChild(ul);
    }
    // Outgoing FKs
    if (t.outgoing_fks.length) {
      body.appendChild(el('h3', {}, `나가는 참조 (${t.outgoing_fks.length})`));
      const ul = el('ul', { class: 'fk-list' });
      t.outgoing_fks.forEach(fk => ul.appendChild(el('li', {},
        tableChip(fk.to_table), ' · ',
        el('span', { class: 'mono small muted' }, `${fk.from_column} → ${fk.to_column}`), ' · ',
        el('span', { class: 'small muted' }, fk.relation_type)
      )));
      body.appendChild(ul);
    }
    // Shared keys
    if (t.shared_keys.length) {
      body.appendChild(el('h3', {}, '공유 컬럼 (허브 키)'));
      const row = el('div', { class: 'tag-row' });
      t.shared_keys.forEach(s => row.appendChild(el('span', { class: 'chip subtle' },
        `${s.column} · ${s.co_tables_count}개 공유`)));
      body.appendChild(row);
    }

    // Endpoints touching
    const eps = ENDPOINTS.filter(e => e.tables_touched.includes(t.name));
    if (eps.length) {
      body.appendChild(el('h3', {}, `이 테이블을 건드리는 엔드포인트 (${eps.length})`));
      const ul = el('ul', { class: 'fk-list' });
      eps.slice(0, 40).forEach(e => ul.appendChild(el('li', {},
        el('span', { class: 'chip ' + (e.usage === 'CALLED' ? 'status-used' : 'status-unused') },
          e.http_methods.join('|')),
        ' ', el('span', { class: 'mono small' }, e.url_path),
        ' · ', appChip(e.app))));
      if (eps.length > 40) ul.appendChild(el('li', { class: 'muted small' }, `... 외 ${eps.length - 40}건`));
      body.appendChild(ul);
    }

    backdrop.classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function closeModal() {
    $('#modal').classList.remove('open');
    document.body.style.overflow = '';
    if (location.hash.startsWith('#/tables/')) location.hash = '#/tables';
  }

  // ============================================================
  //  Relations view
  // ============================================================
  function renderRelations() {
    const root = $('#view-relations');
    if (root.dataset.built) return;
    root.innerHTML = '';
    root.appendChild(el('h1', {}, '관계 그래프'));
    root.appendChild(el('p', { class: 'muted' },
      `${META.used_tables}개 사용중 테이블을 관계로 엮어 그린 지도. 실선은 개발자가 명시한 관계(HIGH), 점선은 코드 관찰로만 확인된 관계(MED)입니다.`));

    const controls = el('div', { class: 'graph-controls' });
    // Default: focus biggest cluster (C001) for readability; user can expand
    const cfg = { mode: 'main', showIso: false, onlyHigh: false, focus: '' };
    controls.appendChild(el('label', {}, '보기:'));
    const _mainSize = (DATA.clusters.normalization_components[0] || {}).size || 0;
    [['main', `거대 클러스터만 (${_mainSize})`], ['all', `전체 (${META.used_tables})`]].forEach(([v, lbl]) => {
      const wrap = el('label', { class: 'control-group', style: 'cursor:pointer' });
      const r = el('input', { type: 'radio', name: 'rg-mode', value: v });
      if (v === 'main') r.checked = true;
      r.addEventListener('change', () => { cfg.mode = v; draw(); });
      wrap.append(r, lbl);
      controls.appendChild(wrap);
    });
    const isoCb = el('input', { type: 'checkbox' });
    isoCb.addEventListener('change', () => { cfg.showIso = isoCb.checked; draw(); });
    controls.appendChild(el('label', { class: 'control-group' }, isoCb, '고립 테이블 포함'));
    const highCb = el('input', { type: 'checkbox' });
    highCb.addEventListener('change', () => { cfg.onlyHigh = highCb.checked; draw(); });
    controls.appendChild(el('label', { class: 'control-group' }, highCb, 'HIGH 관계만'));
    const search = el('input', { type: 'text', placeholder: '테이블명 검색...' });
    search.addEventListener('input', () => { cfg.focus = search.value.toLowerCase(); focusIt(); });
    controls.appendChild(el('span', { class: 'spacer' }));
    controls.appendChild(search);
    root.appendChild(controls);

    const frame = el('div', { class: 'graph-frame' });
    const canvas = el('div', { class: 'graph-canvas' });
    const aside = el('div', { class: 'graph-aside' });
    frame.append(canvas, aside);
    root.appendChild(frame);

    // Aside legend + stats
    aside.innerHTML = '';
    // Compute confidence distribution from actual data
    const _edgeConfDist = DATA.edges.table_edges.reduce((acc, e) => {
      acc[e.confidence] = (acc[e.confidence] || 0) + 1; return acc;
    }, {});
    const _mainCluster = DATA.clusters.normalization_components[0];
    aside.appendChild(el('h3', {}, '현황'));
    aside.appendChild(el('p', { class: 'small' },
      `사용중 테이블 ${META.used_tables}개 · 관계 엣지 ${META.total_table_edges}개`,
      el('br'),
      `HIGH ${_edgeConfDist.HIGH || 0} (개발자 의도) · MED ${_edgeConfDist.MED || 0} (raw SQL 관찰)`,
      el('br'), el('br'),
      el('strong', {}, '기본 보기: '),
      `중심 허브 `, el('span', { class: 'mono' }, _mainCluster.hub_table),
      `를 포함한 ${_mainCluster.size}개 테이블의 거대 클러스터만 우선 표시합니다. "전체"로 전환하면 위성 클러스터와 고립 테이블까지 볼 수 있습니다. 마우스 휠로 확대·축소, 드래그로 이동할 수 있습니다.`));
    aside.appendChild(el('h3', {}, '색 안내'));
    aside.appendChild(el('p', { class: 'small muted' }, '색상은 이름 도메인(prefix)으로 자동 배정됩니다.'));
    aside.appendChild(el('h3', {}, '선 안내'));
    aside.appendChild(el('div', { class: 'legend-row' }, el('span', { class: 'legend-line' }), '실선 — HIGH'));
    aside.appendChild(el('div', { class: 'legend-row' }, el('span', { class: 'legend-line dashed' }), '점선 — MED'));
    const detailHost = el('div', { style: 'margin-top:20px' });
    aside.appendChild(detailHost);

    // Prepare data
    const usedTables = Object.values(TABLES).filter(t => t.usage === 'USED');
    const domainColors = buildDomainPalette([...new Set(usedTables.map(t => t.domain_prefix))]);
    function nodeColor(d) { return domainColors[d.domain] || '#CBD5E1'; }
    function nodeSize(d) { return 3 + Math.sqrt(d.incoming + 0.1) * 2.2; }

    const nodes0 = usedTables.map(t => ({
      id: t.name,
      domain: t.domain_prefix,
      incoming: t.incoming_fks.length,
      outgoing: t.outgoing_fks.length,
      isIsolated: t.is_isolated,
    }));
    const links0 = DATA.edges.table_edges.map(e => ({
      source: e.table_a, target: e.table_b,
      confidence: e.confidence,
      sources: e.sources,
      column_a_to_b: e.column_a_to_b,
    }));

    const W = canvas.clientWidth || 900, H = 700;
    const svg = d3.select(canvas).append('svg').attr('viewBox', [0, 0, W, H]);
    const g = svg.append('g');
    let currentScale = 1;
    svg.call(d3.zoom().scaleExtent([0.3, 4]).on('zoom', ev => {
      g.attr('transform', ev.transform);
      currentScale = ev.transform.k;
      updateLabelVisibility();
    }));
    const linkLayer = g.append('g');
    const nodeLayer = g.append('g');

    function updateLabelVisibility() {
      // Show a node's label if its apparent size (radius × current zoom scale)
      // is above a threshold. Largest nodes stay labeled even when zoomed out;
      // smaller nodes reveal their names as the user zooms in.
      nodeLayer.selectAll('g.node').select('text')
        .style('opacity', function(d) {
          const apparent = (d3.select(this.parentNode).datum().__size || 0) * currentScale;
          return apparent >= 14 ? 1 : 0;
        });
    }

    // Top hub tables (by incoming FK) — always labeled as landmarks
    const HUB_LABELS = new Set(
      [...nodes0].sort((a, b) => b.incoming - a.incoming).slice(0, 12).map(n => n.id)
    );
    // Build membership of biggest cluster (C001)
    const mainCluster = DATA.clusters.normalization_components[0];
    const mainClusterSet = new Set(mainCluster ? mainCluster.members : []);

    let sim;
    function draw() {
      let nodes;
      if (cfg.mode === 'main') {
        nodes = nodes0.filter(n => mainClusterSet.has(n.id));
      } else {
        nodes = nodes0.filter(n => cfg.showIso || !n.isIsolated);
      }
      const nodeSet = new Set(nodes.map(n => n.id));
      const links = links0.filter(l =>
        nodeSet.has(typeof l.source === 'object' ? l.source.id : l.source)
        && nodeSet.has(typeof l.target === 'object' ? l.target.id : l.target)
        && (!cfg.onlyHigh || l.confidence === 'HIGH')
      ).map(l => ({ ...l }));

      if (sim) sim.stop();
      sim = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(links).id(d => d.id).distance(40).strength(0.45))
        .force('charge', d3.forceManyBody().strength(-55))
        .force('center', d3.forceCenter(W / 2, H / 2))
        .force('collide', d3.forceCollide().radius(d => nodeSize(d) + 2))
        .on('tick', tick);

      linkLayer.selectAll('*').remove();
      const lsel = linkLayer.selectAll('line').data(links).join('line')
        .attr('class', l => 'link conf-' + (l.confidence || 'MED').toLowerCase());

      nodeLayer.selectAll('*').remove();
      const gsel = nodeLayer.selectAll('g').data(nodes).join('g')
        .attr('class', d => 'node ' + (HUB_LABELS.has(d.id) ? 'hub-labeled' : ''))
        .each(function(d) { d.__size = nodeSize(d); })
        .call(drag(sim))
        .on('click', (ev, d) => { detailShow(d.id); });
      gsel.append('circle')
        .attr('r', d => nodeSize(d))
        .attr('fill', d => nodeColor(d));
      gsel.append('title').text(d => `${d.id} — ${d.domain} · 피참조 ${d.incoming} · 참조 ${d.outgoing}`);
      // Every node gets a label; visibility is zoom-driven (see updateLabelVisibility)
      gsel.append('text')
        .attr('dy', d => -nodeSize(d) - 4)
        .text(d => d.id)
        .style('opacity', 0);
      updateLabelVisibility();

      function tick() {
        lsel.attr('x1', d => d.source.x).attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
        gsel.attr('transform', d => `translate(${d.x},${d.y})`);
      }
    }
    function drag(sim) {
      return d3.drag()
        .on('start', (ev, d) => { if (!ev.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
        .on('drag', (ev, d) => { d.fx = ev.x; d.fy = ev.y; })
        .on('end', (ev, d) => { if (!ev.active) sim.alphaTarget(0); d.fx = null; d.fy = null; });
    }
    function focusIt() {
      const q = cfg.focus;
      nodeLayer.selectAll('g.node').classed('highlight', d => q && d.id.toLowerCase().includes(q));
    }
    function detailShow(id) {
      const t = TABLES[id]; if (!t) return;
      detailHost.innerHTML = '';
      detailHost.appendChild(el('h3', {}, '선택한 테이블'));
      detailHost.appendChild(el('p', { class: 'mono', style: 'margin:0 0 4px' }, id));
      detailHost.appendChild(el('p', { class: 'small muted' },
        `${t.domain_prefix} · 피참조 ${t.incoming_fks.length} · 참조 ${t.outgoing_fks.length} · 컬럼 ${t.columns.length}`));
      detailHost.appendChild(el('button', {
        class: 'ghost-btn', onclick: () => openTableModal(id)
      }, '상세 보기'));
    }

    draw();
    root.dataset.built = '1';
  }

  // deterministic domain palette
  function buildDomainPalette(domains) {
    const palette = ['#2563EB', '#DC2626', '#16A34A', '#F59E0B', '#7C3AED', '#0891B2', '#DB2777', '#65A30D', '#EA580C', '#0D9488', '#4338CA', '#92400E', '#A21CAF', '#374151', '#1E40AF', '#B91C1C', '#166534', '#6B21A8', '#0E7490', '#C2410C'];
    const map = {};
    domains.sort().forEach((d, i) => { map[d] = palette[i % palette.length]; });
    return map;
  }

  // ============================================================
  //  Endpoints view
  // ============================================================
  function renderEndpoints() {
    const root = $('#view-endpoints');
    if (root.dataset.built) return;
    root.innerHTML = '';
    root.appendChild(el('h1', {}, 'API 엔드포인트'));
    root.appendChild(el('p', { class: 'muted' },
      `${META.total_endpoints}개의 백엔드 엔드포인트 중 프론트에서 실제로 호출되는 것과 그렇지 않은 것을 구분해 보여줍니다.`));

    // --- Highlights: 주목할 엔드포인트 3종 ---
    const complex = [...ENDPOINTS].filter(e => (e.tables_touched || []).length >= 5)
      .sort((a, b) => b.tables_touched.length - a.tables_touched.length).slice(0, 10);
    const zeroTouch = ENDPOINTS.filter(e => (e.tables_touched || []).length === 0);
    const expensiveDead = [...ENDPOINTS].filter(e => e.usage === 'UNCALLED' && (e.tables_touched || []).length >= 3)
      .sort((a, b) => b.tables_touched.length - a.tables_touched.length).slice(0, 10);

    const hi = el('div', { class: 'grid grid-3', style: 'margin-top:20px' });
    const makeHiCard = (title, desc, items, renderItem) => {
      const card = el('div', { class: 'card' },
        el('h3', { style: 'margin-top:0' }, title),
        el('p', { class: 'small muted', style: 'margin:0 0 10px' }, desc));
      const ul = el('ul', { style: 'list-style:none;padding:0;margin:0;font-size:13px' });
      items.slice(0, 10).forEach(e => ul.appendChild(renderItem(e)));
      if (items.length === 0) ul.appendChild(el('li', { class: 'muted small' }, '해당 없음'));
      card.appendChild(ul);
      if (items.length > 10) card.appendChild(el('div', { class: 'muted small', style: 'margin-top:8px' }, `외 ${items.length - 10}건`));
      return card;
    };
    hi.appendChild(makeHiCard(
      '복합 오케스트레이션',
      '한 번의 호출에서 5개 이상의 테이블을 건드리는 고복잡도 엔드포인트 (5는 임의 임계값).',
      complex,
      e => el('li', { style: 'padding:3px 0;border-bottom:1px dashed var(--line-soft)' },
        el('span', { class: 'chip subtle' }, String(e.tables_touched.length) + '개 테이블'),
        ' ',
        el('span', { class: 'mono', style: 'font-size:12px' }, e.url_path),
        ' · ', appChip(e.app))));
    hi.appendChild(makeHiCard(
      '테이블 0개 엔드포인트',
      '어떤 테이블도 직접 건드리지 않는 엔드포인트 (헬스체크·외부 프록시·AI 호출 등).',
      zeroTouch,
      e => el('li', { style: 'padding:3px 0;border-bottom:1px dashed var(--line-soft)' },
        el('span', { class: 'chip ' + (e.usage === 'CALLED' ? 'status-used' : 'status-unused') }, e.http_methods.join('|')),
        ' ', el('span', { class: 'mono', style: 'font-size:12px' }, e.url_path),
        ' · ', appChip(e.app))));
    hi.appendChild(makeHiCard(
      '방치된 복합 API',
      '프론트에서 호출되지 않지만 3개 이상 테이블에 손을 뻗는 엔드포인트. 정리 시 가장 눈에 띄는 후보.',
      expensiveDead,
      e => el('li', { style: 'padding:3px 0;border-bottom:1px dashed var(--line-soft)' },
        el('span', { class: 'chip subtle' }, String(e.tables_touched.length) + '개'),
        ' ',
        el('span', { class: 'mono', style: 'font-size:12px' }, e.url_path),
        ' · ', appChip(e.app))));
    root.appendChild(hi);

    // Ratio bar
    const total = ENDPOINTS.length;
    const called = ENDPOINTS.filter(e => e.usage === 'CALLED').length;
    const uncalled = total - called;
    const strip = el('div', { class: 'ep-dashboard-strip' });
    const leftCard = el('div', { class: 'card' },
      el('div', { class: 'row-between' },
        el('span', {}, el('span', { class: 'dot green' }), `호출됨 ${called} (${pct(called, total)}%)`),
        el('span', {}, el('span', { class: 'dot red' }), `호출 안 됨 ${uncalled} (${pct(uncalled, total)}%)`)
      )
    );
    const ratioBar = el('div', { class: 'ep-ratio-bar' });
    const s1 = el('span', { style: `background:var(--green);width:${pct(called, total)}%` });
    const s2 = el('span', { style: `background:var(--red);width:${pct(uncalled, total)}%` });
    ratioBar.append(s1, s2);
    leftCard.appendChild(ratioBar);
    strip.appendChild(leftCard);

    // Per-app bar
    const perApp = Object.values(APPS).filter(a => a.endpoints_total > 0)
      .sort((a, b) => b.uncalled_pct - a.uncalled_pct);
    const barCard = el('div', { class: 'card' },
      el('h3', {}, '앱별 미사용률'),
      el('p', { class: 'small muted', style: 'margin-bottom:8px' }, '긴 막대일수록 방치된 엔드포인트 비중이 높습니다.')
    );
    const barList = el('div');
    perApp.forEach(a => {
      const row = el('div', { style: 'display:grid;grid-template-columns:120px 1fr 80px;gap:10px;align-items:center;padding:3px 0' });
      row.appendChild(el('span', { class: 'small mono' }, a.name));
      const bar = el('div', { style: 'height:10px;border-radius:3px;overflow:hidden;display:flex;background:var(--gray-100)' });
      bar.appendChild(el('span', { style: `background:var(--red);width:${a.uncalled_pct}%` }));
      bar.appendChild(el('span', { style: `background:var(--green);width:${100 - a.uncalled_pct}%` }));
      row.appendChild(bar);
      row.appendChild(el('span', { class: 'small muted', style: 'text-align:right' }, `${a.endpoints_uncalled}/${a.endpoints_total}`));
      barList.appendChild(row);
    });
    barCard.appendChild(barList);
    strip.appendChild(barCard);
    root.appendChild(strip);

    // --- Filter controls ---
    const filters = { usage: 'all', methods: new Set(), q: '' };
    const ctrl = el('div', { class: 'graph-controls', style: 'margin-top:18px;border-radius:10px;border:1px solid var(--line)' });
    ctrl.appendChild(el('label', {}, '상태:'));
    ['all','CALLED','UNCALLED'].forEach(v => {
      const wrap = el('label', { class: 'control-group', style: 'cursor:pointer' });
      const r = el('input', { type: 'radio', name: 'ep-usage', value: v });
      if (v === 'all') r.checked = true;
      r.addEventListener('change', () => { filters.usage = v; renderList(); });
      wrap.append(r, v === 'all' ? '전체' : v === 'CALLED' ? '호출됨' : '호출안됨');
      ctrl.appendChild(wrap);
    });
    ctrl.appendChild(el('span', { style: 'width:1px;height:18px;background:var(--line);margin:0 4px' }));
    ctrl.appendChild(el('label', {}, '메소드:'));
    ['GET','POST','PUT','DELETE','PATCH'].forEach(m => {
      const wrap = el('label', { class: 'control-group', style: 'cursor:pointer' });
      const cb = el('input', { type: 'checkbox', value: m });
      cb.addEventListener('change', () => {
        if (cb.checked) filters.methods.add(m); else filters.methods.delete(m);
        renderList();
      });
      wrap.append(cb, m);
      ctrl.appendChild(wrap);
    });
    ctrl.appendChild(el('span', { class: 'spacer' }));
    const qInput = el('input', { type: 'text', placeholder: 'URL 검색...' });
    qInput.addEventListener('input', () => { filters.q = qInput.value.toLowerCase(); renderList(); });
    ctrl.appendChild(qInput);
    root.appendChild(ctrl);

    // App list
    const list = el('div', { class: 'ep-app-list' });
    root.appendChild(list);
    root.dataset.built = '1';

    function filteredEndpoints() {
      return ENDPOINTS.filter(e => {
        if (filters.usage !== 'all' && e.usage !== filters.usage) return false;
        if (filters.methods.size && !e.http_methods.some(m => filters.methods.has(m))) return false;
        if (filters.q && !e.url_path.toLowerCase().includes(filters.q)) return false;
        return true;
      });
    }

    function renderList() {
      list.innerHTML = '';
      const eps = filteredEndpoints();
      if (eps.length === 0) {
        list.appendChild(el('div', { class: 'empty-state' },
          el('h3', {}, '조건에 맞는 엔드포인트가 없습니다'),
          el('p', { class: 'muted' }, '상단 필터를 바꾸거나 초기화해보세요.'),
          el('button', { class: 'ghost-btn', onclick: () => {
            filters.usage = 'all'; filters.methods.clear(); filters.q = '';
            qInput.value = '';
            $$('input[name=ep-usage]').forEach(x => x.checked = x.value === 'all');
            $$('input[type=checkbox]', ctrl).forEach(x => x.checked = false);
            renderList();
          }}, '필터 초기화')
        ));
        return;
      }
      const grouped = {};
      eps.forEach(e => { (grouped[e.app] ||= []).push(e); });
      const totalC = eps.filter(e => e.usage === 'CALLED').length;
      const totalU = eps.length - totalC;
      list.appendChild(el('div', { class: 'muted small', style: 'padding:10px 16px;border-bottom:1px solid var(--line)' },
        `표시 중: ${eps.length}건 · 호출 ${totalC} / 미호출 ${totalU}`));
      Object.keys(grouped).sort().forEach(appName => renderAppRow(appName, grouped[appName]));
    }

    function renderAppRow(appName, epsRaw) {
      const eps = epsRaw.sort((a, b) => a.url_path.localeCompare(b.url_path));
      const c = eps.filter(x => x.usage === 'CALLED').length;
      const u = eps.length - c;
      const row = el('div', { class: 'ep-app-row' });
      const head = el('div', { class: 'ep-app-row-header' });
      head.appendChild(el('div', { class: 'ep-app-row-name' }, appName));
      const bar = el('div', { class: 'ep-app-row-bar' });
      bar.appendChild(el('span', { style: `background:var(--green);width:${pct(c, eps.length)}%` }));
      bar.appendChild(el('span', { style: `background:var(--red);width:${pct(u, eps.length)}%` }));
      head.appendChild(bar);
      head.appendChild(el('span', { class: 'ep-app-row-counts' }, `호출 ${c} / 미호출 ${u} · 총 ${eps.length}`));
      row.appendChild(head);

      const listPane = el('div', { class: 'ep-list' });
      const tbl = el('table', { class: 'ep-list-table' },
        el('thead', {}, el('tr', {},
          el('th', {}, '메소드'), el('th', {}, 'URL'), el('th', {}, '뷰'),
          el('th', {}, '테이블'), el('th', {}, '상태'), el('th', {}, 'Conf')
        )),
      );
      const tbody = el('tbody');
      eps.forEach(e => {
        const tr = el('tr', { class: e.usage === 'CALLED' ? '' : 'uncalled' });
        tr.appendChild(el('td', {}, e.http_methods.map(m => el('span', { class: 'badge badge-gray' }, m))));
        tr.appendChild(el('td', { class: 'mono' }, e.url_path));
        tr.appendChild(el('td', { class: 'mono small' }, e.view_ref));
        const tdTables = el('td', { class: 'tag-row' });
        (e.tables_touched || []).slice(0, 5).forEach(t => tdTables.appendChild(tableChip(t)));
        if (e.tables_touched.length > 5) tdTables.appendChild(el('span', { class: 'muted small' }, `+${e.tables_touched.length - 5}`));
        tr.appendChild(tdTables);
        tr.appendChild(el('td', {}, el('span', { class: 'chip ' + (e.usage === 'CALLED' ? 'status-used' : 'status-unused') },
          e.usage === 'CALLED' ? '호출됨' : '호출안됨')));
        tr.appendChild(el('td', {}, confBadge(e.confidence || 'LOW')));
        tbody.appendChild(tr);
      });
      tbl.appendChild(tbody);
      listPane.appendChild(tbl);
      row.appendChild(listPane);
      head.addEventListener('click', () => row.classList.toggle('open'));
      list.appendChild(row);
    }

    renderList();
  }

  // ============================================================
  //  Quality view
  // ============================================================
  function renderQuality() {
    const root = $('#view-quality');
    if (root.dataset.built) return;
    root.innerHTML = '';
    root.appendChild(el('h1', {}, '데이터 품질'));
    root.appendChild(el('p', { class: 'muted' },
      '이 시스템에 남아있는 기술 부채와 설계 이상 징후를 분류해 보여줍니다. 각 항목에는 왜 중요한지와 다음 조치 힌트가 함께 붙습니다.'));

    // 1. Zombie models
    const z = DATA.diagnostics.zombie_models;
    const secZ = el('div', { class: 'quality-section' });
    secZ.appendChild(el('h2', {}, el('span', { class: 'dot red' }), `유령 모델 ${z.length}건`));
    secZ.appendChild(el('p', { class: 'why' },
      'Django 코드에는 모델 클래스가 있지만 실제 데이터베이스 스키마에 해당 테이블이 없습니다. 이 모델을 호출하면 런타임 오류가 발생합니다.'));
    secZ.appendChild(nextStep('코드에서 모델을 제거하거나, 실제로 필요한 테이블이라면 DB에 생성한다. 현재는 아무 코드도 호출하지 않아 에러가 드러나지 않았을 뿐.'));
    const zItems = el('div', { class: 'items' });
    z.forEach(x => {
      const item = el('div', { class: 'quality-item' });
      item.appendChild(el('div', { class: 'title' }, x.model));
      item.appendChild(el('div', { class: 'detail' },
        `선언된 테이블: `, el('span', { class: 'mono' }, x.declared_table), el('br'),
        `파일: `, el('span', { class: 'mono small' }, x.file), el('br'),
        `역할: FK의 ${x.direction === 'from' ? '출발' : '도착'}점`));
      zItems.appendChild(item);
    });
    secZ.appendChild(zItems);
    secZ.appendChild(evidenceLine('core_materials/site_data.json → diagnostics.zombie_models · intermediate/extract_relations.py'));
    root.appendChild(secZ);

    // 2. NO_MODEL tables
    const nm = DATA.diagnostics.no_model_tables;
    const secN = el('div', { class: 'quality-section' });
    secN.appendChild(el('h2', {}, el('span', { class: 'dot amber' }), `ORM 모델 없이 쓰이는 테이블 ${nm.length}건`));
    secN.appendChild(el('p', { class: 'why' },
      'Django 모델 없이 raw SQL로만 접근하는 테이블입니다. 스키마 변경 시 코드가 자동으로 반영되지 않아 깨지기 쉽습니다.'));
    secN.appendChild(nextStep('Django 모델로 래핑해 ORM 보호 하에 두거나, 의도적으로 raw SQL을 유지한다면 그 이유(성능·레거시 등)를 주석·위키에 남긴다.'));
    const nmRow = el('div', { class: 'tag-row' });
    nm.forEach(t => nmRow.appendChild(tableChip(t)));
    secN.appendChild(nmRow);
    secN.appendChild(evidenceLine('core_materials/site_data.json → diagnostics.no_model_tables · intermediate/map_apps_tables.py'));
    root.appendChild(secN);

    // 3. Denormalization hotspots
    const hs = DATA.clusters.denormalization_hotspots.filter(h => h.hotspot_level === 'SEVERE' || h.hotspot_level === 'HIGH');
    const secH = el('div', { class: 'quality-section' });
    secH.appendChild(el('h2', {}, el('span', { class: 'dot red' }), `비정규화 핫스팟 ${hs.length}건`));
    secH.appendChild(el('p', { class: 'why' },
      '같은 컬럼명을 여러 테이블이 공유하는데 FK로 묶여 있지 않습니다. JOIN의 안전성·정합성을 코드가 아닌 관행에 기대고 있는 영역입니다.'));
    secH.appendChild(nextStep('관계가 있어야 한다면 FK를 추가한다. 의도된 비정규화(성능·스냅샷 등)라면 해당 컬럼의 공유 의도와 관계의 근거를 스키마 주석으로 남긴다.'));
    const hItems = el('div', { class: 'items' });
    hs.forEach(h => {
      const it = el('div', { class: 'quality-item' });
      it.appendChild(el('div', { class: 'title' }, h.shared_column));
      it.appendChild(el('div', { class: 'detail' },
        `${h.tables_sharing}개 테이블이 공유 · FK로 묶인 쌍 ${h.fk_linked_pairs}/${h.total_possible_pairs}`, el('br'),
        `심각도: `, el('span', { class: 'badge ' + (h.hotspot_level === 'SEVERE' ? 'badge-red' : 'badge-med') }, h.hotspot_level)));
      hItems.appendChild(it);
    });
    secH.appendChild(hItems);
    secH.appendChild(evidenceLine('core_materials/denormalization_hotspots.csv · intermediate/analyze_normalization.py'));
    root.appendChild(secH);

    // 4. Domain vs FK gap
    const g = DATA.clusters.domain_gaps.filter(x => x.gap_severity === 'SEVERE' || x.gap_severity === 'HIGH');
    const secG = el('div', { class: 'quality-section' });
    secG.appendChild(el('h2', {}, el('span', { class: 'dot amber' }), `도메인 vs 관계 갭 ${g.length}건`));
    secG.appendChild(el('p', { class: 'why' },
      '이름 규칙으로는 같은 도메인이지만 테이블 간 FK 커버리지가 낮아, 같은 식구가 서로를 모르는 상태입니다.'));
    secG.appendChild(nextStep('해당 도메인이 실제로 한 가족이 맞는지 재점검한다. 맞다면 FK로 묶고, 트렌딩·집계 출력처럼 의도적으로 독립 설계된 것이라면 그 설계 의도를 문서화한다.'));
    const gItems = el('div', { class: 'items' });
    g.forEach(x => {
      const it = el('div', { class: 'quality-item' });
      it.appendChild(el('div', { class: 'title' }, x.prefix + '_*'));
      it.appendChild(el('div', { class: 'detail' },
        `${x.size}개 테이블 · FK 커버리지 ${(x.fk_coverage * 100).toFixed(1)}%`, el('br'),
        `고립된 식구 ${x.isolated_members}개 · `,
        el('span', { class: 'badge ' + (x.gap_severity === 'SEVERE' ? 'badge-red' : 'badge-med') }, x.gap_severity)));
      gItems.appendChild(it);
    });
    secG.appendChild(gItems);
    secG.appendChild(evidenceLine('core_materials/domain_vs_fk_gap.csv · intermediate/analyze_name_clusters.py'));
    root.appendChild(secG);

    // 5. Self-loops
    const sl = DATA.diagnostics.self_loops;
    if (sl.length) {
      const secS = el('div', { class: 'quality-section' });
      secS.appendChild(el('h2', {}, el('span', { class: 'dot blue' }), `자기참조 ${sl.length}건`));
      secS.appendChild(el('p', { class: 'why' },
        '같은 테이블 안의 행이 다른 행을 참조합니다. 일반적으로 계층(대댓글·폴더 트리 등)을 의도한 설계로, 이 경우 정상입니다.'));
      secS.appendChild(nextStep('코드 리뷰 시 의도한 계층 구조인지만 확인하면 별도 조치 필요 없음.'));
      const items = el('div', { class: 'items' });
      sl.forEach(s => items.appendChild(el('div', { class: 'quality-item' },
        el('div', { class: 'title' }, s.table),
        el('div', { class: 'detail' }, s.column))));
      secS.appendChild(items);
      secS.appendChild(evidenceLine('core_materials/site_data.json → diagnostics.self_loops · intermediate/extract_relations.py'));
      root.appendChild(secS);
    }

    // 6. Multi-owner
    const mo = DATA.diagnostics.multi_owner_tables;
    if (mo.length) {
      const secM = el('div', { class: 'quality-section' });
      secM.appendChild(el('h2', {}, el('span', { class: 'dot amber' }), `중복 소유 테이블 ${mo.length}건`));
      secM.appendChild(el('p', { class: 'why' },
        '두 개 이상의 Django 앱이 같은 테이블에 대해 모델을 선언하고 있습니다. 의도된 분리라면 괜찮지만, 권한·마이그레이션 충돌 위험이 있습니다.'));
      secM.appendChild(nextStep('소유권을 한 앱으로 단일화하고 다른 앱은 import해 사용한다. 권한 분리를 위해 의도한 구조라면 어느 앱이 마이그레이션을 책임지는지 명시한다.'));
      const items = el('div', { class: 'items' });
      mo.forEach(m => items.appendChild(el('div', { class: 'quality-item' },
        el('div', { class: 'title' }, m.table),
        el('div', { class: 'detail' }, '소유: ' + m.owners.join(' · ')))));
      secM.appendChild(items);
      secM.appendChild(evidenceLine('core_materials/site_data.json → diagnostics.multi_owner_tables · intermediate/map_apps_tables.py'));
      root.appendChild(secM);
    }

    root.dataset.built = '1';
  }

  // ============================================================
  //  About view
  // ============================================================
  function renderAbout() {
    const root = $('#view-about');
    if (root.dataset.built) return;
    root.innerHTML = '';
    root.appendChild(el('h1', {}, '전제와 한계'));
    root.appendChild(el('p', { class: 'muted' },
      '이 분석이 어느 범위에서 확실하고, 어디서부터 주의가 필요한지 정직하게 밝힙니다.'));

    // 1. Closed world
    const s1 = el('div', { class: 'about-section' });
    s1.appendChild(el('h2', {}, '1. 무엇을 가정했는가 — 폐쇄 세계'));
    s1.appendChild(el('p', {},
      '이 분석은 아래 세 가지 외에 다른 소비자·생산자가 존재하지 않는다고 전제합니다.'));
    const ul1 = el('ul');
    ul1.appendChild(el('li', {}, '백엔드 저장소: ', el('code', {}, META.source_trees.backend)));
    ul1.appendChild(el('li', {}, '프론트엔드 저장소: ', el('code', {}, META.source_trees.frontend)));
    ul1.appendChild(el('li', {}, '하이픈 데이터베이스 스키마'));
    s1.appendChild(ul1);
    s1.appendChild(el('p', { class: 'muted small' },
      '모바일앱·제휴 API·외부 배치 파이프라인은 존재하지 않는 것으로 가정했습니다. 만약 이런 소비자가 실제로 있다면 "미사용" 라벨 중 일부가 실은 사용 중일 수 있습니다.'));
    root.appendChild(s1);

    // 2. Reliability per step
    const s2 = el('div', { class: 'about-section' });
    s2.appendChild(el('h2', {}, '2. 단계별 신뢰도'));
    const t = el('table', { class: 'conf-table' },
      el('thead', {}, el('tr', {},
        el('th', {}, '단계'), el('th', {}, '내용'), el('th', {}, '신뢰도'), el('th', {}, '근거'), el('th', {}, '재현 스크립트')
      )),
    );
    const tb = el('tbody');
    const _epTotal = META.total_endpoints;
    const steps = [
      ['1', '테이블 사용 여부 1차 라벨링', '95%', 'db_table= 및 raw SQL 패턴 하드코딩 매칭', 'intermediate/label_tables.py'],
      ['2', '폐쇄 세계 전제로 USED/UNUSED 확정', '95%', '외부 소비자 불확실성 제거', 'intermediate/finalize_labels.py'],
      ['3', '앱 ↔ 테이블 매핑', '90%', '앱명-단어 충돌 오탐 보정 후', 'intermediate/map_apps_tables.py, boost_pass.py'],
      ['4', '테이블 간 관계 (FK)', '95%', 'models.py AST + 컬럼 교차검증 98%', 'intermediate/extract_relations.py'],
      ['4.5', '정규화 지형', '95%', '관계 그래프 연결 성분 기반', 'intermediate/analyze_normalization.py, analyze_name_clusters.py'],
      ['5', 'API 엔드포인트 전수 추출', '99%', `urls.py/views.py AST, HTTP 메소드 미해결 1/${_epTotal}`, 'intermediate/extract_endpoints.py'],
      ['6', '엔드포인트 호출 여부', '높음', '폐쇄 세계 가정 하 프론트 스캔 · exact match 97%', 'intermediate/detect_unused_endpoints.py'],
      ['7', '서비스 간 관계', '높음', 'import/shared_table/cron 세 신호 결합', 'intermediate/extract_service_edges.py'],
    ];
    steps.forEach(([n, d, c, e, script]) => tb.appendChild(el('tr', {},
      el('td', { class: 'mono' }, 'Step ' + n),
      el('td', {}, d), el('td', {}, c), el('td', { class: 'small' }, e),
      el('td', { class: 'mono small muted' }, script))));
    t.appendChild(tb);
    s2.appendChild(t);
    root.appendChild(s2);

    // 3. Simplifications
    const s3 = el('div', { class: 'about-section' });
    s3.appendChild(el('h2', {}, '3. 의도적으로 단순화한 것'));
    const ul3 = el('ul');
    ul3.appendChild(el('li', {}, '동적으로 조합되는 테이블명(예: f"YT_bumper_crawl_video_list_{country}")은 전수 탐지하지 못합니다. 샘플 검증 결과 실제로는 0건이었습니다.'));
    ul3.appendChild(el('li', {}, '복잡한 서브쿼리 JOIN은 일부 누락될 수 있습니다. ORM이 생성하는 JOIN은 모델 FK로 이미 커버됩니다.'));
    ul3.appendChild(el('li', {}, '프론트엔드의 동적 URL 조합(변수 베이스 + 하위 경로)은 대부분 해석되지만 일부 prefix-match로 떨어집니다.'));
    s3.appendChild(ul3);
    root.appendChild(s3);

    // 3.5. Runtime blind spots
    const sBlind = el('div', { class: 'about-section' });
    sBlind.appendChild(el('h2', {}, '4. 엔드포인트 호출 스캔의 사각지대'));
    sBlind.appendChild(el('p', {},
      '"프론트에서 호출되지 않음(UNCALLED)"은 ',
      el('strong', {}, 'Next.js 소스 기준'),
      '의 판정입니다. 다음 호출 경로는 이 스캔 밖에 있습니다 — UNCALLED라도 실제로는 아래 경로로 살아있을 수 있습니다.'));
    const ulBlind = el('ul');
    ulBlind.appendChild(el('li', {}, 'Celery/cron 등 백그라운드 스케줄러에서의 직접 호출 (일부는 Step 7의 CRON 엣지로 간접 포착).'));
    ulBlind.appendChild(el('li', {}, 'Django admin 액션, 관리 명령(manage.py), shell 통한 수동 호출.'));
    ulBlind.appendChild(el('li', {}, '마이그레이션 스크립트 내부에서의 일회성 호출.'));
    ulBlind.appendChild(el('li', {}, '외부 서비스(슬랙 봇·깃허브 웹훅 등)의 웹훅 콜백. 폐쇄 세계 전제를 엄격히 지키면 없지만, 실제 운영에서는 존재할 수 있음.'));
    sBlind.appendChild(ulBlind);
    sBlind.appendChild(el('p', { class: 'small muted' },
      '따라서 "UNCALLED" 리스트는 "제거 후보"가 아니라 "조사 후보"로 다루는 것이 안전합니다.'));
    root.appendChild(sBlind);

    // 4. Manual review items
    const s4 = el('div', { class: 'about-section' });
    s4.appendChild(el('h2', {}, '5. 수동 검수 권장'));
    const ul4 = el('ul');
    ul4.appendChild(el('li', {}, '일반 영단어 테이블 중 ages, genders는 DB 문맥이 아닌 단어로만 등장해 NOT_A_DB_REF로 분류됐습니다. 실제 DB 상태 확인 권장.'));
    const _lowConfEpCount = ENDPOINTS.filter(e => e.confidence === 'LOW').length;
    ul4.appendChild(el('li', {}, `LOW confidence 엔드포인트 ${_lowConfEpCount}건 (API 엔드포인트 뷰에서 확인)`));
    ul4.appendChild(el('li', {}, `유령 모델 ${DATA.diagnostics.zombie_models.length}건은 코드에서 제거하거나 DB에 테이블을 생성하는 결정이 필요합니다.`));
    s4.appendChild(ul4);
    root.appendChild(s4);

    // 5. Snapshot
    const s5 = el('div', { class: 'about-section' });
    s5.appendChild(el('h2', {}, '6. 스냅샷 시점 및 재현'));
    s5.appendChild(el('p', {}, `분석 생성일: `, el('code', {}, META.generated_at)));
    s5.appendChild(el('p', { class: 'small muted' },
      '이 시점 이후의 코드·스키마 변경은 반영되지 않습니다. ', el('code', {}, 'intermediate/'),
      ' 폴더의 Python 스크립트들을 Step 순서대로 다시 실행한 뒤 ',
      el('code', {}, 'intermediate/build_html.py'),
      '로 번들하면 재생성됩니다.'));

    // 6. AI learning — JSON companion
    const s6 = el('div', { class: 'about-section' });
    s6.appendChild(el('h2', {}, '7. 내부 AI 학습 시 주의'));
    s6.appendChild(el('p', {},
      '이 HTML은 사람이 읽는 용도로 설계됐습니다. 테이블 상세 · 엔드포인트 목록 등은 ' +
      'JavaScript로 렌더링되므로 HTML 텍스트를 그대로 인덱싱하면 내용이 누락됩니다.'));
    s6.appendChild(el('p', {},
      el('strong', {}, 'AI 학습 파이프라인에는 HTML과 함께 ', el('code', {}, 'core_materials/site_data.json'), ' 을 함께 투입해주세요.'),
      ' 모든 테이블 · 관계 · 엔드포인트 데이터가 구조화된 JSON으로 들어 있습니다.'));
    s6.appendChild(el('p', { class: 'small muted' },
      `스키마 최상위 키: meta, tables, apps, endpoints, edges, clusters, diagnostics. ` +
      `데이터 규모: 테이블 ${META.total_schema_tables}, 엔드포인트 ${META.total_endpoints}, 앱 ${META.app_count}, 관계 엣지 ${META.total_table_edges}.`));
    root.appendChild(s5);
    root.appendChild(s6);

    root.dataset.built = '1';
  }

  const VIEWS = {
    home: renderHome,
    services: renderServices,
    tables: renderTables,
    relations: renderRelations,
    endpoints: renderEndpoints,
    quality: renderQuality,
    about: renderAbout,
  };

  // Initialization — bind meta-date, sidebar counts, modal handlers
  window.addEventListener('DOMContentLoaded', () => {
    // Snapshot dates
    const md = $('#meta-date'); if (md) md.textContent = META.generated_at;
    const ts1 = $('#topbar-snapshot'); if (ts1) ts1.textContent = META.generated_at;
    const ts2 = $('#sidebar-snapshot'); if (ts2) ts2.textContent = META.generated_at;

    // Sidebar counts — dynamically reflect data volume
    const setCnt = (id, n) => { const el = $(id); if (el) el.textContent = String(n); };
    setCnt('#cnt-services', META.app_count);
    setCnt('#cnt-tables', META.total_schema_tables);
    setCnt('#cnt-relations', META.total_table_edges);
    setCnt('#cnt-endpoints', META.total_endpoints);
    const qCount = (DATA.diagnostics.zombie_models.length > 0 ? 1 : 0)
                 + (DATA.diagnostics.no_model_tables.length > 0 ? 1 : 0)
                 + (DATA.clusters.denormalization_hotspots.filter(h => h.hotspot_level === 'SEVERE').length > 0 ? 1 : 0)
                 + (DATA.clusters.domain_gaps.filter(g => g.gap_severity === 'SEVERE' || g.gap_severity === 'HIGH').length > 0 ? 1 : 0)
                 + (DATA.diagnostics.multi_owner_tables.length > 0 ? 1 : 0)
                 + (DATA.diagnostics.self_loops.length > 0 ? 1 : 0);
    setCnt('#cnt-quality', qCount);

    // Modal
    $('#modal-close').addEventListener('click', closeModal);
    $('#modal').addEventListener('click', (e) => { if (e.target.id === 'modal') closeModal(); });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeModal(); });

    // Global search (simple name-match across tables + apps + endpoints)
    setupGlobalSearch();
  });

  function setupGlobalSearch() {
    const input = $('#global-search');
    if (!input) return;
    const results = el('div', { class: 'search-results' });
    results.style.display = 'none';
    input.parentElement.appendChild(results);

    function close() { results.style.display = 'none'; results.innerHTML = ''; }

    input.addEventListener('input', () => {
      const q = input.value.trim().toLowerCase();
      if (q.length < 2) { close(); return; }
      const hits = [];
      for (const t of Object.values(TABLES)) {
        if (t.name.toLowerCase().includes(q)) hits.push({ kind: '테이블', name: t.name, href: '#/tables/' + encodeURIComponent(t.name) });
        if (hits.length >= 10) break;
      }
      for (const a of Object.values(APPS)) {
        if (a.name.toLowerCase().includes(q)) hits.push({ kind: '앱', name: a.name, href: '#/services?focus=' + encodeURIComponent(a.name) });
        if (hits.length >= 14) break;
      }
      for (const e of ENDPOINTS) {
        if (e.url_path.toLowerCase().includes(q)) hits.push({ kind: 'API', name: (e.http_methods[0] || '') + ' ' + e.url_path, href: '#/endpoints' });
        if (hits.length >= 20) break;
      }
      if (hits.length === 0) { close(); return; }
      results.innerHTML = '';
      hits.slice(0, 20).forEach(h => {
        const row = el('a', { class: 'search-row', href: h.href },
          el('span', { class: 'search-kind' }, h.kind),
          el('span', { class: 'search-name' }, h.name));
        row.addEventListener('click', close);
        results.appendChild(row);
      });
      results.style.display = 'block';
    });

    input.addEventListener('blur', () => setTimeout(close, 120));
    document.addEventListener('keydown', (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') { e.preventDefault(); input.focus(); }
    });
  }

})();
