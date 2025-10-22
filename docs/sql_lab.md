# SQL Lab — Query `publish/*.csv` with DuckDB-WASM

Run SQL **in your browser** against the portfolio CSVs. Each file under `publish/` is exposed as a **view** named by its file stem:
`route_counts`, `airport_degree`, `euro_atfm_timeseries`, `euro_atfm_by_location`, `top_od_pairs`, `dim_airport_clean`.

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
<div style="margin:.5rem 0;"> <textarea id="sql" style="width:100%;height:160px;font-family:ui-monospace,monospace;"></textarea> </div> <button id="run" style="padding:.4rem .8rem;">Run</button> <span id="status" style="margin-left:.6rem;color:#666;"></span> <div id="result" style="margin-top:10px;overflow:auto;"></div> <script type="module"> /* Helpers: siteRoot + cache-buster + MkDocs instant-nav hook */ function siteRoot(){ const p=location.pathname.split('/').filter(Boolean); return p.length?'/'+p[0]+'/':'/'; } function bust(u){ const v=Date.now(); return u+(u.includes('?')?'&':'?')+'v='+v; } function onNav(fn){ function run(){ setTimeout(fn,0);} if(window.document$) document$.subscribe(run); if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',run); else run(); } /* DuckDB-WASM */ import * as duckdb from 'https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.29.0/dist/duckdb-browser-eh.mjs'; import duckdb_wasm from 'https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.29.0/dist/duckdb-wasm-eh.wasm'; import duckdb_worker from 'https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.29.0/dist/duckdb-browser-eh.worker.js'; let _db=null, _conn=null; async function initDB(){ if (_db) return; const bundle = { mainModule: duckdb_wasm, mainWorker: duckdb_worker }; const logger = new duckdb.ConsoleLogger(); _db = new duckdb.AsyncDuckDB(logger, bundle); await _db.instantiate(bundle); _conn = await _db.connect(); await _conn.query("INSTALL httpfs; LOAD httpfs;"); // Create views for each CSV from datasets.json const ds = await (await fetch(bust(siteRoot()+"assets/datasets.json"))).json(); for (const d of ds){ const stem = d.file.replace(/\.csv$/i,''); const url = bust(siteRoot()+"publish/"+d.file); await _conn.query(`CREATE OR REPLACE VIEW "${stem}" AS SELECT * FROM read_csv_auto('${url}', AUTO_DETECT=TRUE, SAMPLE_SIZE=20000);`); } } function renderTable(df){ const mount=document.getElementById('result'); if (!df || df.rows.length===0){ mount.innerHTML="<em>No rows.</em>"; return; } const cols = df.schema.fields.map(f=>f.name); let html = "<table class='dataframe'><thead><tr>" + cols.map(c=>`<th>${c}</th>`).join("") + "</tr></thead><tbody>"; for (const row of df.rows){ html += "<tr>" + row.map(v=>`<td>${v===null?'':v}</td>`).join("") + "</tr>"; } html += "</tbody></table>"; mount.innerHTML = html; } async function runSQL(){ const btn=document.getElementById('run'); const status=document.getElementById('status'); const sql=document.getElementById('sql').value; const mount=document.getElementById('result'); try{ btn.disabled=true; status.textContent="Running…"; await initDB(); const res = await _conn.query(sql); renderTable(res); status.textContent="Done"; }catch(err){ console.error(err); status.textContent="Error"; mount.innerHTML="<pre style='color:#b71c1c;white-space:pre-wrap;'>"+(err.message||String(err))+"</pre>";

}finally{
btn.disabled=false;
}
}
function boot(){
const btn=document.getElementById('run'); if(!btn) return;
btn.onclick=runSQL;
const q=document.getElementById('sql');
if(q && !q.value.trim()){ q.value="SELECT iata, deg_total FROM airport_degree ORDER BY deg_total DESC LIMIT 15;"; }
}
onNav(boot);
</script>

<style> .dataframe{border-collapse:collapse;width:100%;font-size:0.9rem;} .dataframe th,.dataframe td{border:1px solid #ddd;padding:.35rem .5rem;white-space:nowrap;} .dataframe thead th{position:sticky;top:0;background:var(--md-default-fg-color--lightest,#f7f7f7);} </style>

