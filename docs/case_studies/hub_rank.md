# Hub Ranking — Route Network (PageRank)

This ranking uses **PageRank** on the directed route graph (weighted by `num_routes`) to identify influential hubs.

### Interactive (if JSON available)
<div id="hub_rank" style="height:520px;"></div>

<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
<script>
(function () {
  function siteRoot() {
    var parts = location.pathname.split('/').filter(Boolean);
    return parts.length ? ('/' + parts[0] + '/') : '/';
  }
  function bust(u) {
    var v = Date.now();
    return u + (u.indexOf('?') > -1 ? '&' : '?') + 'v=' + v;
  }

  function render() {
    var url = bust(siteRoot() + 'assets/hub_rank.json');
    fetch(url)
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status + ' ' + url);
        return r.json();
      })
      .then(function (fig) {
        if (!fig || !fig.data) throw new Error('Invalid hub_rank.json');
        Plotly.newPlot('hub_rank', fig.data, fig.layout || {}, {
          displayModeBar: false,
          responsive: true
        });
      })
      .catch(function (err) {
        console.error('[hub-rank] fallback to static PNG:', err);
        // Fallback ke gambar statis yang benar
        document.getElementById('hub_rank').innerHTML =
          '<img src="../assets/network_degree_top20.png" alt="Top-20 Airport Degree" style="max-width:100%;height:auto">';
      });
  }

  if (window.document$ && typeof window.document$.subscribe === 'function') {
    window.document$.subscribe(render);     // dukung MkDocs Material instant loading
  } else if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', render);
  } else {
    render();
  }
})();
</script>

<noscript>
  <img src="../assets/network_degree_top20.png" alt="Top-20 Airport Degree" style="max-width:100%;height:auto">
</noscript>

**Download:** [assets/hub_rank.csv](../assets/hub_rank.csv)
