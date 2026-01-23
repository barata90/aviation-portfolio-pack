# SQL Lab — Query `publish/*.csv` with DuckDB-WASM

Run SQL **in your browser** against the portfolio CSVs. Each file under `publish/` is exposed as a **view**.

<div id="lab" style="margin:.5rem 0; position:relative; z-index:3;">

  <div style="margin-bottom: 10px; display: flex; gap: 8px; flex-wrap: wrap;">
    <button class="md-button" style="font-size:0.75rem; padding: 4px 10px; cursor:pointer; background:#e3f2fd; color:#0d47a1; border:none;" onclick="setQuery('global')">🏆 Top Global Hubs</button>
    <button class="md-button" style="font-size:0.75rem; padding: 4px 10px; cursor:pointer; background:#e8f5e9; color:#1b5e20; border:none;" onclick="setQuery('me_eu')">⚔️ ME vs Europe</button>
    <button class="md-button" style="font-size:0.75rem; padding: 4px 10px; cursor:pointer; background:#fff3e0; color:#e65100; border:none;" onclick="setQuery('routes')">✈️ Top Routes</button>
    <button class="md-button" style="font-size:0.75rem; padding: 4px 10px; cursor:pointer; background:#ffebee; color:#b71c1c; border:none;" onclick="setQuery('delay')">⏱️ Delay Analysis</button>
  </div>

  <p style="margin-bottom: 5px; font-size:0.85em; color:#666;">
    <strong>👉 Edit SQL below or select a button above, then click "Run Query".</strong>
  </p>
  
  <textarea id="sql" style="width:100%;height:180px;font-family:ui-monospace,monospace;padding:10px;border:1px solid #ccc;border-radius:4px;background:#f8f8f8; color:#222; font-size:14px; line-height:1.4;">
-- Click a button above to load a sample query...
-- Default Example:
SELECT iata, deg_total as total_routes 
FROM airport_degree 
ORDER BY deg_total DESC 
LIMIT 10;
  </textarea>
</div>

<p>
  <button id="run"
          type="button"
          class="md-button md-button--primary"
          style="padding:.45rem .9rem; cursor:pointer;"
          onclick="window.__runSQL__ && window.__runSQL__(event)">
    ▶ Run Query
  </button>
  <span id="status" style="margin-left:.6rem;color:#666;font-style:italic;font-size:0.9em;">Ready</span>
</p>

<div id="result" style="margin-top:15px; overflow:auto; min-height:50px; border-top:1px solid #eee; padding-top:10px;"></div>

<script type="importmap">
{
  "imports": {
    "apache-arrow": "https://cdn.jsdelivr.net/npm/apache-arrow@14.0.2/+esm",
    "@duckdb/duckdb-wasm": "https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.29.0/dist/duckdb-browser.mjs"
  }
}
</script>

<script type="module">
// --- Config & Helpers ---
const log = (...a) => console.log('[sql_lab]', ...a);
const getSiteRoot = () => {
    const path = window.location.pathname;
    if (path.includes('/aviation-portfolio-pack/')) return '/aviation-portfolio-pack/';
    return '/';
};

const state = { conn: null, initialized: false };

// --- E. PRESET QUERIES (English) ---
const queries = {
    global: `-- 🏆 Top 15 Most Connected Airports (Global Hubs)
SELECT 
    iata, 
    deg_out AS outbound_routes,
    deg_in AS inbound_routes,
    deg_total AS total_connectivity
FROM airport_degree
ORDER BY deg_total DESC
LIMIT 15;`,

    me_eu: `-- ⚔️ Battle of Hubs: Middle East vs Europe
-- Comparative analysis of connectivity strategies
SELECT 
    iata, 
    deg_total AS total_connectivity,
    CASE 
        WHEN iata IN ('DXB', 'DOH', 'AUH', 'IST') THEN 'Middle East / Super Connector'
        ELSE 'European Legacy Hub'
    END AS region
FROM airport_degree
WHERE iata IN ('DXB', 'DOH', 'AUH', 'FRA', 'LHR', 'AMS', 'CDG', 'MUC')
ORDER BY total_connectivity DESC;`,

    routes: `-- ✈️ High Density Routes (Top OD Pairs)
-- Airport pairs with the highest number of unique routes/airlines
SELECT 
    src_iata || ' ➡ ' || dst_iata AS route_pair,
    num_routes AS carrier_count
FROM route_counts
ORDER BY num_routes DESC
LIMIT 15;`,

    delay: `-- ⏱️ Delay Analysis (Eurocontrol Data)
-- Areas with the highest total delay minutes
SELECT 
    location,
    CAST(delay_minutes AS INT) as total_delay_minutes
FROM euro_atfm_by_location
ORDER BY delay_minutes DESC
LIMIT 10;`
};

// Button Helper Function
window.setQuery = (key) => {
    const q = queries[key];
    if(q) {
        document.getElementById('sql').value = q;
        // Optional: Uncomment below to auto-run on click
        // document.getElementById('run').click(); 
    }
};

