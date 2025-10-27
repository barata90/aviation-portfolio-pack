# Ops Forecast & Incidents — ATFM Delay

This page shows a **trend + seasonal** fit on monthly en-route ATFM delays, flags **anomalies** (|z| ≥ 2.5) and projects a **6-month forecast**. Data: `publish/euro_atfm_timeseries.csv`.

<div id="ops_plot" style="height:520px;"></div>
<div id="ops_tbl"></div>

<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
<script>
function siteRoot(){ const p = location.pathname.split('/').filter(Boolean); return p.length ? '/' + p[0] + '/' : '/'; }
function bust(u){ const v = Date.now(); return u + (u.includes('?') ? '&' : '?') + 'v=' + v; }
function onNav(fn){
  const run = () => setTimeout(fn,0);
  if (window.document$ && typeof window.document$.subscribe === 'function') { window.document$.subscribe(run); }
  else if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', run); }
  else { run(); }
}
function toXY(arr){ const x=[],y=[]; (arr||[]).forEach(p=>{ x.push('t' in p ? new Date(p.t) : (p.label||p.month)); y.push('y' in p ? p.y : p.value); }); return {x,y}; }

function render(){
  const url = bust(siteRoot() + 'assets/ops_forecast.json');
  fetch(url).then(r => { if(!r.ok) throw new Error('HTTP '+r.status+' '+url); return r.json(); }).then(d => {
    const s  = toXY(d.series);
    const ft = toXY(d.fitted);
    const fc = toXY(d.forecast);

    const traces = [
      {x:s.x,  y:s.y,  type:'scatter', mode:'lines+markers', name:'Actual'},
      {x:ft.x, y:ft.y, type:'scatter', mode:'lines',         name:'Trend x Seasonal'},
      {x:fc.x, y:fc.y, type:'scatter', mode:'lines',         name:'Forecast', line:{dash:'dot'}}
    ];

    const an = d.anomalies || [];
    if (an.length){
      const ax = an.map(a => 't' in a ? new Date(a.t) : (a.label||a.month));
      const ay = an.map(a => 'y' in a ? a.y : a.value);
      const txt = an.map(a => 'z' in a ? ('z='+a.z) : '');
      traces.push({x:ax, y:ay, type:'scatter', mode:'markers', name:'Anomaly',
                   marker:{size:10, symbol:'x-thin'}, text:txt,
                   hovertemplate:'%{x|%Y-%m}: %{y:.0f} %{text}<extra></extra>'});
    }

    Plotly.newPlot('ops_plot', traces,
      {margin:{l:50,r:10,t:10,b:40}, xaxis:{title:'Month'}, yaxis:{title:'Delay minutes'}, height:520},
      {displayModeBar:false, responsive:true});

    const tdiv = document.getElementById('ops_tbl');
    if (an.length){
      let html = "<h4>Detected Incidents</h4><table class='dataframe'><thead><tr><th>Month</th><th>Delay</th><th>z</th></tr></thead><tbody>";
      an.sort((a,b)=> (('t' in a?a.t:a.label) < ('t' in b?b.t:b.label) ? -1 : 1)).forEach(a=>{
        const label = 't' in a ? new Date(a.t).toISOString().slice(0,7) : (a.label||a.month);
        const val = ('y' in a ? a.y : a.value);
        html += `<tr><td>${label}</td><td>${Number(val).toLocaleString('en-US')}</td><td>${a.z ?? ''}</td></tr>`;
      });
      html += "</tbody></table>";
      tdiv.innerHTML = html;
    } else {
      tdiv.innerHTML = "<em>No anomalies detected at |z| ≥ 2.5.</em>";
    }
  }).catch(err=>{
    document.getElementById('ops_plot').innerHTML = "<em>Failed to load ops_forecast.json: " + String(err.message || err) + "</em>";
    console.error(err);
  });
}
onNav(render);
</script>

<style>
.dataframe{border-collapse:collapse;width:100%;font-size:0.9rem;margin-top:10px;}
.dataframe th,.dataframe td{border:1px solid #ddd;padding:.35rem .5rem;white-space:nowrap;}
.dataframe thead th{position:sticky;top:0;background:var(--md-default-fg-color--lightest,#f7f7f7);}
</style>
