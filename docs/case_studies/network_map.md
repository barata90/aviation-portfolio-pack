# Network Map — Airport Connectivity (Leaflet)

<div id="map" style="height:520px; min-height:520px; width:100%; border-radius:8px; overflow:hidden;"></div>

<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

<script>
(function(){
  function siteRoot(){
  const parts = location.pathname.split('/').filter(Boolean);
  return parts.length ? '/' + parts[0] + '/' : '/';
}
function bust(u){
  const v = Date.now(); // avoid stale JSON/CSV on Pages/CDN
  return u + (u.includes('?') ? '&' : '?') + 'v=' + v;
}
  function onNav(fn){ function run(){ setTimeout(fn,0);} if(window.document$) document$.subscribe(run); if(document.readyState==='loading') document.addEventListener('DOMContentLoaded', run); else run(); }
  function visible(el){ if(!el) return false; const r=el.getBoundingClientRect(); return r.width>0 && r.height>0; }
  function render(){
    const mount=document.getElementById('map'); if(!mount) return;
    if(!visible(mount)) { setTimeout(render,120); return; }
    if(typeof L==='undefined'){ setTimeout(render,80); return; }
    if(window._leaflet_map){ try{ window._leaflet_map.remove(); }catch(e){} }
    const map = window._leaflet_map = L.map('map',{preferCanvas:true});
    map.setView([25.25,55.30],3);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:8, attribution:'&copy; OpenStreetMap'}).addTo(map);
    [150,500,1000].forEach(ms=>setTimeout(()=>map.invalidateSize(), ms)); window.addEventListener('resize',()=>map.invalidateSize());
    fetch(bust(siteRoot()+'assets/airports.geojson'))
      .then(r=>{ if(!r.ok) throw new Error('HTTP '+r.status); return r.json(); })
      .then(geo=>{
        if(!geo.features || !geo.features.length){ L.marker([25.252,55.364]).addTo(map).bindPopup('airports.geojson is empty.'); return; }
        const layer=L.geoJSON(geo,{
          pointToLayer:(f,latlng)=>{ const deg=(+f.properties.deg_total)||0; const rad=Math.max(3,Math.sqrt(deg)); return L.circleMarker(latlng,{radius:rad,weight:1,color:'#1565c0',fillColor:'#42a5f5',fillOpacity:0.6}); },
          onEachFeature:(f,l)=>{ const p=f.properties||{}; l.bindPopup(`<b>${p.iata||''} — ${p.name||''}</b><br/>${p.city||''}, ${p.country||''}<br/>deg_total: <b>${p.deg_total||0}</b>`); }
        }).addTo(map);
        try{ map.fitBounds(layer.getBounds(),{padding:[20,20]}); }catch(e){}
      })
      .catch(err=>{ console.error('airports.geojson error:',err); L.marker([25.252,55.364]).addTo(map).bindPopup('airports.geojson not found.'); });
  }
  onNav(render);
})();
</script>

> Bubble size represents **deg_total** (connectivity). Click a marker for airport details.
