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

<!-- --- DuckDB SQL Lab: robust, Arrow-aware, IDB-safe --- -->
<div id="lab" style="margin:.5rem 0; position:relative; z-index:3;">
  <textarea id="sql" style="width:100%;height:160px;font-family:ui-monospace,monospace;">SELECT 42 AS answer;</textarea>
</div>

<p>
  <button id="run"
          type="button"
          class="md-button md-button--primary"
          style="padding:.45rem .9rem; cursor:pointer;"
          onclick="window.__runSQL__ && window.__runSQL__(event)">
    Run
  </button>
  <span id="status" style="margin-left:.6rem;color:#666;">Idle</span>
</p>

<div id="result" style="margin-top:10px;overflow:auto;"></div>

<!-- Import map agar 'apache-arrow' bisa di-resolve oleh duckdb-browser.mjs -->
<script type="importmap">
{
  "imports": {
    "apache-arrow": "https://cdn.jsdelivr.net/npm/apache-arrow@14.0.2/+esm"
  }
}
</script>

<script type="module">
/* =============== helpers =============== */
const log=(...a)=>console.log('[sql_lab]',...a);
function siteRoot(){ const p=location.pathname.split('/').filter(Boolean); return p.length?'/'+p[0]+'/':'/'; }
function bust(u){ const v=Date.now(); return u+(u.includes('?')?'&':'?')+'v='+v; }
function onNav(fn){ const run=()=>setTimeout(fn,0); if(window.document$&&typeof document$.subscribe==='function') document$.subscribe(run); if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',run); else run(); }

/* =============== state =============== */
const state={ duckdb:null, db:null, conn:null, views:[] };

/* =============== probes (SAB & IndexedDB) =============== */
const supportsSAB = !!self.SharedArrayBuffer && self.crossOriginIsolated===true;
function probeIndexedDB(){
  return new Promise((resolve)=>{
    try{
      const req=indexedDB.open('duckdb_probe'); req.onsuccess=()=>{ try{req.result.close(); indexedDB.deleteDatabase('duckdb_probe');}catch{} resolve(true); };
      req.onerror=()=>resolve(false); req.onblocked=()=>resolve(false);
    }catch{ resolve(false); }
  });
}

/* =============== load DuckDB (bundle resmi + worker blob) =============== */
async function ensureDB(){
  if(state.conn) return state.conn;

  const idbOK = await probeIndexedDB();
  if(!idbOK){ // hindari throw “operation is insecure”
    try{ Object.defineProperty(globalThis,'indexedDB',{value:undefined,writable:true,configurable:true}); }catch{}
  }

  // Import ESM utama; fallback ke unpkg jika jsDelivr bermasalah
  let duckdb;
  try{
    duckdb = await import('https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.29.0/dist/duckdb-browser.mjs');
  }catch{
    duckdb = await import('https://unpkg.com/@duckdb/duckdb-wasm@1.29.0/dist/duckdb-browser.mjs');
  }
  state.duckdb = duckdb;

  // Ambil daftar bundle (OBJECT, bukan array) lalu pilih
  const bundles = duckdb.getJsDelivrBundles ? duckdb.getJsDelivrBundles() : duckdb.getCdnBundles();
  if(!bundles) throw new Error('Unable to load bundle list');

  let chosen = await duckdb.selectBundle(bundles);
  // Jika bundle threaded dipilih tapi SAB/IDB tidak aman → pakai MVP
  if (chosen?.pthreadWorker && (!supportsSAB || !idbOK)) chosen = bundles.mvp || chosen;

  if (!chosen?.mainWorker || !chosen?.mainModule) {
    chosen = bundles.mvp || bundles.eh || chosen;
    if (!chosen?.mainWorker || !chosen?.mainModule) throw new Error('No suitable DuckDB bundle found');
  }

  // Worker via blob+importScripts — pola yang direkomendasikan dokumentasi
  const workerSource = `importScripts("${chosen.mainWorker}");`;
  const workerUrl = URL.createObjectURL(new Blob([workerSource], { type: "text/javascript" }));
  const worker = new Worker(workerUrl);
  const logger = new duckdb.ConsoleLogger();
  const db = new duckdb.AsyncDuckDB(logger, worker);

  await db.instantiate(chosen.mainModule, chosen.pthreadWorker);
  const conn = await db.connect();
  await conn.query('INSTALL httpfs; LOAD httpfs;');

  state.db=db; state.conn=conn;
  return conn;
}

/* =============== daftar view CSV dari assets/datasets.json =============== */
function sanitize(s){ return String(s).toLowerCase().replace(/[^a-z0-9_]/g,'_').replace(/^_+/, ''); }
async function registerViews(){
  if(state.views.length) return state.views;
  let ds;
  try{ ds = await (await fetch(bust(siteRoot()+'assets/datasets.json'))).json(); }
  catch(e){ log('datasets.json not available:', e); return state.views; }

  const items = Array.isArray(ds) ? ds : (ds && Array.isArray(ds.items)) ? ds.items : [];
  for(const it of items){
    const f = it.file || it.path || '';
    if(!/\.csv$/i.test(f)) continue;
    const stem = sanitize((f.split('/').pop()||'').replace(/\.csv$/i,''));
    const csvUrl = bust(siteRoot()+'publish/'+f);
    await state.conn.query(`
      CREATE OR REPLACE VIEW "${stem}"
      AS SELECT * FROM read_csv_auto('${csvUrl}', AUTO_DETECT=TRUE, SAMPLE_SIZE=20000);
    `);
    state.views.push({view:stem,file:f});
  }
  return state.views;
}

/* =============== renderer (Arrow-first, fallback array) =============== */
function renderTable(result){
  const mount=document.getElementById('result');

  // Arrow Table: bisa diiterasi langsung 'for (const row of result)'
  let headers = [];
  if (Array.isArray(result?.schema?.fields)) headers = result.schema.fields.map(f=>f.name);

  const rows = [];
  if (result && typeof result[Symbol.iterator] === 'function') {
    // Arrow Table iterator → StructRowProxy
    for (const row of result) {
      const obj = {};
      if (headers.length === 0) headers = Object.keys(row);
      for (const k of headers) obj[k] = row[k];
      rows.push(obj);
    }
  } else if (typeof result?.toArray === 'function') {
    const arr = result.toArray();
    if (arr.length && !Array.isArray(arr[0])) {
      rows.push(...arr); // array of objects
      if (headers.length===0 && rows.length) headers = Object.keys(rows[0]);
    }
  } else if (Array.isArray(result?.rows)) {
    // Bentuk lama: rows = [[...]]
    if (headers.length===0 && result?.schema?.fields) headers = result.schema.fields.map(f=>f.name);
    for (const r of result.rows){
      const obj={}; (headers.length?headers:r.map((_,i)=>'col_'+(i+1))).forEach((c,i)=>obj[c]=r[i]);
      rows.push(obj);
    }
  }

  if (!rows.length){ mount.innerHTML='<em>No rows.</em>'; return; }

  if (headers.length===0) headers = Object.keys(rows[0]);

  let html = "<table class='dataframe'><thead><tr>"
           + headers.map(c=>`<th>${c}</th>`).join('')
           + "</tr></thead><tbody>";
  const CAP=5000; let i=0;
  for(const r of rows){ if(i++>=CAP) break; html+="<tr>"+headers.map(c=>`<td>${r[c]==null?'':r[c]}</td>`).join('')+"</tr>"; }
  html+="</tbody></table>";
  if(rows.length>CAP) html+=`<div style="opacity:.7;font-size:.85rem;margin-top:.35rem;">Showing first ${CAP.toLocaleString()} rows</div>`;
  mount.innerHTML=html;
}
function showError(err){
  const mount=document.getElementById('result');
  mount.innerHTML=`<pre style="color:#b71c1c;white-space:pre-wrap;">${err?.message ?? String(err)}</pre>`;
}

/* =============== run =============== */
async function runSQL(ev){
  try{
    ev?.preventDefault?.();
    const btn=document.getElementById('run');
    const status=document.getElementById('status');
    const qEl=document.getElementById('sql');
    btn.disabled=true; status.textContent='Running…';
    await ensureDB(); await registerViews();
    const res = await state.conn.query(qEl.value);
    renderTable(res); status.textContent='Done';
  }catch(err){ console.error('[sql_lab] run error:', err); document.getElementById('status').textContent='Error'; showError(err); }
  finally{ const btn=document.getElementById('run'); if(btn) btn.disabled=false; }
}
window.__runSQL__=runSQL;

/* =============== boot =============== */
onNav(async ()=>{
  const btn=document.getElementById('run'); if(btn) btn.addEventListener('click',runSQL);
  try{
    await ensureDB(); await registerViews();
    const q=document.getElementById('sql');
    if(q && !q.value.trim()){
      const prefer = state.views.find(v=>v.view==='airport_degree') || state.views[0];
      q.value = prefer ? `SELECT * FROM ${prefer.view} LIMIT 15;`
                       : `SELECT month, delay_min
                          FROM read_json_auto('${siteRoot()}api/euro_atfm_timeseries_last24.json')
                          ORDER BY month DESC LIMIT 5;`;
    }
  }catch(e){ console.warn('[sql_lab] boot warn:', e); }
});
</script>

<style>
#lab { position: relative; z-index: 3; }
.dataframe{border-collapse:collapse;width:100%;font-size:0.9rem;}
.dataframe th,.dataframe td{border:1px solid #ddd;padding:.35rem .5rem;white-space:nowrap;}
.dataframe thead th{position:sticky;top:0;background:var(--md-default-fg-color--lightest,#f7f7f7);}
</style>
