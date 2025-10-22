# Ops Forecast & Incidents — ATFM Delay

This page shows a **trend + seasonal** fit on monthly en-route ATFM delays, flags **anomalies** (|z| ≥ 2.5) and projects a **6-month forecast**. Data: `publish/euro_atfm_timeseries.csv`.

<div id="ops_plot" style="height:520px;"></div>
<div id="ops_tbl"></div>

<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
<script>
function siteRoot(){ const p=location.pathname.split('/').filter(Boolean); return p.length?'/'+p[0]+'/':'/'; }
function bust(u){ const v=Date.now(); return u+(u.includes('?')?'&':'?')+'v='+v; }
function onNav(fn){ function run(){ setTimeout(fn,0);} if(window.document$) document$.subscribe(run); if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',run); else run(); }

function render(){
  const url = bust(siteRoot() + 'assets/ops_forecast.json');
  fetch(url).then(r=>r.json()).then(d=>{
    const months = d.months, actual=d.actual, fitted=d.fitted;
    const fvals = d.forecast.values || [];
    const last = months[months.length-1];
    const futureX = [];
    if (months.length){
      const [y,m] = last.split('-').map(Number);
      let yy=y, mm=m;
      for (let i=1;i<=fvals.length;i++){
        mm += 1; if (mm>12){ mm=1; yy+=1; }
        futureX.push(yy + '-' + String(mm).padStart(2,'0'));
      }
    }
    const traces = [
      {x:months, y:actual, type:'scatter', mode:'lines+markers', name:'Actual'},
      {x:months, y:fitted, type:'scatter', mode:'lines', name:'Trend × Seasonal'},
      {x:futureX, y:fvals, type:'scatter', mode:'lines', name:'Forecast', line:{dash:'dot'}}
    ];
    // anomalies
    const ax=[], ay=[], txt=[];
    (d.anomalies||[]).forEach(a=>{ ax.push(a.label); ay.push(a.value); txt.push('z='+a.z);});
    if (ax.length){
      traces.push({x:ax, y:ay, type:'scatter', mode:'markers', name:'Anomaly', marker:{size:10, symbol:'x-thin'}, text:txt, hovertemplate:'%{x}: %{y:.0f} (%{text})<extra></extra>'});
    }
    const layout = {margin:{l:50,r:10,t:10,b:40}, xaxis:{title:'Month'}, yaxis:{title:'Delay minutes'}, height:520};
    Plotly.newPlot('ops_plot', traces, layout, {displayModeBar:false, responsive:true});

    // table of anomalies
    const tdiv = document.getElementById('ops_tbl');
    if ((d.anomalies||[]).length){
      let html = "<h4>Detected Incidents</h4><table class='dataframe'><thead><tr><th>Month</th><th>Delay</th><th>z</th></tr></thead><tbody>";
      d.anomalies.sort((a,b)=> (a.label<b.label?-1:1)).forEach(a=>{
        html += `<tr><td>${a.label}</td><td>${a.value.toLocaleString('en-US')}</td><td>${a.z}</td></tr>`;
      });
      html += "</tbody></table>";
      tdiv.innerHTML = html;
    } else {
      tdiv.innerHTML = "<em>No anomalies detected at |z| ≥ 2.5.</em>";
    }
  }).catch(err=>{
    document.getElementById('ops_plot').innerHTML = "<em>ops_forecast.json not found. Run the site build.</em>";
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
