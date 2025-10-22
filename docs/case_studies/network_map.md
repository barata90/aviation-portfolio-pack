# Network Map — Airport Connectivity (Leaflet)

<div id="map" style="height:520px; min-height:520px; width:100%; border-radius:8px; overflow:hidden;"></div>

<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

<script>
function siteRoot(){
  const parts = location.pathname.split('/').filter(Boolean);
  return parts.length ? '/' + parts[0] + '/' : '/';
}
const map = L.map('map').setView([25.25, 55.3], 3);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 8, attribution: '&copy; OpenStreetMap'
}).addTo(map);
setTimeout(()=>map.invalidateSize(), 150);

fetch(siteRoot() + 'assets/airports.geojson')
  .then(r => r.json())
  .then(geo => {
    const layer = L.geoJSON(geo, {
      pointToLayer: (feat, latlng) => {
        const deg = (+feat.properties.deg_total) || 0;
        const r = Math.max(3, Math.sqrt(deg));
        return L.circleMarker(latlng, {
          radius: r, weight: 1, color: '#1565c0', fillColor: '#42a5f5', fillOpacity: 0.6
        });
      },
      onEachFeature: (feat, l) => {
        const p = feat.properties || {};
        l.bindPopup(`<b>${p.iata || ''} — ${p.name || ''}</b><br/>
          ${p.city || ''}, ${p.country || ''}<br/>
          deg_total: <b>${p.deg_total || 0}</b>`);
      }
    }).addTo(map);
    map.fitBounds(layer.getBounds(), {padding:[20,20]});
  })
  .catch(err => { console.error(err); document.getElementById('map').innerHTML = "<em>Data not available.</em>"; });
</script>

> Bubble size merepresentasikan **deg_total** (konektivitas). Klik marker untuk detail bandara.
