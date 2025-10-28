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
<div style="margin:.5rem 0;"> <textarea id="sql" style="width:100%;height:160px;font-family:ui-monospace,monospace;"></textarea> </div> <button id="run" style="padding:.4rem .8rem;">Run</button> <span id="status" style="margin-left:.6rem;color:#666;"></span> <div id="views" style="margin:.5rem 0 .25rem 0; font-size:.9rem; opacity:.85;"></div> <div id="result" style="margin-top:10px;overflow:auto;"></div> <script type="module"> /* ---------- helpers: siteRoot + cache-buster + mkdocs instant-nav ---------- */ function siteRoot(){ const p=location.pathname.split('/').filter(Boolean); return p.length?'/'+p[0]+'/':'/'; } function bust(u){ const v=Date.now(); return u+(u.includes('?')?'&':'?')+'v='+v; } function onNav(fn){ const run=()=>setTimeout(fn,0); if(window.document$&&typeof document$.subscribe==='function'){document$.subscribe(run);} else if (document.readyState==='loading'){document.addEventListener('DOMContentLoaded',run);} else {run();}} /* ---------- datasets.json normalizer ---------- */ function normalizeDatasets(j){ let arr=[]; if (Array.isArray(j)) arr=j; else if (j && typeof j==='object'){ for (const k of ['datasets','publish','items','files','csvs']) { if (Array.isArray(j[k])) { arr=j[k]; break; } } } const rows=[]; const seen=new Set(); for (const raw of (arr||[])){ const any = (raw?.file ?? raw?.path ?? raw?.href ?? raw?.csv ?? '').toString().trim(); if (!any) continue; if (!/\.csv(\?|$)/i.test(any)) continue; // normalize path to "publish/xxx.csv" let p = any.replace(/^\.?\/*/,''); // strip ./ or leading / if (p.startsWith('docs/')) p = p.replace(/^docs\//,''); if (!p.startsWith('publish/')) { if (!p.includes('/')) p = 'publish/'+p; } if (seen.has(p)) continue; seen.add(p); // view name: file stem, sanitized to [a-z0-9_] const stem = p.split('/').pop().replace(/\.csv$/i,''); const view = stem.toLowerCase().replace(/[^a-z0-9_]/g,'_').replace(/_+/g,'_'); rows.push({ path:p, view, name:stem }); } return rows; } /* ---------- DuckDB-WASM set-up ---------- */ import * as duckdb from 'https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.29.0/dist/duckdb-browser-eh.mjs'; import duckdb_wasm from 'https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.29.0/dist/duckdb-wasm-eh.wasm'; import duckdb_worker from 'https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.29.0/dist/duckdb-browser-eh.worker.js'; let _db=null, _conn=null, _views=[]; async function initDB(){ if (_db) return; const bundle = { mainModule: duckdb_wasm, mainWorker: duckdb_worker }; const logger = new duckdb.ConsoleLogger(); _db = new duckdb.AsyncDuckDB(logger, bundle); await _db.instantiate(bundle); _conn = await _db.connect(); await _conn.query("INSTALL httpfs; LOAD httpfs;"); await _conn.query("SET memory_limit='256MB';"); // reasonable default for browser } async function registerViews(){ const resp = await fetch(bust(siteRoot()+"assets/datasets.json")); const json = await resp.json(); const items = normalizeDatasets(json); _views = items; // Create/refresh views for (const it of items){ const url = bust(siteRoot()+it.path); // same-origin CSV on GitHub Pages const q = ` CREATE OR REPLACE VIEW "${it.view}" AS SELECT * FROM read_csv_auto('${url}', AUTO_DETECT=TRUE, SAMPLE_SIZE=20000) `; await _conn.query(q); } // Render quick "available views" hint const vdiv = document.getElementById('views'); if (vdiv){ const names = items.map(it => '`'+it.view+'`').join(', '); vdiv.innerHTML = names ? `Available views: ${names}` : ''; } } /* ---------- UI: run SQL + render results ---------- */ function renderTable(df){ const mount = document.getElementById('result'); if (!df || !df.rows || df.rows.length===0){ mount.innerHTML = "<em>No rows.</em>"; return; } const cols = (df.schema?.fields||[]).map(f=>f.name); let html = "<table class='dataframe'><thead><tr>" + cols.map(c=>`<th>${c}</th>`).join("") + "</tr></thead><tbody>"; const limit = 5000; // safety cap for DOM let i=0; for (const row of df.rows){ if (i++ >= limit) break; html += "<tr>" + row.map(v=>`<td>${v===null?'':v}</td>`).join("") + "</tr>"; } html += "</tbody></table>"; if (df.rows.length > limit){ html += `<div style="opacity:.7;font-size:.85rem;margin-top:.35rem;">Showing first ${limit.toLocaleString()} rows</div>`; } mount.innerHTML = html; } async function runSQL(){ const btn=document.getElementById('run'); const status=document.getElementById('status'); const sql=document.getElementById('sql').value; const mount=document.getElementById('result'); try{ btn.disabled=true; status.textContent="Running…"; await initDB(); if (_views.length===0) await registerViews(); const res = await _conn.query(sql); renderTable(res); status.textContent="Done"; }catch(err){ console.error(err); status.textContent="Error"; mount.innerHTML="<pre style='color:#b71c1c;white-space:pre-wrap;'>"+(err.message||String(err))+"</pre>";

}finally{
btn.disabled=false;
}
}

async function boot(){
const btn=document.getElementById('run'); if(!btn) return;
btn.onclick = runSQL;

// Default example: prefer airport_degree if exists, otherwise first view
try{
await initDB();
await registerViews();
const prefer = _views.find(v => v.view === 'airport_degree') || _views[0];
const textarea = document.getElementById('sql');
if (textarea && (!textarea.value || !textarea.value.trim())){
if (prefer){
textarea.value = SELECT * FROM ${prefer.view} LIMIT 50;;
}else{
textarea.value = "-- No CSVs found under publish/. Add files then redeploy.";
}
}
} catch(e){
console.warn(e);
}
}

onNav(boot);
</script>

<style> .dataframe{border-collapse:collapse;width:100%;font-size:0.9rem;} .dataframe th,.dataframe td{border:1px solid #ddd;padding:.35rem .5rem;white-space:nowrap;} .dataframe thead th{position:sticky;top:0;background:var(--md-default-fg-color--lightest,#f7f7f7);} </style>
