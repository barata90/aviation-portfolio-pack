# Data Explorer — Publish CSV

Pick a dataset and explore (search / sort / paging).

<select id="sel" style="margin:8px 0;"></select>
<div id="tbl_mount"><table id="tbl" class="display" width="100%"></table></div>

<link rel="stylesheet" href="https://cdn.datatables.net/1.13.8/css/jquery.dataTables.min.css"/>
<link rel="stylesheet" href="https://cdn.datatables.net/scroller/2.4.3/css/scroller.dataTables.min.css"/>
<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
<script src="https://cdn.datatables.net/1.13.8/js/jquery.dataTables.min.js"></script>
<script src="https://cdn.datatables.net/scroller/2.4.3/js/dataTables.scroller.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/papaparse@5.4.1/papaparse.min.js"></script>

<script>
function siteRoot(){
  const parts = location.pathname.split('/').filter(Boolean);
  return parts.length ? '/' + parts[0] + '/' : '/';
}
function bust(u){
  const v = Date.now(); // avoid stale JSON/CSV on GitHub Pages/CDN
  return u + (u.includes('?') ? '&' : '?') + 'v=' + v;
}

function toArrayData(rows, fields){
  const out = [];
  for (const r of rows){
    if (Object.values(r).every(v => v === null || v === "" || typeof v === "undefined")) continue;
    out.push(fields.map(f => (r[f] ?? "")));
  }
  return out;
}
function uniqueFields(fields){
  const seen = {};
  return fields.map(f => (f in seen ? (seen[f]++, f + "_" + seen[f]) : (seen[f]=0, f)));
}

function initExplorer(){
  const sel = document.getElementById('sel');
  const mount = document.getElementById('tbl_mount');
  if (!sel || !mount) return;

  fetch(bust(siteRoot() + 'assets/datasets.json')).then(r=>r.json()).then(list=>{
    sel.innerHTML = '';
    if (!list.length){ sel.outerHTML="<em>publish/ is empty.</em>"; return; }
    for (const d of list){
      const opt = document.createElement('option');
      opt.value = d.file; opt.textContent = `${d.file}  (${(d.size/1024).toFixed(1)} KB)`;
      sel.appendChild(opt);
    }
    const load = (fname)=>{
      mount.innerHTML = '<table id="tbl" class="display" width="100%"></table>';
      const url = bust(siteRoot() + 'publish/' + fname);
      Papa.parse(url, {
        download: true, header: true, dynamicTyping: false, skipEmptyLines: "greedy",
        complete: (res) => {
          const fields0 = res.meta.fields || [];
          const fields  = uniqueFields(fields0);
          const data    = toArrayData(res.data, fields0);
          const columns = fields.map(t => ({ title: t }));
          $('#tbl').DataTable({
            data, columns, destroy: true, processing: true, deferRender: true, autoWidth: false,
            pageLength: 25, lengthMenu: [25,50,100,250,1000],
            scrollX: true,
            scroller: data.length > 1000,
            scrollY: data.length > 1000 ? '60vh' : '',
            orderClasses: false, stateSave: true
          });
        },
        error: (err) => { mount.innerHTML = '<em>Failed to load CSV: ' + err.message + '</em>'; console.error(err); }
      });
    };
    sel.onchange = e => load(e.target.value);
    load(sel.value);
  });
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initExplorer);
else initExplorer();
if (window.document$) document$.subscribe(initExplorer);
</script>
