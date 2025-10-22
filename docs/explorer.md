# Data Explorer — Publish CSV

Pilih dataset dan jelajahi langsung (search/sort/paging).

<select id="sel" style="margin:8px 0;"></select>
<table id="tbl" class="display" width="100%"></table>

<link rel="stylesheet" href="https://cdn.datatables.net/1.13.8/css/jquery.dataTables.min.css"/>
<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
<script src="https://cdn.datatables.net/1.13.8/js/jquery.dataTables.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/papaparse@5.4.1/papaparse.min.js"></script>

<script>
function siteRoot(){
  const parts = location.pathname.split('/').filter(Boolean);
  return parts.length ? '/' + parts[0] + '/' : '/';
}
const datasetsUrl = siteRoot() + 'assets/datasets.json';
const publishBase = siteRoot() + 'publish/';

fetch(datasetsUrl).then(r=>r.json()).then(list=>{
  const sel = document.getElementById('sel');
  if (!list.length) { sel.outerHTML = "<em>publish/ kosong.</em>"; return; }
  list.forEach(d => {
    const opt = document.createElement('option');
    opt.value = d.file; opt.textContent = `${d.file}  (${(d.size/1024).toFixed(1)} KB)`;
    sel.appendChild(opt);
  });
  const load = (fname)=>{
    if ($.fn.DataTable.isDataTable('#tbl')) $('#tbl').DataTable().clear().destroy();
    const url = publishBase + fname;
    Papa.parse(url, {download:true, header:true, dynamicTyping:true, complete:(res)=>{
      const cols = res.meta.fields.map(c=>({title:c, data:c}));
      $('#tbl').DataTable({data:res.data, columns:cols, pageLength:25, deferRender:true, scrollX:true});
    }});
  };
  sel.addEventListener('change', e => load(e.target.value));
  load(sel.value);
});
</script>
