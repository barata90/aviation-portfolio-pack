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

<div style="margin:.5rem 0;"> <textarea id="sql" style="width:100%;height:160px;font-family:ui-monospace,monospace;"></textarea> </div> <button id="run" style="padding:.4rem .8rem;">Run</button> <span id="status" style="margin-left:.6rem;color:#666;"></span> <div id="result" style="margin-top:10px;overflow:auto;"></div> <script type="module"> /* ---------- helpers (siteRoot, cache-buster, material instant nav) ---------- */ function siteRoot(){ const p=location.pathname.split('/').filter(Boolean); return p.length?'/'+p[0]+'/':'/'; } function bust(u){ return u+(u.includes('?')?'&':'?')+'v='+Date.now(); } function onNav(fn){ const run=()=>setTimeout(fn,0); if (window.document$) document$.subscribe(run); if (document.readyState==='loading') document.addEventListener('DOMContentLoaded',run); else run(); } /* ------------------------------- duckdb-wasm ------------------------------- */ import * as duckdb from 'https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.29.0/dist/duckdb-browser-eh.mjs'; import duckdb_wasm from 'https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.29.0/dist/duckdb-wasm-eh.wasm'; import duckdb_worker from 'https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.29.0/dist/duckdb-browser-eh.worker.js'; let db=null, conn=null, views=[]; function sanitize(name){ return String(name).toLowerCase().replace(/[^a-z0-9_]/g,'_').replace(/_+/g,'_'); } async function initDB(){ if (db) return; const logger = new duckdb.ConsoleLogger(); db = new duckdb.AsyncDuckDB(logger, { mainModule: duckdb_wasm, mainWorker: duckdb_worker }); await db.instantiate(); conn = await db.connect(); await conn.query("INSTALL httpfs; LOAD httpfs;"); } async function registerViews(){ if (views.length) return views; // read datasets index and create 1 view per CSV const ds = await (await fetch(bust(siteRoot()+'assets/datasets.json'))).json(); const items = Array.isArray(ds) ? ds : (ds.items || ds.files || ds || []); const files = items .map(x => (x.path || x.file || '').split('/').pop()) .filter(f => /\.csv$/i.test(f)); for (const f of files){ const stem = sanitize(f.replace(/\.csv$/i,'')); const csvUrl = bust(siteRoot()+'publish/'+f); await conn.query(`CREATE OR REPLACE VIEW ${stem} AS SELECT * FROM read_csv_auto('${csvUrl}', AUTO_DETECT=TRUE, SAMPLE_SIZE=20000);`); views.push({ view: stem, file: f }); } return views; } /* ---------------------------------- UI ------------------------------------ */ function renderTable(df){ const mount = document.getElementById('result'); if (!df || !df.rows || df.rows.length===0){ mount.innerHTML = "<em>No rows.</em>"; return; } const cols = df.schema.fields.map(f=>f.name); let html = "<table class='dataframe'><thead><tr>" + cols.map(c=>`<th>${c}</th>`).join("") + "</tr></thead><tbody>"; const cap = 5000; let i=0; for (const row of df.rows){ if (i++>=cap) break; html += "<tr>" + row.map(v=>`<td>${v===null?'':v}</td>`).join("") + "</tr>"; } html += "</tbody></table>"; if (df.rows.length>cap) html += `<div style="opacity:.7;font-size:.85rem;margin-top:.35rem;">Showing first ${cap.toLocaleString()} rows</div>`; mount.innerHTML = html; } async function runSQL(){ const btn = document.getElementById('run'); const status = document.getElementById('status'); const q = document.getElementById('sql'); const mount = document.getElementById('result'); try{ btn.disabled = true; status.textContent = "Running…"; await initDB(); await registerViews(); const res = await conn.query(q.value); renderTable(res); status.textContent = "Done"; }catch(err){ console.error(err); status.textContent = "Error"; mount.innerHTML = "<pre style='color:#b71c1c;white-space:pre-wrap;'>" + (err.message||String(err)) + "</pre>";

}finally{
btn.disabled = false;
}
}

onNav(() => {
const btn = document.getElementById('run');
if (!btn) return;
btn.addEventListener('click', runSQL);

// Prefill: prefer a CSV view if available; else demo JSON
(async () => {
try{
await initDB();
const v = (await registerViews()).find(x=>x.view==='airport_degree') || views[0];
const q = document.getElementById('sql');
if (q && !q.value.trim()){
q.value = v ? SELECT * FROM ${v.view} LIMIT 15;
: SELECT month, delay_min FROM read_json_auto('${siteRoot()}api/euro_atfm_timeseries_last24.json') ORDER BY month DESC LIMIT 5;;
}
}catch(e){ console.warn(e); }
})();
});
</script>

<style> .dataframe{border-collapse:collapse;width:100%;font-size:0.9rem;} .dataframe th,.dataframe td{border:1px solid #ddd;padding:.35rem .5rem;white-space:nowrap;} .dataframe thead th{position:sticky;top:0;background:var(--md-default-fg-color--lightest,#f7f7f7);} </style>
