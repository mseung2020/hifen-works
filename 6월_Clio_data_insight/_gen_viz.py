# -*- coding: utf-8 -*-
import json
D = json.load(open('_viz_data.json', encoding='utf-8'))
DATA_JSON = json.dumps(D, ensure_ascii=False)

HTML = r'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>조회수 대박 ≠ 올리브영 랭킹</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0/dist/chartjs-plugin-datalabels.min.js"></script>
<style>
  *{box-sizing:border-box; margin:0; padding:0;}
  body{ font-family:'Pretendard',-apple-system,'Apple SD Gothic Neo',sans-serif;
        background:#fff; color:#1a1a1a; display:flex; justify-content:center;
        padding:48px 24px; -webkit-font-smoothing:antialiased; }
  .wrap{ width:100%; max-width:860px; }
  section{ margin-bottom:64px; }
  .eyebrow{ font-size:13px; letter-spacing:.08em; color:#3b82f6; font-weight:600; text-align:center; }
  h2{ font-size:22px; font-weight:800; text-align:center; margin-top:8px; letter-spacing:-.02em; }
  .sub{ font-size:13px; color:#8a8f98; text-align:center; margin-top:8px; line-height:1.6; }
  .legend{ display:flex; justify-content:center; gap:20px; margin-top:16px; font-size:13px; font-weight:600; color:#4b5563; }
  .legend .it{ display:flex; align-items:center; gap:7px; }
  .legend .sw{ width:13px; height:13px; border-radius:50%; }
  .chart-wrap{ position:relative; height:440px; margin-top:18px; }
  .rbox{ display:inline-block; margin-top:14px; padding:6px 14px; border-radius:999px;
         background:#f1f5f9; color:#475569; font-size:12.5px; font-weight:600; }
  svg{ width:100%; height:auto; display:block; margin-top:10px; }
  .foot{ font-size:11.5px; color:#aeb4bd; line-height:1.7; text-align:center; margin-top:14px; }
  .foot b{ color:#8a8f98; }
</style>
</head>
<body>
<div class="wrap">

  <section>
    <div class="eyebrow">26 상반기 뷰티 · 조회수 vs 올리브영</div>
    <h2>① 조회수 대박과 올리브영 랭킹은 따로 논다</h2>
    <div class="sub">가로 = 조회수 TOP100 점유 콘텐츠 수(바이럴 파워) · 세로 = 올리브영 일간 TOP100 유지일수(매출 지표)<br>
      우상향 추세가 없다 — 바이럴 강자(오른쪽)는 바닥에 깔리고, 올리브영 강자(위쪽)는 왼쪽에 몰린다</div>
    <div class="legend">
      <div class="it"><span class="sw" style="background:#4f7cb3"></span>YouTube</div>
      <div class="it"><span class="sw" style="background:#e06a8a"></span>Instagram</div>
    </div>
    <div class="chart-wrap"><canvas id="scatter"></canvas></div>
    <div style="text-align:center"><span class="rbox">상관계수(Spearman) ≈ YouTube 0.02 · Instagram 0.13 → 사실상 무상관</span></div>
  </section>

  <section>
    <div class="eyebrow">두 개의 리그</div>
    <h2>② 조회수 바이럴 TOP10 → 올리브영에선 어디에?</h2>
    <div class="sub">왼쪽 = 26 상반기 조회수 바이럴 TOP10 브랜드 · 오른쪽 = 그 브랜드의 올리브영 유지일수 순위(540개 중)<br>
      대부분의 선이 바닥(순위 밖)으로 추락한다 — 조회수 1등이 매출 1등은 아니다</div>
    <svg id="slope" viewBox="0 0 780 470"></svg>
    <div class="foot"><b>유지일수</b> = 제품이 올리브영 일간 TOP100(전체 카테고리)에 머문 날 수 합 ·
      바이럴 = 조회수 TOP100 영상/게시물 중 점유 개수(YT+IG 합산)</div>
  </section>

</div>

<script>
  const D = __DATA__;
  Chart.register(ChartDataLabels);

  /* ── ① 산점도 ── */
  const LABELS = new Set(['메디힐','아누아','토리든','에스트라','어노브','페리페라',
                          '로레알파리','CJ웰케어','LG생활건강','스킨1004','입생로랑 뷰티','키엘','니베아']);
  const mk = ch => D.pts.filter(p=>p.ch===ch).map(p=>({x:p.x, y:p.y, b:p.b}));
  const dlCfg = {
    display:(c)=>LABELS.has(c.dataset.data[c.dataIndex].b),
    formatter:(v)=>v.b, align:'right', anchor:'end', offset:4,
    font:{size:11, weight:'600'}, color:'#52606d', clamp:true
  };

  new Chart(document.getElementById('scatter'), {
    type:'scatter',
    data:{ datasets:[
      { label:'YouTube', data:mk('YT'), backgroundColor:'rgba(79,124,179,.62)',
        pointRadius:6, pointHoverRadius:8, datalabels:dlCfg },
      { label:'Instagram', data:mk('IG'), backgroundColor:'rgba(224,106,138,.62)',
        pointRadius:6, pointHoverRadius:8, datalabels:dlCfg },
    ]},
    options:{
      responsive:true, maintainAspectRatio:false,
      layout:{padding:{top:10, right:20}},
      scales:{
        x:{ title:{display:true, text:'조회수 TOP100 점유 콘텐츠 수  →  바이럴', font:{size:12}, color:'#9aa1ab'},
            min:0, grid:{color:'#f3f4f6'}, border:{display:false}, ticks:{color:'#aeb4bd', stepSize:1} },
        y:{ title:{display:true, text:'올리브영 TOP100 유지일수  →  매출 지표', font:{size:12}, color:'#9aa1ab'},
            min:0, grid:{color:'#f3f4f6'}, border:{display:false}, ticks:{color:'#aeb4bd'} },
      },
      plugins:{
        legend:{display:false},
        tooltip:{callbacks:{label:(c)=>`${c.raw.b} · 바이럴 ${c.raw.x} / OY유지 ${c.raw.y}일`}},
      }
    }
  });

  /* ── ② 슬로프그래프 (SVG) ── */
  const SVGNS='http://www.w3.org/2000/svg';
  const svg=document.getElementById('slope');
  const add=(t,a)=>{const e=document.createElementNS(SVGNS,t); for(const k in a) e.setAttribute(k,a[k]); return e;};
  const txt=(x,y,s,a={})=>{const e=add('text',Object.assign({x,y},a)); e.textContent=s; svg.appendChild(e); return e;};

  const viral=D.viral.slice(0,10);
  const leftX=300, rightX=560, y0=40, y1=410, maxRank=450;
  const leftY=i=> y0 + i*((y1-y0)/9);
  const rankY=r=> !r ? y1+34 : y0 + Math.min(Math.log(r)/Math.log(maxRank),1)*(y1-y0);

  // 헤더
  txt(leftX,22,'조회수 바이럴 TOP10',{ 'text-anchor':'end','font-size':13,'font-weight':'700','fill':'#334155'});
  txt(rightX,22,'올리브영 순위',{ 'text-anchor':'start','font-size':13,'font-weight':'700','fill':'#334155'});

  // 오른쪽 순위 가이드
  [[1,'1위'],[10,'10위'],[50,'50위'],[200,'200위']].forEach(([r,lab])=>{
    const y=rankY(r);
    svg.appendChild(add('line',{x1:rightX,y1:y,x2:rightX+150,y2:y,stroke:'#eef0f3','stroke-width':1}));
    txt(rightX+150,y+4,lab,{'text-anchor':'end','font-size':10.5,'fill':'#c2c7cf'});
  });
  txt(rightX+150,rankY(null)+4,'순위 밖',{'text-anchor':'end','font-size':10.5,'fill':'#e08a8a','font-weight':'700'});
  svg.appendChild(add('line',{x1:rightX,y1:rankY(null),x2:rightX+150,y2:rankY(null),stroke:'#fae0e0','stroke-width':1,'stroke-dasharray':'3 3'}));

  viral.forEach((v,i)=>{
    const ly=leftY(i), ry=rankY(v.oy_rank);
    const col = v.yt>v.ig ? '#4f7cb3' : v.ig>v.yt ? '#e06a8a' : '#8a6fc0';
    // 연결선
    svg.appendChild(add('line',{x1:leftX,y1:ly,x2:rightX,y2:ry,stroke:col,'stroke-width':2.4,'stroke-opacity':.75,'stroke-linecap':'round'}));
    // 노드
    svg.appendChild(add('circle',{cx:leftX,cy:ly,r:4.5,fill:col}));
    svg.appendChild(add('circle',{cx:rightX,cy:ry,r:4.5,fill:col}));
    // 왼쪽 라벨
    txt(leftX-12,ly-3,`${i+1}. ${v.b}`,{'text-anchor':'end','font-size':12.5,'font-weight':'700','fill':'#1f2937'});
    txt(leftX-12,ly+11,`YT${v.yt} · IG${v.ig}`,{'text-anchor':'end','font-size':10,'fill':'#9aa1ab'});
    // 오른쪽 라벨 (순위)
    txt(rightX+12,ry+4,v.oy_rank?`${v.oy_rank}위`:'순위 밖',
        {'text-anchor':'start','font-size':12,'font-weight':'700','fill':v.oy_rank&&v.oy_rank<=20?'#16a34a':'#ef6a6a'});
  });
</script>
</body>
</html>'''

open('조회수_vs_올리브영랭킹.html','w',encoding='utf-8').write(HTML.replace('__DATA__', DATA_JSON))
print('written 조회수_vs_올리브영랭킹.html')
