# Visual Insights — Executive Demo

> Halaman ini menampilkan highlight visual yang langsung “bicara” ke use case Emirates.

## Ops Delay — 24 Bulan (Anomali & Moving Average)
![ATFM 24m](../assets/ops_delay_24m_advanced.png)

### Interaktif (zoom/hover)
<div id="ops_plot" style="height:420px;"></div>
<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
<script>
/* Resolve base path for GitHub Pages project (e.g. /aviation-portfolio-pack/) or root (/) */
function siteRoot(){
  const parts = location.pathname.split('/').filter(Boolean);
  // project pages: [/REPO/...]; user/Custom domain: []
  return parts.length ? '/' + parts[0] + '/' : '/';
}
function loadJSON(name){ return fetch(siteRoot() + 'assets/' + name).then(r => r.json()); }

/* Draw interactive chart */
loadJSON('ops_delay_plotly.json')
  .then(fig => Plotly.newPlot('ops_plot', fig.data, fig.layout, {displayModeBar:false, responsive:true}))
  .catch(err => {
    const d = document.getElementById('ops_plot');
    d.innerHTML = "<em>Interactive plot failed to load.</em>";
    console.error(err);
  });
</script>

## KPI Ringkas
<div id="kpi_mount"></div>
<script>
loadJSON('ops_delay_kpis.json').then(k=>{
  const root = document.getElementById('kpi_mount');
  const fmt = n => (n==null)?'—':Intl.NumberFormat('en-US',{maximumFractionDigits:0}).format(n);
  const pct = n => (n==null)?'—':(n>=0?'+':'')+n.toFixed(1)+'%';
  root.innerHTML = `
    <div class="kpi-grid">
      <div class="kpi"><div class="kpi-label">Last Month</div><div class="kpi-value">${fmt(k.last_month)}</div><div class="kpi-sub">${k.last_month_label||''}</div></div>
      <div class="kpi"><div class="kpi-label">12M Rolling</div><div class="kpi-value">${fmt(k.rolling_12m)}</div></div>
      <div class="kpi"><div class="kpi-label">YoY %</div><div class="kpi-value">${pct(k.yoy_pct)}</div></div>
    </div>
  `;
});
</script>

## Top Locations (Mini Panels)
![Top-12 panels](../assets/ops_delay_top_locations_smallmultiples.png)

## Network Strength — Top-20 Airport Degree
![Top-20 degree](../assets/network_degree_top20.png)

---

### Navigasi dataset
- [Euro ATFM Timeseries](../pages/euro_atfm_timeseries.md) · [By Location](../pages/euro_atfm_by_location.md)  
- [Airport Degree](../pages/airport_degree.md) · [Top OD Pairs](../pages/top_od_pairs.md)