// --- A. Setup DuckDB ---
async function ensureDB() {
    if (state.conn) return state.conn;
    
    const duckdb = await import('@duckdb/duckdb-wasm');
    const bundles = duckdb.getJsDelivrBundles();
    const chosen = await duckdb.selectBundle(bundles);
    
    const workerUrl = URL.createObjectURL(
        new Blob([`importScripts("${chosen.mainWorker}");`], {type: 'text/javascript'})
    );
    
    const db = new duckdb.AsyncDuckDB(new duckdb.ConsoleLogger(), new Worker(workerUrl));
    await db.instantiate(chosen.mainModule, chosen.pthreadWorker);
    
    const conn = await db.connect();
    await conn.query('INSTALL httpfs; LOAD httpfs;');
    state.conn = conn;
    return conn;
}

// --- B. Register CSVs as Tables ---
async function registerViews() {
    if (state.initialized) return;
    const conn = await ensureDB();
    const root = getSiteRoot();
    
    try {
        const jsonUrl = root + 'assets/datasets.json';
        const resp = await fetch(jsonUrl);
        if(!resp.ok) throw new Error("Failed to load datasets.json");
        
        const data = await resp.json();
        // Fallback: check 'datasets' (new) or 'items' (old)
        const items = data.datasets || data.items || (Array.isArray(data) ? data : []);

        for (const item of items) {
            const filePath = item.path || item.file; 
            if (!filePath || !filePath.endsWith('.csv')) continue;
            
            // Sanitize table name
            const tableName = item.name || filePath.split('/').pop().replace('.csv', '').replace(/[^a-z0-9_]/g, '_');
            
            // Construct URL (root + path from JSON)
            const fileUrl = window.location.origin + root + filePath;
            
            await conn.query(`
                CREATE OR REPLACE VIEW "${tableName}" AS 
                SELECT * FROM read_csv_auto('${fileUrl}');
            `);
            log(`View registered: ${tableName}`);
        }
        state.initialized = true;
    } catch (e) {
        console.error("Registration Failed:", e);
    }
}

// --- C. Render Table to HTML ---
function renderTable(arrowTable) {
    const mount = document.getElementById('result');
    if (!arrowTable || arrowTable.numRows === 0) {
        mount.innerHTML = '<p style="color:#666; font-style:italic;">No rows returned.</p>';
        return;
    }

    const fields = arrowTable.schema.fields.map(f => f.name);
    let html = `<table class="dataframe"><thead><tr>${fields.map(f => `<th>${f}</th>`).join('')}</tr></thead><tbody>`;

    const rows = arrowTable.toArray();
    const limit = 100; 
    const displayRows = rows.slice(0, limit); 
    
    displayRows.forEach(row => {
        html += "<tr>";
        fields.forEach(f => {
            html += `<td>${row[f] === null ? '' : row[f]}</td>`;
        });
        html += "</tr>";
    });
    
    html += "</tbody></table>";
    if(rows.length > limit) html += `<div style="font-size:0.8em; color:#666; margin-top:8px; text-align:right;">Showing first ${limit} of ${rows.length} rows.</div>`;
    mount.innerHTML = html;
}

// --- D. Main Execution (Run Button) ---
async function runSQL(ev) {
    ev?.preventDefault();
    const btn = document.getElementById('run');
    const status = document.getElementById('status');
    const resultDiv = document.getElementById('result');
    const sql = document.getElementById('sql').value;

    try {
        btn.disabled = true;
        status.textContent = 'Processing...';
        resultDiv.innerHTML = '<div style="color:#666;">⏳ Initializing DB & Running query...</div>';

        await ensureDB();
        await registerViews();

        const result = await state.conn.query(sql);
        renderTable(result);
        status.textContent = 'Done';
    } catch (err) {
        status.textContent = 'Error';
        resultDiv.innerHTML = `<div style="color:#b71c1c; background:#ffebee; padding:12px; border:1px solid #ef9a9a; border-radius:4px; font-family:monospace; font-size:0.9em;"><strong>❌ Error:</strong><br>${err.message}</div>`;
        console.error(err);
    } finally {
        btn.disabled = false;
    }
}

window.__runSQL__ = runSQL;
</script>

<style>
/* Clean Table CSS */
.dataframe { 
    border-collapse: collapse; 
    width: 100%; 
    font-size: 0.85rem; 
    margin-top: 5px; 
    box-shadow: 0 2px 4px rgba(0,0,0,0.05); 
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}
.dataframe th { 
    background: #f1f3f4; 
    position: sticky; 
    top: 0; 
    text-align: left; 
    font-weight: 600; 
    color: #444; 
    border-bottom: 2px solid #ddd;
    padding: 10px 12px;
}
.dataframe td { 
    border-bottom: 1px solid #eee; 
    padding: 8px 12px; 
    color: #333;
}
.dataframe tr:nth-child(even) { background: #fafafa; }
.dataframe tr:hover { background: #f5f5f5; }
</style>
