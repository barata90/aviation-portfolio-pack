# Route Flow — Top OD Pairs (Sankey)

<div id="sankey" style="height:520px;"></div>
<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
<script>

function siteRoot(){
  const parts = location.pathname.split('/').filter(Boolean);
  return parts.length ? '/' + parts[0] + '/' : '/';
}
function bust(u){
  const v = Date.now(); // force fresh fetch on Pages/CDN
  return u + (u.includes('?') ? '&' : '?') + 'v=' + v;
}

function renderSankey(){
  const target = document.getElementById('sankey');
  if (!target) return;
  fetch(bust(siteRoot() + 'assets/route_flow_sankey.json'))
    .then(r=>r.json())
    .then(fig=> Plotly.newPlot('sankey', fig.data, fig.layout, {displayModeBar:false, responsive:true}))
    .catch(err=>{ console.error(err); target.innerHTML="<em>Data not available.</em>";});
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', renderSankey);
else renderSankey();
if (window.document$) document$.subscribe(renderSankey);
</script>

> Shows route flows from **Top OD Pairs** (by number of route variants).
