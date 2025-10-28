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

<!-- --- DuckDB SQL Lab: UI --- -->
<div id="lab" style="margin:.5rem 0;">
  <textarea id="sql" style="width:100%;height:160px;font-family:ui-monospace,monospace;">SELECT 42 AS answer;</textarea>
</div>
<p>
  <button id="run" type="button" style="padding:.45rem .9rem;">Run</button>
  <span id="status" style="margin-left:.6rem;color:#666;"></span>
</p>
<div id="result" style="margin-top:10px;overflow:auto;"></div>

<script type="module">
/* ---------- helpers (siteRoot, cache-buster, Material instant-nav hook) ---------- */
function siteRoot(){ const p = location.pathname.split('/').filter(Boolean); return p.length ? '/' + p[0] + '/' : '/'; }
function bust(u){ const v = Date.now(); return u + (u.includes('?') ? '&' : '?') + 'v=' + v; }
function onNav(fn){
  const run = () => setTimeout(fn, 0);
  if (window.document$ && typeof document$.subscribe === 'function') document$.subscribe(run);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', run); else run();
}

/* ---------- DuckDB-WASM (browser) ---------- */
import * as duckdb from 'https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.29.0/dist/duckdb-browser-eh.mjs';
import duckdb_wasm   from 'https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.29.0/dist/duckdb-wasm-eh.wasm';
import duckdb_worker from 'https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.29.0/dist/duckdb-browser-eh.worker.js';

let _db = null, _conn = null, _views = [];

function sanitizeViewName(name){ return String(name).toLowerCase().replace(/[^a-z0-9_]/g, '_').replace(/^_+/, ''); }

async function initDB(){
  if (_db) return;
  const bundle = { mainModule: duckdb_wasm, mainWorker: duckdb_worker };
  const logger = new duckdb.ConsoleLogger();
  _db = new duckdb.AsyncDuckDB(logger, bundle);
  await _db.instantiate(bundle);
  _conn = await _db.connect();
  await _conn.query('INSTALL httpfs; LOAD httpfs;');
}

async function registerViews(){
  if (_views.length) return _views;
  const url = bust(siteRoot() + 'assets/datasets.json');
  const ds  = await (await fetch(url)).json();
  const items = Array.isArray(ds) ? ds : (ds && Array.isArray(ds.items)) ? ds.items : [];
  for (const it of items){
    const f = it.file || it.path || '';
    if (!/\.csv$/i.test(f)) continue;
    const stem   = sanitizeViewName((f.split('/').pop() || '').replace(/\.csv$/i, ''));
    const csvUrl = bust(siteRoot() + 'publish/' + f);
    await _conn.query(`CREATE OR REPLACE VIEW "${stem}" AS SELECT * FROM read_csv_auto('${csvUrl}', AUTO_DETECT=TRUE, SAMPLE_SIZE=20000)`);
    _views.push({ view: stem, file: f });
  }
  return _views;
}

/* ---------- UI rendering ---------- */
function renderTable(df){
  const mount = document.getElementById('result');
  if (!df || !df.rows || df.rows.length === 0){ mount.innerHTML = '<em>No rows.</em>'; return; }
  const cols = df.schema.fields.map(f => f.name);
  let html = "<table class='dataframe'><thead><tr>" + cols.map(c=>`<th>${c}</th>`).join("") + "</tr></thead><tbody>";
  const cap = 5000; let i = 0;
  for (const row of df.rows){ if (i++ >= cap) break; html += "<tr>" + row.map(v => `<td>${v==null?'':v}</td>`).join("") + "</tr>"; }
  html += "</tbody></table>";
  if (df.rows.length > cap) html += `<div style="opacity:.7;font-size:.85rem;margin-top:.35rem;">Showing first ${cap.toLocaleString()} rows</div>`;
  mount.innerHTML = html;
}

async function runSQL(){
  const btn = document.getElementById('run');
  const status = document.getElementById('status');
  const qEl = document.getElementById('sql');
  const mount = document.getElementById('result');
  try{
    btn.disabled = true;
    status.textContent = 'Running…';
    await initDB();
    await registerViews();
    const res = await _conn.query(qEl.value);
    renderTable(res);
    status.textContent = 'Done';
  }catch(err){
    console.error(err);
    status.textContent = 'Error';
    mount.innerHTML = `<pre style="color:#b71c1c;white-space:pre-wrap;">${err?.message || String(err)}</pre>`;
  }finally{
    btn.disabled = false;
  }
}

/* ---------- Boot (bind tombol + isi contoh query) ---------- */
onNav(async () => {
  const btn = document.getElementById('run');
  if (!btn) return;
  // pastikan tombol berada di atas elemen yang mungkin overlap
  btn.style.position = 'relative'; btn.style.zIndex = '10';
  btn.addEventListener('click', runSQL);

  try{
    await initDB();
    const views = await registerViews();
    const prefer = views.find(v => v.view === 'airport_degree') || views[0];
    const q = document.getElementById('sql');
    if (q && !q.value.trim()){
      q.value = prefer
        ? `SELECT * FROM ${prefer.view} LIMIT 15;`
        : `SELECT month, delay_min
           FROM read_json_auto('${siteRoot()}api/euro_atfm_timeseries_last24.json')
           ORDER BY month DESC LIMIT 5;`;
    }
  }catch(e){ console.warn(e); }
});
</script>

<style>
/* Pastikan area interaktif tidak ketutupan overlay dari blok kode di atas */
#lab { position: relative; z-index: 1; }
#run { cursor: pointer; }
/* Styling tabel sederhana */
.dataframe{border-collapse:collapse;width:100%;font-size:0.9rem;}
.dataframe th,.dataframe td{border:1px solid #ddd;padding:.35rem .5rem;white-space:nowrap;}
.dataframe thead th{position:sticky;top:0;background:var(--md-default-fg-color--lightest,#f7f7f7);}
</style>
