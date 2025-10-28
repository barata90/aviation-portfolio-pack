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

<!-- Import map untuk apache-arrow, dipakai oleh duckdb-wasm -->
<script type="importmap">
{
  "imports": {
    "apache-arrow": "https://cdn.jsdelivr.net/npm/apache-arrow@14.0.2/+esm"
  }
}
</script>
<!-- Shim agar import map & ESM bisa diload ulang via importShim -->
<script async src="https://cdn.jsdelivr.net/npm/es-module-shims@1.9.0/dist/es-module-shims.min.js" crossorigin="anonymous"></script>

<!-- =============== SQL Lab UI =============== -->
<div id="lab" style="margin:.5rem 0; position:relative; z-index:3;">
  <textarea id="sql" style="width:100%;height:160px;font-family:ui-monospace,monospace;">SELECT 42 AS answer;</textarea>
</div>

<p>
  <button id="run"
          type="button"
          class="md-button md-button--primary"
          style="padding:.45rem .9rem; cursor:pointer;"
          onclick="window.__sqlLabClick && window.__sqlLabClick(event)">
    Run
  </button>
  <span id="status" style="margin-left:.6rem;color:#666;">Idle</span>
</p>

<div id="result" style="margin-top:10px;overflow:auto;"></div>

<!-- ===== WRAPPER (non-module): pastikan tombol selalu bekerja ===== -->
<script>
(function(){
  const STATUS = ()=>document.getElementById('status');
  const RESULT = ()=>document.getElementById('result');
  let _moduleLoaded = false, _loading = false;

  async function loadModuleOnce(){
    if (_moduleLoaded || _loading) return;
    _loading = true;
    try{
      if (!window.importShim) return; // shim belum siap
      const tag = document.getElementById('sql-lab-module');
      if (!tag) return;
      const code = tag.textContent || '';
      const url  = 'data:text/javascript;charset=utf-8,' + encodeURIComponent(code);
      await window.importShim(url);    // eksekusi modul via shim (bukan native)
      _moduleLoaded = true;
    }catch(e){
      window.__sqlLabInitError = e;
    }finally{
      _loading = false;
    }
  }

  async function waitRunner(ms=6000){
    const t0=Date.now();
    while(Date.now()-t0<ms){
      if (window.__runSQL__) return true;
      // Coba load modul bila belum
      await loadModuleOnce();
      if (window.__runSQL__) return true;
      await new Promise(r=>setTimeout(r,120));
    }
    return !!window.__runSQL__;
  }

  window.__sqlLabClick = async function(ev){
    try{
      ev && ev.preventDefault && ev.preventDefault();
      const btn=document.getElementById('run');
      if (btn) btn.disabled=true;
      if (STATUS()) STATUS().textContent='Loading engine…';

      const ok = await waitRunner(8000);

      if (ok && window.__runSQL__){
        await window.__runSQL__(ev);
      }else{
        if (window.__sqlLabInitError){
          RESULT().innerHTML = '<pre style="color:#b71c1c;white-space:pre-wrap;">'
            + (window.__sqlLabInitError.message||String(window.__sqlLabInitError))
            + '</pre>';
          if (STATUS()) STATUS().textContent='Error';
        }else{
          RESULT().innerHTML = '<em>Engine belum siap. Coba reload (Cmd/Ctrl-Shift-R).</em>';
          if (STATUS()) STATUS().textContent='Idle';
        }
      }
    } finally {
      const btn=document.getElementById('run');
      if (btn) btn.disabled=false;
    }
  };

  // Bind normal juga (untuk yang tidak klik via onclick)
  document.addEventListener('DOMContentLoaded', function(){
    const btn=document.getElementById('run');
    if (btn) btn.addEventListener('click', window.__sqlLabClick);
  });
})();
</script>

<!-- ===== MODUL DISIMPAN SEBAGAI TEKS: dieksekusi via importShim ===== -->
<script type="application/x-sql-lab-module" id="sql-lab-module">
const log = (...a)=>console.log('[sql_lab]', ...a);
function siteRoot(){ const p=location.pathname.split('/').filter(Boolean); return p.length?'/'+p[0]+'/':'/'; }
function bust(u){ const v=Date.now(); return u+(u.includes('?')?'&':'?')+'v='+v; }
function onNav(fn){
  const run=()=>setTimeout(fn,0);
  if (window.document$ && typeof document$.subscribe==='function') document$.subscribe(run);
  if (document.readyState==='loading') document.addEventListener('DOMContentLoaded',run); else run();
}

