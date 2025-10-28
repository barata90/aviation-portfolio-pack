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
<div style="margin:.5rem 0;"> <textarea id="sql" style="width:100%;height:160px;font-family:ui-monospace,monospace;"></textarea> </div> <button id="run" style="padding:.4rem .8rem;">Run</button> <span id="status" style="margin-left:.6rem;color:#666;"></span> <div id="views_help" style="margin:.6rem 0 .2rem 0; font-size:.9rem; opacity:.85;"></div> <div id="result" style="margin-top:10px;overflow:auto;"></div> <script type="module"> /* ---------- helpers: site root + cache buster + mkdocs instant nav ---------- */ function siteRoot(){ const p=location.pathname.split('/').filter(Boolean); return p.length?'/'+p[0]+'/':'/'; } function bust(u){ const v=Date.now(); return u+(u.includes('?')?'&':'?')+'v='+v; } function onNav(fn){ const run=()=>setTimeout(fn,0); if(window.document$ && typeof document$.subscribe==='function'){ document$.subscribe(run); } else if(document.readyState==='loading'){ document.addEventListener('DOMContentLoaded',run); } else { run(); } } /* ---------- duckdb-wasm imports ---------- */ import * as duckdb from 'https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.29.0/dist/duckdb-browser-eh.mjs'; import duckdb_wasm from 'https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.29.0/dist/duckdb-wasm-eh.wasm'; import duckdb_worker from 'https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.29.0/dist/duckdb-browser-eh.worker.js'; let _db=null, _conn=null, _views=[]; /* sanitize filename -> view name */ function stemToView(stem){ return String(stem).toLowerCase().replace(/[^a-z0-9_]+/g,'_').replace(/^_+|_+$/g,''); } /* register views from assets/datasets.json (only *.csv) */ async function registerViews(){ const help = document.getElementById('views_help'); const list = await (await fetch(bust(siteRoot()+'assets/datasets.json'))).json().catch(()=>[]); const csvs = (Array.isArray(list)?list:[]).filter(d=>/\.csv$/i.test(d.file)); _views = []; for (const d of csvs){ const url = bust(siteRoot()+'publish/'+d.file); const view = stemToView(d.file.replace(/\.csv$/i,'')); await _conn.query(`CREATE OR REPLACE VIEW "${view}" AS SELECT * FROM read_csv_auto('${url}', AUTO_DETECT=TRUE, SAMPLE_SIZE=20000);`); _views.push({view, url}); } if (_views.length){ help.innerHTML = "Available views: " + _views.map(v=>`<code>${v.view}</code>`).join(', '); } else { help.innerHTML = "<em>No CSVs detected under <code>publish/</code>. Add files then redeploy.</em>"; } } /* initialize DB once */ async function initDB(){ if (_db) return; const bundle = { mainModule: duckdb_wasm, mainWorker: duckdb_worker }; const logger = new duckdb.ConsoleLogger(); _db = new duckdb.AsyncDuckDB(logger, bundle); await _db.instantiate(bundle); _conn = await _db.connect(); await _conn.query("INSTALL httpfs; LOAD httpfs;"); } /* render duckdb result to simple HTML table */ function renderTable(res){ const mount = document.getElementById('result'); if (!res){ mount.innerHTML = "<em>No result.</em>"; return; } const cols = (res.schema?.fields||[]).map(f=>f.name); const rows = res.toArray(); // array of objects if (!rows.length){ mount.innerHTML = "<em>No rows.</em>"; return; } let html = "<div style='font-size:.85rem;margin-top:.35rem;'>Showing first " + rows.length.toLocaleString() + " rows</div>"; html += "<table class='dataframe'><thead><tr>" + cols.map(c=>`<th>${c}</th>`).join("") + "</tr></thead><tbody>"; for (const r of rows){ html += "<tr>" + cols.map(c=>`<td>${r[c] ?? ''}</td>`).join("") + "</tr>"; } html += "</tbody></table>"; mount.innerHTML = html; } /* run button */ async function runSQL(){ const btn = document.getElementById('run'); const status = document.getElementById('status'); const sql = document.getElementById('sql').value; const mount = document.getElementById('result'); try{ btn.disabled = true; status.textContent = "Running…"; await initDB(); if (_views.length===0) await registerViews(); const res = await _conn.query(sql); renderTable(res); status.textContent = "Done"; } catch(err){ console.error(err); status.textContent = "Error"; mount.innerHTML = "<pre style='color:#b71c1c;white-space:pre-wrap;'>"+(err.message||String(err))+"</pre>";

} finally {
btn.disabled = false;
}
}

/* boot on page load / mkdocs instant-nav */
async function boot(){
const btn = document.getElementById('run');
if (!btn) return;
btn.onclick = runSQL;

try{
await initDB();
await registerViews();
const q = document.getElementById('sql');
if (q && !q.value.trim()){
const prefer = _views.find(v=>v.view==='airport_degree') || _views[0];
q.value = prefer ? SELECT * FROM ${prefer.view} LIMIT 50;
: -- No CSVs found under publish/. Add files then redeploy.;
}
} catch(err){
console.warn(err);
}
}
onNav(boot);
</script>

<style> .dataframe{border-collapse:collapse;width:100%;font-size:0.9rem;} .dataframe th,.dataframe td{border:1px solid #ddd;padding:.35rem .5rem;white-space:nowrap;} .dataframe thead th{position:sticky;top:0;background:var(--md-default-fg-color--lightest,#f7f7f7);} </style>
