# Visual Insights — Executive Demo

> Halaman ini menampilkan highlight visual yang langsung “bicara” ke use case Emirates.

## Ops Delay — 24 Bulan (Anomali & Moving Average)
![ATFM 24m](../assets/ops_delay_24m_advanced.png)

### Interaktif (zoom/hover)
<div id="ops_plot" style="height:420px;"></div>
<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
<script>
fetch('../assets/ops_delay_plotly.json')
  .then(r => r.json())
  .then(fig => Plotly.newPlot('ops_plot', fig.data, fig.layout, {displayModeBar:false, responsive:true}));
</script>

## KPI Ringkas
<script>
fetch('../assets/ops_delay_kpis.json').then(r=>r.json()).then(k=>{
  const div = document.createElement('div');
  div.className='kpi-grid';
  const fmt = n => (n==null)?'—':Intl.NumberFormat('en-US',{maximumFractionDigits:0}).format(n);
  const pct = n => (n==null)?'—':(n>=0?'+':'')+n.toFixed(1)+'%';
  div.innerHTML = `
    <div class="kpi"><div class="kpi-label">Last Month</div><div class="kpi-value">${fmt(k.last_month)}</div><div class="kpi-sub">${k.last_month_label||''}</div></div>
    <div class="kpi"><div class="kpi-label">12M Rolling</div><div class="kpi-value">${fmt(k.rolling_12m)}</div></div>
    <div class="kpi"><div class="kpi-label">YoY %</div><div class="kpi-value">${pct(k.yoy_pct)}</div></div>
  `;
  document.currentScript.after(div);
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
