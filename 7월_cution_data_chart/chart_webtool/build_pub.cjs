const fs = require('fs');
const { months, series } = JSON.parse(fs.readFileSync('/tmp/pubmonthly.json', 'utf8'));
const xlabels = months.map(m => m.slice(5) + '월');
const EMPH = {
  '클리오 킬커버 파운웨어': { color: '#2a78d6', w: 4.2, tag: '자사' },
  '정샘물 스킨누더':      { color: '#1f8a4c', w: 3.2, tag: '강자' },
  '루나 롱래스팅컨실':     { color: '#eb6834', w: 3.0, tag: '발행최다' },
};
const seriesCfg = Object.keys(series).map(name => {
  const e = EMPH[name]; const em = !!e;
  return {
    name, type: 'line', data: series[name], smooth: false,
    showSymbol: true, symbolSize: em ? 8 : 5,
    lineStyle: { width: em ? e.w : 1.3, color: em ? e.color : '#d6d5cf' },
    itemStyle: { color: em ? e.color : '#d6d5cf' },
    z: em ? 10 : 1,
    label: em ? { show: true, position: 'top', color: e.color, fontWeight: 700, fontSize: 11 } : { show: false },
    endLabel: em ? { show: true, distance: 6, formatter: name.split(' ')[0] + ' · ' + e.tag, color: e.color, fontWeight: 700, fontSize: 12 } : { show: false },
    labelLayout: em ? { moveOverlap: 'shiftY', hideOverlap: false } : undefined,
    emphasis: { focus: 'series' },
  };
});
const html = `<!doctype html><html lang="ko"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>인사이트 · 월별 발행량 (3~6월)</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.1/dist/echarts.min.js"></script>
<style>
:root{--ink:#0b0b0b;--ink2:#52514e;--muted:#9a9992;--accent:#2a78d6}
*{box-sizing:border-box}
body{margin:0;background:#f4f4f2;font-family:"Pretendard",system-ui,-apple-system,"Apple SD Gothic Neo","Segoe UI",sans-serif;color:var(--ink)}
.card{max-width:1080px;margin:30px auto;background:#fff;border-radius:18px;box-shadow:0 4px 24px rgba(0,0,0,.06);padding:32px 40px 26px}
.eyebrow{font-size:12px;font-weight:700;letter-spacing:.12em;color:var(--accent);text-transform:uppercase;margin-bottom:6px}
h1{font-size:23px;font-weight:800;margin:0 0 4px}
.lead{font-size:14px;color:var(--ink2);line-height:1.55;margin:0 0 8px}
.legend{display:flex;gap:16px;flex-wrap:wrap;margin:8px 0 4px;font-size:12.5px;color:var(--ink2)}
.lg{display:flex;gap:6px;align-items:center}.bar{width:20px;height:4px;border-radius:2px}
.chart{width:100%;height:480px}
.foot{font-size:12px;color:var(--muted);line-height:1.5;border-top:1px solid #e1e0d9;padding-top:12px;margin-top:6px}
.take{background:#f7faff;border:1px solid #e3edfb;border-radius:12px;padding:14px 16px;margin-top:14px;font-size:13.5px;line-height:1.65;color:#1f2d3d}
.take b{color:var(--accent)}
</style></head><body>
<div class="card">
  <div class="eyebrow">INSIGHT · 월별 발행량 (2026 3~6월)</div>
  <h1>발행량을 &lsquo;가장 많이&rsquo; 쏟은 제품은 오히려 하위권</h1>
  <p class="lead">제품 언급 컨텐츠(유튜브 영상+인스타 게시물, 중복 제거)의 <b>월별 발행 건수</b>(2026-03~06). 위로 갈수록 많이 발행. 클리오(자사)·정샘물(강자)·루나(발행최다)만 강조.</p>
  <div class="legend">
    <span class="lg"><span class="bar" style="background:#2a78d6"></span>클리오(자사)</span>
    <span class="lg"><span class="bar" style="background:#1f8a4c"></span>정샘물(강자)</span>
    <span class="lg"><span class="bar" style="background:#eb6834"></span>루나(발행최다)</span>
    <span class="lg"><span class="bar" style="background:#d6d5cf"></span>기타</span>
  </div>
  <div id="chart" class="chart"></div>
  <div class="take">
    <b>해석:</b> 월별로 봐도 발행량 최상위는 <b>루나(6월 113건)·바닐라코(5월 98건)·라네즈(4월 106건)</b> 등 &lsquo;반짝·약세&rsquo; 제품이고, 강자인 <b>클리오·정샘물은 월 20~46건 수준으로 꾸준하지만 적다.</b> 특히 클리오는 6월 12건까지 줄었다. 발행 물량과 랭킹 상위가 비례하지 않는 패턴이 월별에서도 유지된다.
  </div>
  <p class="foot">발행량 = 해당 월 제품 언급 고유 유튜브 영상+인스타 게시물 수. 기간 2026-03~06(인스타 집계 시작 구간). 데이터: 유튜브·인스타.</p>
</div>
<script>
const ch=echarts.init(document.getElementById('chart'),null,{devicePixelRatio:3});
ch.setOption({
  backgroundColor:'transparent',textStyle:{fontFamily:'Pretendard,system-ui,sans-serif'},
  grid:{left:56,right:128,top:24,bottom:40},
  tooltip:{trigger:'axis',order:'valueDesc',valueFormatter:v=>v==null?'-':v+'건'},
  xAxis:{type:'category',data:${JSON.stringify(xlabels)},boundaryGap:false,axisLine:{lineStyle:{color:'#c3c2b7'}},axisTick:{show:false},axisLabel:{color:'#52514e',fontSize:13}},
  yAxis:{type:'value',min:0,name:'월 발행 건수',nameTextStyle:{color:'#898781',fontSize:11},splitLine:{lineStyle:{color:'#ecebe6'}},axisLabel:{color:'#898781'}},
  series:${JSON.stringify(seriesCfg)}
});
</script></body></html>`;
fs.writeFileSync('insight_05_pubmonthly.html', html);
console.log('저장: insight_05_pubmonthly.html');
