# SQL Lab — Query `publish/*.csv` with DuckDB-WASM

Run SQL **in your browser** against the portfolio CSVs. Each file under `publish/` is exposed as a **view** named by its file stem (sanitized).

**Examples**

```sql
-- Top airports by connectivity
SELECT iata, deg_total
FROM airport_degree
ORDER BY deg_total DESC
LIMIT 15;

-- Last 24 months ATFM
SELECT period_start, delay_minutes
FROM euro_atfm_timeseries
WHERE period_start >= DATE_trunc('month', CURRENT_DATE) - INTERVAL 23 MONTH
ORDER BY 1;

-- OD pairs where both endpoints are top-50 hubs
WITH hubs AS (
  SELECT iata FROM airport_degree ORDER BY deg_total DESC LIMIT 50
)
SELECT rc.src_iata, rc.dst_iata, rc.num_routes
FROM route_counts rc
WHERE rc.src_iata IN (SELECT iata FROM hubs)
  AND rc.dst_iata IN (SELECT iata FROM hubs)
ORDER BY rc.num_routes DESC
LIMIT 50;
```

<!-- Import maps (normal & shim) agar bare import apache-arrow terselesaikan -->
<script type="importmap">
{
  "imports": {
    "apache-arrow": "https://cdn.jsdelivr.net/npm/apache-arrow@14.0.2/+esm"
  }
}
</script>
<script type="importmap-shim">
{
  "imports": {
    "apache-arrow": "https://cdn.jsdelivr.net/npm/apache-arrow@14.0.2/+esm"
  }
}
</script>

<!-- Loader ESM universal -->
<script src="https://cdn.jsdelivr.net/npm/es-module-shims@1.9.0/dist/es-module-shims.min.js" async crossorigin="anonymous"></script>

<!-- =============== SQL Lab UI =============== -->
<div id="lab" style="margin:.5rem 0; position:relative; z-index:3;">
  <textarea id="sql" style="width:100%;height:160px;font-family:ui-monospace,monospace;">SELECT 42 AS answer;</textarea>
</div>

<p>
  <button id="run" type="button" class="md-button md-button--primary"
          style="padding:.45rem .9rem; cursor:pointer; position:relative; z-index:4;"
          onclick="window.__runSQL__ && window.__runSQL__(event)">
    Run
  </button>
  <span id="status" style="margin-left:.6rem;color:#666;">Idle</span>
</p>

<div id="result" style="margin-top:10px;overflow:auto;"></div>

