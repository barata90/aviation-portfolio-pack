# SQL Lab — Query `publish/*.csv` with DuckDB-WASM

Run SQL **in your browser** against the portfolio CSVs. Each file under `publish/` is exposed as a **view** named by its file stem.

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
```
<div id="lab" style="margin:.5rem 0; position:relative; z-index:3;"> <p style="margin-bottom: 5px;"> <strong>👉 Click "Run" or press Shift+Enter to execute.</strong> </p>

<textarea id="sql" style="width:100%;height:160px;font-family:ui-monospace,monospace;padding:10px;border:1px solid #ccc;"> -- Check Top 10 Airports (Data from publish/airport_degree.csv) SELECT iata, deg_total as total_routes FROM airport_degree ORDER BY total_routes DESC LIMIT 10; </textarea>

</div>

<p> <button id="run" type="button" class="md-button md-button--primary" style="padding:.45rem .9rem; cursor:pointer;" onclick="window.runSQL && window.runSQL(event)"> Run </button> <span id="status" style="margin-left:.6rem;color:#666;">Idle</span> </p>

<div id="result" style="margin-top:10px;overflow:auto;"></div>

<script type="importmap"> { "imports": { "apache-arrow": "https://cdn.jsdelivr.net/npm/apache-arrow@14.0.2/+esm" } } </script>

<script type="module"> /* =============== helpers =============== */ const log=(...a)=>console.log('[sql_lab]',...a); function onNav(fn){ const run=()=>setTimeout(fn,0); if(window.document$&&typeof document$.subscribe==='function') document$.subscribe(run); if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',run); else run(); }

/* =============== state =============== */ const state={ duckdb:null, db:null, conn:null, views:[] };

/* =============== probes (SAB & IndexedDB) =============== */ const supportsSAB = !!self.SharedArrayBuffer && self.crossOriginIsolated===true; function probeIndexedDB(){ return new Promise((resolve)=>{ try{ const req=indexedDB.open('duckdb_probe'); req.onsuccess=()=>{ try{req.result.close(); indexedDB.deleteDatabase('duckdb_probe');}catch{} resolve(true); }; req.onerror=()=>resolve(false); req.onblocked=()=>resolve(false); }catch{ resolve(false); } }); }

/* =============== load DuckDB (bundle resmi + worker blob) =============== */ async function ensureDB(){ if(state.conn) return state.conn;

const idbOK = await probeIndexedDB(); if(!idbOK){ // hindari throw “operation is insecure” try{ Object.defineProperty(globalThis,'indexedDB',{value:undefined,writable:true,configurable:true}); }catch{} }

// Import ESM utama let duckdb; try{ duckdb = await import('https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.29.0/dist/duckdb-browser.mjs'); }catch{ duckdb = await import('https://unpkg.com/@duckdb/duckdb-wasm@1.29.0/dist/duckdb-browser.mjs'); } state.duckdb = duckdb;

// Ambil daftar bundle const bundles = duckdb.getJsDelivrBundles ? duckdb.getJsDelivrBundles() : duckdb.getCdnBundles(); let chosen = await duckdb.selectBundle(bundles);

if (chosen?.pthreadWorker && (!supportsSAB || !idbOK)) chosen = bundles.mvp || chosen; if (!chosen?.mainWorker || !chosen?.mainModule) chosen = bundles.mvp || bundles.eh || chosen;

const workerSource = importScripts(&quot;${chosen.mainWorker}&quot;);; const workerUrl = URL.createObjectURL(new Blob([workerSource], { type: "text/javascript" })); const worker = new Worker(workerUrl); const logger = new duckdb.ConsoleLogger(); const db = new duckdb.AsyncDuckDB(logger, worker);

await db.instantiate(chosen.mainModule, chosen.pthreadWorker); const conn = await db.connect(); await conn.query('INSTALL httpfs; LOAD httpfs;');

state.db=db; state.conn=conn; return conn; }

/* =============== REGISTER VIEWS (MODIFIED: MANUAL LIST) =============== / / Bagian ini dimodifikasi agar membaca langsung dari folder publish tanpa datasets.json */ async function registerViews(){ if(state.views.length) return state.views;

// DAFTAR FILE MANUAL (Sesuai Screenshot Anda) const csvFiles = [ "airport_degree.csv", "dim_airport_clean.csv", "euro_atfm_by_location.csv", "euro_atfm_timeseries.csv", "route_counts.csv", "top_od_pairs.csv" ];

// URL Raw GitHub agar tidak kena masalah path local const baseUrl = "https://www.google.com/search?q=https://raw.githubusercontent.com/barata90/aviation-portfolio-pack/main/publish/";

for(const f of csvFiles){ const stem = f.replace('.csv', '').replace(/[^a-z0-9_]/g,'_'); const csvUrl = baseUrl + f;

// Log untuk debugging di Console browser
console.log(`Registering view: ${stem} from ${csvUrl}`);

try {
    await state.conn.query(`
      CREATE OR REPLACE VIEW &quot;${stem}&quot;
      AS SELECT * FROM read_csv_auto(&#39;${csvUrl}&#39;, AUTO_DETECT=TRUE, SAMPLE_SIZE=20000);
    `);
    state.views.push({view:stem, file:f});
} catch(err) {
    console.warn(`Failed to load ${f}`, err);
}
} return state.views; }

/* =============== renderer (Arrow-first, fallback array) =============== */ function renderTable(result){ const mount=document.getElementById('result');

let headers = []; if (Array.isArray(result?.schema?.fields)) headers = result.schema.fields.map(f=>f.name);

const rows = []; if (result && typeof result[Symbol.iterator] === 'function') { for (const row of result) { const obj = {}; if (headers.length === 0) headers = Object.keys(row); for (const k of headers) obj[k] = row[k]; rows.push(obj); } } else if (typeof result?.toArray === 'function') { const arr = result.toArray(); if (arr.length && !Array.isArray(arr[0])) { rows.push(...arr); if (headers.length===0 && rows.length) headers = Object.keys(rows[0]); } }

if (!rows.length){ mount.innerHTML='<em>No rows.</em>'; return; } if (headers.length===0) headers = Object.keys(rows[0]);

let html = "<table class='dataframe'><thead><tr>" + headers.map(c=>&lt;th&gt;${c}&lt;/th&gt;).join('') + "</tr></thead><tbody>"; const CAP=5000; let i=0; for(const r of rows){ if(i++>=CAP) break; html+="<tr>"+headers.map(c=>&lt;td&gt;${r[c]==null?&#39;&#39;:r[c]}&lt;/td&gt;).join('')+"</tr>"; } html+="</tbody></table>"; if(rows.length>CAP) html+=&lt;div style=&quot;opacity:.7;font-size:.85rem;margin-top:.35rem;&quot;&gt;Showing first ${CAP.toLocaleString()} rows&lt;/div&gt;; mount.innerHTML=html; }

function showError(err){ const mount=document.getElementById('result'); mount.innerHTML=&lt;pre style=&quot;color:#b71c1c;white-space:pre-wrap;&quot;&gt;${err?.message ?? String(err)}&lt;/pre&gt;;

}

/* =============== run =============== */ async function runSQL(ev){ try{ ev?.preventDefault?.(); const btn=document.getElementById('run'); const status=document.getElementById('status'); const qEl=document.getElementById('sql'); btn.disabled=true; status.textContent='Running…'; await ensureDB(); await registerViews(); const res = await state.conn.query(qEl.value); renderTable(res); status.textContent='Done'; }catch(err){ console.error('[sql_lab] run error:', err); document.getElementById('status').textContent='Error'; showError(err); } finally{ const btn=document.getElementById('run'); if(btn) btn.disabled=false; } } window.runSQL=runSQL;

/* =============== boot =============== */ onNav(async ()=>{ const btn=document.getElementById('run'); if(btn) btn.addEventListener('click',runSQL); }); </script>

<style> #lab { position: relative; z-index: 3; } .dataframe{border-collapse:collapse;width:100%;font-size:0.9rem;} .dataframe th,.dataframe td{border:1px solid #ddd;padding:.35rem .5rem;white-space:nowrap;} .dataframe thead th{position:sticky;top:0;background:var(--md-default-fg-color--lightest,#f7f7f7);} </style>
