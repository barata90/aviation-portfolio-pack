# Route Flow — Top OD Pairs (Sankey)

<div id="sankey" style="height:520px;"></div>
<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
<script>

function siteRoot(){
  const parts = location.pathname.split('/').filter(Boolean);
  return parts.length ? '/' + parts[0] + '/' : '/';
}
function bust(u){
  const v = Date.now(); // cache-buster to avoid stale JSON/CSV
  return u + (u.includes('?') ? '&' : '?') + 'v=' + v;
}

fetch(bust(siteRoot() + 'assets/route_flow_sankey.json'))
  .then(r=>r.json())
  .then(fig=> Plotly.newPlot('sankey', fig.data, fig.layout, {displayModeBar:false, responsive:true}))
  .catch(err=>{ console.error(err); document.getElementById('sankey').innerHTML="<em>Data not available.</em>";});
</script>

> Shows route flows from **Top OD Pairs** (by number of route variants).
