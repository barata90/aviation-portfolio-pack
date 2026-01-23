# SQL Lab — Query `publish/*.csv`

Run SQL **in your browser** against your portfolio data.

<div id="lab" style="margin:.5rem 0; position:relative; z-index:3;">
  <p style="margin-bottom: 5px;">
    <strong>👉 Click "Run" to execute.</strong>
  </p>

<textarea id="sql" style="width:100%;height:160px;font-family:ui-monospace,monospace;padding:10px;border:1px solid #ccc;">
-- Check Top 10 Airports (Data from publish/airport_degree.csv)
SELECT 
    iata, 
    deg_total as total_routes
FROM airport_degree
ORDER BY total_routes DESC
LIMIT 10;
</textarea>
</div>

<p>
  <button id="run" type="button" class="md-button md-button--primary" style="padding:.45rem .9rem; cursor:pointer;">
    ▶ Run Query
  </button>
  <span id="status" style="margin-left:.6rem;color:#666;">Waiting...</span>
</p>

<div id="result" style="margin-top:10px;overflow:auto;"></div>

<script type="module">
import * as duckdb from 'https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.28.0/dist/duckdb-browser.mjs';

const runBtn = document.getElementById('run');
const statusSpan = document.getElementById('status');
const sqlInput = document.getElementById('sql');
const resultDiv = document.getElementById('result');

let db = null;
let conn = null;

// DAFTAR FILE DI FOLDER PUBLISH (Sesuai Screenshot kamu)
const FILES = [
    'airport_degree.csv',
    'dim_airport_clean.csv',
    'euro_atfm_by_location.csv',
    'euro_atfm_timeseries.csv',
    'route_counts.csv',
    'top_od_pairs.csv'
];

// Base URL Raw GitHub (Anti-Gagal)
const BASE_URL = 'https://raw.githubusercontent.com/barata90/aviation-portfolio-pack/main/publish/';

async function init() {
    if (conn) return conn;

    statusSpan.textContent = 'Initializing engine...';
    
    // 1. Setup DuckDB
    const CDN_BUNDLES = duckdb.getJsDelivrBundles();
    const bundle = await duckdb.selectBundle(CDN_BUNDLES);
    const worker_url = URL.createObjectURL(
        new Blob([`importScripts("${bundle.mainWorker}");`], {type: 'text/javascript'})
    );
    const worker = new Worker(worker_url);
    const logger = new duckdb.ConsoleLogger();
    db = new duckdb.AsyncDuckDB(logger, worker);
    await db.instantiate(bundle.mainModule, bundle.pthreadWorker);
    conn = await db.connect();

    // 2. Register Files dari folder PUBLISH
    statusSpan.textContent = 'Loading CSVs from publish/...';
    
    for (const file of FILES) {
        const tableName = file.replace('.csv', ''); // Hilangkan .csv jadi nama tabel
        const url = BASE_URL + file;
        
        // Buat View langsung ke URL Raw GitHub
        await conn.query(`
            CREATE OR REPLACE VIEW "${tableName}" 
            AS SELECT * FROM read_csv_auto('${url}');
        `);
        console.log(`Table registered: ${tableName}`);
    }

    statusSpan.textContent = 'Ready!';
    return conn;
}

// Event Listener Tombol Run
runBtn.addEventListener('click', async () => {
    runBtn.disabled = true;
    statusSpan.textContent = 'Running query...';
    resultDiv.innerHTML = '';

    try {
        const c = await init(); // Pastikan DB siap
        const query = sqlInput.value;
        const res = await c.query(query);
        
        // Render Hasil ke HTML Table
        const rows = res.toArray();
        if (rows.length === 0) {
            resultDiv.innerHTML = '<em>No results.</em>';
        } else {
            const cols = Object.keys(rows[0]);
            let html = '<table class="dataframe" style="width:100%; border-collapse:collapse; font-size:0.9rem;"><thead><tr style="background:#f0f0f0;">';
            cols.forEach(k => html += `<th style="border:1px solid #ddd; padding:5px;">${k}</th>`);
            html += '</tr></thead><tbody>';
            
            rows.forEach(row => {
                html += '<tr>';
                cols.forEach(k => html += `<td style="border:1px solid #ddd; padding:5px;">${row[k]}</td>`);
                html += '</tr>';
            });
            html += '</tbody></table>';
            resultDiv.innerHTML = html;
        }
        statusSpan.textContent = `Done (${rows.length} rows).`;
        
    } catch (err) {
        console.error(err);
        resultDiv.innerHTML = `<div style="color:red; font-weight:bold;">Error: ${err.message}</div>`;
        statusSpan.textContent = 'Error.';
    } finally {
        runBtn.disabled = false;
    }
});
</script>
