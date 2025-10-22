# Hub Ranking — Route Network (PageRank)

This ranking uses **PageRank** on the directed route graph (weighted by `num_routes`) to identify influential hubs.

<div id="hub_rank" style="height:520px;"></div>
<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
<script>
function siteRoot(){ const parts=location.pathname.split('/').filter(Boolean); return parts.length?'/'+parts[0]+'/':'/'; }
function bust(u){ const v=Date.now(); return u+(u.includes('?')?'&':'?')+'v='+v; }
function renderHub(){ fetch(bust(siteRoot()+'assets/hub_rank.json')).then(r=>r.json()).then(fig=>{ Plotly.newPlot('hub_rank', fig.data, fig.layout, {displayModeBar:false, responsive:true}); }).catch(err=>{ console.error(err); document.getElementById('hub_rank').innerHTML='<em>Figure not available.</em>'; }); }
if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',renderHub); else renderHub(); if(window.document$) document$.subscribe(renderHub);
</script>

Download: [`assets/hub_rank.csv`](../assets/hub_rank.csv)