import * as duckdb from 'https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.29.0/dist/duckdb-browser-eh.mjs';
const WASM_URL   = 'https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.29.0/dist/duckdb-wasm-eh.wasm';
const WORKER_URL = 'https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.29.0/dist/duckdb-browser-eh.worker.js';

const state = { db:null, conn:null, views:[] };

async function makeSameOriginWorker(){
  try{
    const src = await (await fetch(WORKER_URL, {mode:'cors'})).text();
    const blob = new Blob([src], {type:'text/javascript'});
    const blobURL = URL.createObjectURL(blob);
    return new Worker(blobURL);
  }catch(e){
    return new Worker(WORKER_URL);
  }
}

async function ensureDB(){
  if (state.conn) return state.conn;
  const worker = await makeSameOriginWorker();
  const logger = new duckdb.ConsoleLogger();
  const db = new duckdb.AsyncDuckDB(logger, worker);
  await db.instantiate(WASM_URL);
  const conn = await db.connect();
  await conn.query('INSTALL httpfs; LOAD httpfs;');
  state.db=db; state.conn=conn;
  return conn;
}

function sanitize(name){ return String(name).toLowerCase().replace(/[^a-z0-9_]/g,'_').replace(/^_+/,''); }

async function registerViews(){
  if (state.views.length) return state.views;
  let ds;
  try { ds = await (await fetch(bust(siteRoot()+'assets/datasets.json'))).json(); }
  catch(e){ log('datasets.json not found/unreadable:', e); return state.views; }

  const items = Array.isArray(ds) ? ds : (ds && Array.isArray(ds.items)) ? ds.items : [];
  for (const it of items){
    const f = it.file || it.path || '';
    if (!/\.csv$/i.test(f)) continue;
    const stem   = sanitize((f.split('/').pop()||'').replace(/\.csv$/i,''));
    const csvUrl = bust(siteRoot()+'publish/'+f);
    await state.conn.query(`
      CREATE OR REPLACE VIEW "${stem}"
      AS SELECT * FROM read_csv_auto('${csvUrl}', AUTO_DETECT=TRUE, SAMPLE_SIZE=20000);
    `);
    state.views.push({ view: stem, file: f });
  }
  return state.views;
}

function renderTable(df){
  const mount=document.getElementById('result');
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
  const mount=document.getElementById('result');
  mount.innerHTML = `<pre style="color:#b71c1c;white-space:pre-wrap;">${err?.message||String(err)}</pre>`;
}

async function doRun(){
  const status=document.getElementById('status'); const qEl=document.getElementById('sql');
  try{
    status.textContent='Running…';
    await ensureDB();
    await registerViews();
    const res = await state.conn.query(qEl.value);
    renderTable(res);
    status.textContent='Done';
  }catch(err){
    console.error('[sql_lab] run error:', err);
    status.textContent='Error';
    showError(err);
  }
}

window.__runSQL__ = async function(ev){
  ev && ev.preventDefault && ev.preventDefault();
  const btn=document.getElementById('run'); if(btn) btn.disabled=true;
  try{ await doRun(); } finally{ if(btn) btn.disabled=false; }
};

// Prefill setelah navigasi
onNav(async ()=>{
  try{
    await ensureDB();
    await registerViews();
    const q=document.getElementById('sql');
    if(q && !q.value.trim()){
      const prefer = state.views.find(v=>v.view==='airport_degree') || state.views[0];
      q.value = prefer
        ? `SELECT * FROM ${prefer.view} LIMIT 15;`
        : `SELECT month, delay_min
           FROM read_json_auto('${siteRoot()}api/euro_atfm_timeseries_last24.json')
           ORDER BY month DESC LIMIT 5;`;
    }
  }catch(e){
    window.__sqlLabInitError = e;
    console.warn('[sql_lab] init warn:', e);
  }
});
</script>

<style>
#lab { position: relative; z-index: 3; }
.dataframe{border-collapse:collapse;width:100%;font-size:0.9rem;}
.dataframe th,.dataframe td{border:1px solid #ddd;padding:.35rem .5rem;white-space:nowrap;}
.dataframe thead th{position:sticky;top:0;background:var(--md-default-fg-color--lightest,#f7f7f7);}
</style>
