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

<!-- --- DuckDB SQL Lab: UI (auto-bundle, Arrow-aware renderer) --- -->
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

<script type="module">
/* =============== helpers =============== */
const log = (...a)=>console.log('[sql_lab]', ...a);
function siteRoot(){ const p = location.pathname.split('/').filter(Boolean); return p.length?'/'+p[0]+'/':'/'; }
function bust(u){ const v=Date.now(); return u+(u.includes('?')?'&':'?')+'v='+v; }
function onNav(fn){ const run=()=>setTimeout(fn,0); if (window.document$ && typeof document$.subscribe==='function') document$.subscribe(run); if (document.readyState==='loading') document.addEventListener('DOMContentLoaded',run); else run(); }

/* =============== state =============== */
const state = { duckdb:null, db:null, conn:null, views:[] };

/* =============== load DuckDB (official bundle picker) =============== */
async function ensureDB(){
  if (state.conn) return state.conn;

  // Satu import ESM — biarkan library memilih bundle terbaik
  const duckdb = await import('https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.29.0/dist/duckdb-browser.mjs');
  state.duckdb = duckdb;

  const bundle  = await duckdb.selectBundle(duckdb.getJsDelivrBundles());
  log('bundle selected:', bundle);

  // Worker sebagai module (fallback tanpa opsi bila perlu)
  let worker;
  try { worker = new Worker(bundle.mainWorker, { type:'module' }); }
  catch { worker = new Worker(bundle.mainWorker); }

  const logger = new duckdb.ConsoleLogger();
  const db = new duckdb.AsyncDuckDB(logger, worker);
  await db.instantiate(bundle.mainModule, bundle.pthreadWorker);

  const conn = await db.connect();
  await conn.query('INSTALL httpfs; LOAD httpfs;');

  state.db = db; state.conn = conn;
  return conn;
}

/* =============== register CSV views from datasets.json =============== */
function sanitize(name){ return String(name).toLowerCase().replace(/[^a-z0-9_]/g,'_').replace(/^_+/,''); }

async function registerViews(){
  if (state.views.length) return state.views;

  let ds;
  try { ds = await (await fetch(bust(siteRoot()+'assets/datasets.json'))).json(); }
  catch(e){ log('datasets.json not available:', e); return state.views; }

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

/* =============== rendering (mendukung Arrow Result) =============== */
function renderTable(result){
  const mount = document.getElementById('result');

  // Ambil kolom dari schema atau dari objek baris
  const colsFromSchema = (result && result.schema && Array.isArray(result.schema.fields))
    ? result.schema.fields.map(f => f.name)
    : [];

  // Arrow: toArray() -> array of objects; Fallback: result.rows (bentuk lama)
  let rows = [];
  if (result && typeof result.toArray === 'function') {
    rows = result.toArray();                 // [{col:val,...}, ...]
  } else if (result && Array.isArray(result.rows)) {
    rows = result.rows;                      // [[v1,v2,...], ...]
  }

  if (!rows || rows.length === 0){
    mount.innerHTML = '<em>No rows.</em>';
    return;
  }

  const header = colsFromSchema.length
    ? colsFromSchema
    : (Array.isArray(rows[0]) ? rows[0].map((_,i)=>`col_${i+1}`) : Object.keys(rows[0]));

  let html = "<table class='dataframe'><thead><tr>" +
             header.map(c=>`<th>${c}</th>`).join('') +
             "</tr></thead><tbody>";

  const CAP = 5000;
  let i = 0;
  for (const r of rows){
    if (i++ >= CAP) break;
    if (Array.isArray(r)){
      html += "<tr>"+ r.map(v=>`<td>${v==null?'':v}</td>`).join('') +"</tr>";
    } else {
      html += "<tr>"+ header.map(c=>`<td>${r[c]==null?'':r[c]}</td>`).join('') +"</tr>";
    }
  }
  html += "</tbody></table>";
  if (rows.length > CAP)
    html += `<div style="opacity:.7;font-size:.85rem;margin-top:.35rem;">Showing first ${CAP.toLocaleString()} rows</div>`;

  mount.innerHTML = html;
}

function showError(err){
  const mount = document.getElementById('result');
  const msg = err?.message ?? String(err);
  mount.innerHTML = `<pre style="color:#b71c1c;white-space:pre-wrap;">${msg}</pre>`;
}

/* =============== run =============== */
async function runSQL(ev){
  try{
    if (ev?.preventDefault) ev.preventDefault();
    const btn=document.getElementById('run');
    const status=document.getElementById('status');
    const qEl=document.getElementById('sql');

    btn.disabled = true;
    status.textContent = 'Running…';

    await ensureDB();
    await registerViews();

    const res = await state.conn.query(qEl.value);
    renderTable(res);
    status.textContent = 'Done';
  }catch(err){
    console.error('[sql_lab] run error:', err);
    document.getElementById('status').textContent='Error';
    showError(err);
  }finally{
    const btn=document.getElementById('run');
    if (btn) btn.disabled=false;
  }
}
window.__runSQL__ = runSQL; // fallback untuk onclick inline

/* =============== boot =============== */
onNav(async ()=>{
  const btn = document.getElementById('run');
  if (btn) btn.addEventListener('click', runSQL);

  try{
    await ensureDB();
    await registerViews();

    // Prefill: pilih view CSV kalau ada; kalau tidak, demo JSON
    const q = document.getElementById('sql');
    if (q && !q.value.trim()){
      const prefer = state.views.find(v=>v.view==='airport_degree') || state.views[0];
      q.value = prefer
        ? `SELECT * FROM ${prefer.view} LIMIT 15;`
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
