# SQL Lab

Run SQL in your browser using DuckDB-WASM.

<style>
  .sql-container { margin: 1em 0; }
  textarea { width: 100%; height: 150px; font-family: monospace; padding: 10px; border: 1px solid #ccc; border-radius: 4px; }
  button { cursor: pointer; background: #2f3640; color: white; border: none; padding: 8px 16px; border-radius: 4px; font-weight: bold; margin-top: 5px; }
  button:disabled { background: #95a5a6; cursor: wait; }
  #output-table { margin-top: 1em; overflow-x: auto; font-size: 0.9em; }
  table { border-collapse: collapse; width: 100%; }
  th, td { border: 1px solid #ddd; padding: 6px; text-align: left; }
  th { background-color: #f2f2f2; }
</style>

<div class="sql-container">
<p><strong>👇 Edit SQL & Run (Top 10 Airports):</strong></p>
<textarea id="custom-sql">
SELECT 
    iata, 
    city, 
    country, 
    deg_total as total_routes
FROM read_csv_auto('https://raw.githubusercontent.com/barata90/aviation-portfolio-pack/main/publish/airport_degree.csv')
ORDER BY total_routes DESC
LIMIT 10;
</textarea>
<button id="run-btn">▶ RUN QUERY</button>
<div id="status-msg" style="display:inline-block; margin-left:10px; color:#666;">Ready</div>
</div>

<div id="output-table"></div>

<script type="module">
import * as duckdb from 'https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.28.0/dist/duckdb-browser.mjs';

const runBtn = document.getElementById('run-btn');
const sqlInput = document.getElementById('custom-sql');
const statusMsg = document.getElementById('status-msg');
const outputDiv = document.getElementById('output-table');

let db = null;
let conn = null;

async function initDB() {
    if (conn) return conn;
    
    statusMsg.innerText = "Initializing DuckDB...";
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
    statusMsg.innerText = "Ready";
    return conn;
}

runBtn.addEventListener('click', async () => {
    runBtn.disabled = true;
    statusMsg.innerText = "Running...";
    outputDiv.innerHTML = "";

    try {
        const c = await initDB();
        const query = sqlInput.value;
        const result = await c.query(query);
        
        // Render Table Simple
        const rows = result.toArray();
        if (rows.length === 0) {
            outputDiv.innerHTML = "<em>No results found.</em>";
        } else {
            const keys = Object.keys(rows[0]);
            let html = '<table><thead><tr>' + keys.map(k => `<th>${k}</th>`).join('') + '</tr></thead><tbody>';
            rows.forEach(row => {
                html += '<tr>' + keys.map(k => `<td>${row[k]}</td>`).join('') + '</tr>';
            });
            html += '</tbody></table>';
            outputDiv.innerHTML = html;
        }
        statusMsg.innerText = "Done (" + rows.length + " rows)";
    } catch (err) {
        console.error(err);
        outputDiv.innerHTML = `<div style="color:red; font-weight:bold;">Error: ${err.message}</div>`;
        statusMsg.innerText = "Error";
    } finally {
        runBtn.disabled = false;
    }
});
</script>