<script>
(function(){
  const log = (...a)=>console.log('[sql_lab]', ...a);
  const statusEl = ()=>document.getElementById('status');
  const resultEl = ()=>document.getElementById('result');
  const siteRoot = ()=>{ const p=location.pathname.split('/').filter(Boolean); return p.length?'/'+p[0]+'/':'/'; };
  const bust = (u)=>{ const v=Date.now(); return u+(u.includes('?')?'&':'?')+'v='+v; };

  /* >>> FIX: gunakan browser.mjs (bukan ...-eh.mjs) */
  const DUCKDB_MJS = 'https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.29.0/dist/duckdb-browser.mjs';

  let _duckdb=null, _db=null, _conn=null, _views=[];

  function sanitize(name){ return String(name).toLowerCase().replace(/[^a-z0-9_]/g,'_').replace(/^_+/,''); }

  async function makeSameOriginWorker(url){
    try{
      const js = await (await fetch(url, {mode:'cors'})).text();
      const blobUrl = URL.createObjectURL(new Blob([js], {type:'text/javascript'}));
      return new Worker(blobUrl);
    }catch(e){
      log('worker blob fallback -> direct URL', e);
      return new Worker(url);
    }
  }

  async function getConn(){
    if (_conn) return _conn;
    if (typeof importShim !== 'function') throw new Error('Engine belum siap. Coba reload (Ctrl/Cmd+Shift+R).');

    const duckdb = await importShim(DUCKDB_MJS);
    _duckdb = duckdb;

    // >>> FIX: pilih bundle resmi dari jsDelivr
    const bundles = duckdb.getJsDelivrBundles();
    const bundle  = await duckdb.selectBundle(bundles);
    log('bundle selected:', bundle);

    const worker = await makeSameOriginWorker(bundle.mainWorker);
    const logger = new duckdb.ConsoleLogger();
    const db = new duckdb.AsyncDuckDB(logger, worker);

    // >>> FIX: instantiate pakai bundle.mainModule (+ pthreadWorker jika ada)
    await db.instantiate(bundle.mainModule, bundle.pthreadWorker);

    const conn = await db.connect();
    await conn.query('INSTALL httpfs; LOAD httpfs;');

    _db=db; _conn=conn;
    return conn;
  }

  async function registerViews(){
    if (_views.length) return _views;
    let ds;
    try { ds = await (await fetch(bust(siteRoot()+'assets/datasets.json'))).json(); }
    catch(e){ log('datasets.json not found/unreadable:', e); return _views; }

    const items = Array.isArray(ds) ? ds : (ds && Array.isArray(ds.items)) ? ds.items : [];
    for (const it of items){
      const f = it.file || it.path || '';
      if (!/\.csv$/i.test(f)) continue;
      const stem   = sanitize((f.split('/').pop()||'').replace(/\.csv$/i,''));
      const csvUrl = bust(siteRoot()+'publish/'+f);
      await _conn.query(`
        CREATE OR REPLACE VIEW "${stem}"
        AS SELECT * FROM read_csv_auto('${csvUrl}', AUTO_DETECT=TRUE, SAMPLE_SIZE=20000);
      `);
      _views.push({ view: stem, file: f });
    }
    return _views;
  }

  function renderTable(df){
    const mount=resultEl();
    if(!df || !df.rows || df.rows.length===0){ mount.innerHTML='<em>No rows.</em>'; return; }
    const cols=df.schema.fields.map(f=>f.name);
    let html="<table class='dataframe'><thead><tr>"+cols.map(c=>`<th>${c}</th>`).join("")+"</tr></thead><tbody>";
    const cap=5000; let i=0;
    for(const row of df.rows){ if(i++>=cap) break; html+="<tr>"+row.map(v=>`<td>${v==null?'':v}</td>`).join("")+"</tr>"; }
    html+="</tbody></table>";
    if(df.rows.length>cap) html+=`<div style="opacity:.7;font-size:.85rem;margin-top:.35rem;">Showing first ${cap.toLocaleString()} rows</div>`;
    mount.innerHTML=html;
  }
  function showError(err){
    resultEl().innerHTML = `<pre style="color:#b71c1c;white-space:pre-wrap;">${err?.message||String(err)}</pre>`;
  }

  async function runSQL(ev){
    try{
      ev && ev.preventDefault && ev.preventDefault();
      const btn=document.getElementById('run');
      btn.disabled=true; statusEl().textContent='Running…';

      await getConn();
      await registerViews();

      const sql = document.getElementById('sql').value;
      const res = await _conn.query(sql);
      renderTable(res);
      statusEl().textContent='Done';
    }catch(err){
      console.error('[sql_lab] run error:', err);
      statusEl().textContent='Error';
      showError(err);
    }finally{
      const btn=document.getElementById('run'); if(btn) btn.disabled=false;
    }
  }

  window.__runSQL__ = runSQL;

  document.addEventListener('DOMContentLoaded', ()=>{
    const q = document.getElementById('sql');
    if (q && !q.value.trim()){
      q.value = `SELECT month, delay_min
FROM read_json_auto('${siteRoot()}api/euro_atfm_timeseries_last24.json')
ORDER BY month DESC
LIMIT 5;`;
    }
  });
})();
</script>

<style>
#lab { position: relative; z-index: 3; }
#run { pointer-events: auto; }
.dataframe{border-collapse:collapse;width:100%;font-size:0.9rem;}
.dataframe th,.dataframe td{border:1px solid #ddd;padding:.35rem .5rem;white-space:nowrap;}
.dataframe thead th{position:sticky;top:0;background:var(--md-default-fg-color--lightest,#f7f7f7);}
</style>
