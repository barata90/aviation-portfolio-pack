# Scenario Simulator — ATFM Delay (Last 24 Months)

Interactively test **what-if**: reduce delays at **Top-N locations** by **X%** and see the impact on total delay.

<div id="sim_ctrls" style="display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin:10px 0;">
  <label>Top-N locations: <input id="nloc" type="range" min="1" max="25" value="10" oninput="nloc_val.textContent=value"></label><span id="nloc_val">10</span>
  <label>Reduction %: <input id="reduct" type="range" min="0" max="50" value="15" oninput="reduct_val.textContent=value+'%'"></label><span id="reduct_val">15%</span>
</div>

<div id="sim_plot" style="height:420px;"></div>
<div id="sim_kpi" style="margin:6px 0 0 2px; font-size:0.95em;"></div>

<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
<script>
function siteRoot(){ const parts=location.pathname.split('/').filter(Boolean); return parts.length?'/'+parts[0]+'/':'/'; }
function bust(u){ const v=Date.now(); return u+(u.includes('?')?'&':'?')+'v='+v; }
function renderScenario(){ const el=document.getElementById('sim_plot'); if(!el) return; fetch(bust(siteRoot()+'assets/scenario_timeseries.json')).then(r=>r.json()).then(data=>{ const months=data.months; const baseline=data.total.slice(); const locs=data.top_locations; function compute(n,pct){ const scale=1-(pct/100); const locset=new Set(locs.slice(0,n)); const perLoc=data.locations; const scen=baseline.map((v,i)=>{ let delta=0; locset.forEach(L=>{ delta+=perLoc[L][i]*(1-scale); }); return v-delta; }); return scen.map(x=>Math.max(0,x)); } function draw(){ const n=+document.getElementById('nloc').value; const pct=+document.getElementById('reduct').value; const scen=compute(n,pct); const fig={data:[{x:months,y:baseline,type:'scatter',mode:'lines',name:'Baseline'},{x:months,y:scen,type:'scatter',mode:'lines',name:`Scenario (Top-${n} @ -${pct}%)`}], layout:{margin:{l:50,r:10,t:10,b:40},xaxis:{title:'Month'},yaxis:{title:'Delay minutes'},height:420}}; Plotly.newPlot('sim_plot',fig.data,fig.layout,{displayModeBar:false,responsive:true}); const bsum=baseline.reduce((a,b)=>a+b,0); const ssum=scen.reduce((a,b)=>a+b,0); const saving=bsum-ssum; document.getElementById('sim_kpi').innerHTML = 'Total savings over 24 months: <b>'+saving.toLocaleString('en-US',{maximumFractionDigits:0})+'</b> minutes'; } draw(); document.getElementById('nloc').oninput=draw; document.getElementById('reduct').oninput=draw; }); }
if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',renderScenario); else renderScenario(); if(window.document$) document$.subscribe(renderScenario);
</script>

> Baseline per location is proportionally allocated — good enough to demonstrate impact without a heavy model.
