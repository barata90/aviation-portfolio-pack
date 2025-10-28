# Data Explorer — Publish CSV

Pick a dataset and explore (search / sort / paging).

<select id="sel" style="margin:8px 0; min-width:320px;"></select>
<div id="meta" style="margin:.25rem 0 .5rem 0; font-size:.9rem; opacity:.8;"></div>
<div id="tbl_mount"><table id="tbl" class="display" width="100%"></table></div>

<link rel="stylesheet" href="https://cdn.datatables.net/1.13.8/css/jquery.dataTables.min.css"/>
<link rel="stylesheet" href="https://cdn.datatables.net/scroller/2.4.3/css/scroller.dataTables.min.css"/>
<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
<script src="https://cdn.datatables.net/1.13.8/js/jquery.dataTables.min.js"></script>
<script src="https://cdn.datatables.net/scroller/2.4.3/js/dataTables.scroller.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/papaparse@5.4.1/papaparse.min.js"></script>

<script>
(function(){
  // -------- helpers --------
  function siteRoot(){
    const parts = location.pathname.split('/').filter(Boolean);
    return parts.length ? '/' + parts[0] + '/' : '/';
  }
  function bust(u){
    const v = Date.now();
    return u + (u.includes('?') ? '&' : '?') + 'v=' + v;
  }
  function lastSeg(p){ try { return p.split('/').filter(Boolean).pop() || p; } catch(e){ return p; } }
  function uniqueFields(fields){
    const seen = Object.create(null);
    return fields.map(f => {
      if (seen[f] === undefined){ seen[f] = 0; return f; }
      seen[f] += 1; return f + '_' + seen[f];
    });
  }
  function toArrayData(rows, fields){
    const out = [];
    for (const r of rows){
      // skip empty rows
      if (Object.values(r).every(v => v === null || v === '' || typeof v === 'undefined')) continue;
      out.push(fields.map(f => (r[f] ?? '')));
    }
    return out;
  }

  // -------- datasets.json normalizer --------
  function normalizeDatasets(json){
    // Accept multiple possible shapes; return array of { path, size }
    let arr = [];
    if (Array.isArray(json)) arr = json;
    else if (json && typeof json === 'object'){
      const candidates = [json.datasets, json.publish, json.items, json.files, json.csvs];
      for (const c of candidates){
        if (Array.isArray(c)){ arr = c; break; }
      }
    }
    // Map to unified shape; filter only CSV
    const rows = [];
    for (const d of (arr || [])){
      const raw = d || {};
      const anyPath = raw.file || raw.csv || raw.path || raw.href || '';
      const asStr = String(anyPath || '').trim();
      if (!asStr) continue;
      const isCsv = /\.csv(\?|$)/i.test(asStr);
      if (!isCsv) continue;

      // normalize to publish-relative path
      let path = asStr.replace(/^\.?\/*/, '');  // remove leading ./ or /
      if (path.startsWith('docs/')) path = path.replace(/^docs\//,'');
      if (!path.startsWith('publish/')){
        // If it looks like just a filename, assume under publish/
        if (!path.includes('/')) path = 'publish/' + path;
      }
      const size = Number(raw.size || raw.size_bytes || raw.bytes || 0);
      rows.push({ path, size, name: lastSeg(path) });
    }
    // de-duplicate by path
    const seen = new Set();
    const uniq = [];
    for (const r of rows){
      if (seen.has(r.path)) continue;
      seen.add(r.path);
      uniq.push(r);
    }
    return uniq;
  }

  // -------- UI / loader --------
  let dt = null;

  function loadCsv(relPath){
    const mount = document.getElementById('tbl_mount');
    const meta  = document.getElementById('meta');
    if (!mount) return;

    // Build absolute URL under site root
    let path = relPath.replace(/^\.?\/*/, '');
    if (!path.startsWith('publish/')){
      // safety: default under publish/
      if (!path.includes('/')) path = 'publish/' + path;
    }
    const url = bust(siteRoot() + path);

    // Recreate table node to fully reset DataTables state
    mount.innerHTML = '<table id="tbl" class="display" width="100%"></table>';

    Papa.parse(url, {
      download: true,
      header: true,
      dynamicTyping: false,
      skipEmptyLines: 'greedy',
      complete: (res) => {
        const f0 = res.meta.fields || [];
        if (!f0.length){
          document.getElementById('tbl').outerHTML =
            '<em>CSV has no header/columns. Check the file: '+ path +'</em>';
          meta.textContent = '';
          return;
        }
        const f = uniqueFields(f0);
        const data = toArrayData(res.data || [], f0);
        const cols = f.map(t => ({ title: t }));

        // init DataTables
        dt = $('#tbl').DataTable({
          data, columns: cols, destroy: true,
          processing: true, deferRender: true,
          autoWidth: false, pageLength: 25,
          lengthMenu: [25, 50, 100, 250, 1000],
          scrollX: true,
          scroller: data.length > 1000,
          scrollY: data.length > 1000 ? '60vh' : '',
          orderClasses: false,
          stateSave: true
        });

        // meta
        const nf = (n) => new Intl.NumberFormat('en-US').format(n);
        meta.textContent = `Loaded ${nf(data.length)} rows × ${f.length} columns from ${path}`;
      },
      error: (err) => {
        document.getElementById('tbl').outerHTML =
          '<em>Failed to load CSV: '+ (err && err.message ? err.message : err) +'</em>';
        meta.textContent = '';
        console.error(err);
      }
    });
  }

  function init(){
    const sel = document.getElementById('sel');
    const mount = document.getElementById('tbl_mount');
    if (!sel || !mount) return;

    fetch(bust(siteRoot() + 'assets/datasets.json'))
      .then(r => r.json())
      .then(json => {
        const items = normalizeDatasets(json);
        if (!items.length){
          sel.outerHTML = '<em>publish/ is empty. Add CSVs under <code>publish/</code> and redeploy.</em>';
          return;
        }
        // Populate select
        sel.innerHTML = '';
        for (const it of items){
          const kb = it.size ? `  (${(it.size/1024).toFixed(1)} KB)` : '';
          const opt = document.createElement('option');
          opt.value = it.path;   // full publish/… path
          opt.textContent = `${it.name}${kb}`;
          sel.appendChild(opt);
        }
        const first = sel.value;
        sel.onchange = (e) => loadCsv(e.target.value);
        loadCsv(first);
      })
      .catch(err => {
        sel.outerHTML = '<em>datasets.json not found. Run the site build to regenerate assets.</em>';
        console.error(err);
      });
  }

  if (window.document$ && typeof window.document$.subscribe === 'function'){
    window.document$.subscribe(init);
  } else if (document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
</script>
