# SQL Lab — Query `publish/*.csv` with DuckDB-WASM

Run SQL **in your browser** against the portfolio CSVs. Each file under `publish/` is exposed as a **view** named by its file stem.

<div id="lab" style="margin:.5rem 0; position:relative; z-index:3;">
<p style="margin-bottom: 5px;"><strong>👉 Click "Run" or press Shift+Enter to execute.</strong></p>
<textarea id="sql" style="width:100%;height:160px;font-family:ui-monospace,monospace;padding:10px;border:1px solid #ccc;border-radius:4px;background:#f8f8f8;">
-- Top 10 Airports by Connectivity
SELECT 
    iata, 
    deg_total as total_routes
FROM airport_degree
ORDER BY total_routes DESC
LIMIT 10;
</textarea>
</div>

<p>
  <button id="run"
          type="button"
          class="md-button md-button--primary"
          style="padding:.45rem .9rem; cursor:pointer;"
          onclick="window.__runSQL__ && window.__runSQL__(event)">
    Run Query
  </button>
  <span id="status" style="margin-left:.6rem;color:#666;font-style:italic;">Ready</span>
</p>

<div id="result" style="margin-top:10px;overflow:auto;min-height:50px;border-top:1px solid #eee;padding-top:10px;"></div>

<script type="importmap">
{
  "imports": {
    "apache-arrow": "https://cdn.jsdelivr.net/npm/apache-arrow@14.0.2/+esm",
    "@duckdb/duckdb-wasm": "https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.29.0/dist/duckdb-browser.mjs"
  }
}
</script>

<script type="module">
// --- Konfigurasi & Helper ---
const log = (...a) => console.log('[sql_lab]', ...a);
const getSiteRoot = () => {
    const path = window.location.pathname;
    // Deteksi jika berjalan di subfolder GitHub Pages
    if (path.includes('/aviation-portfolio-pack/')) return '/aviation-portfolio-pack/';
    return '/';
};

const state = { conn: null, initialized: false };

// --- Fungsi 1: Siapkan Database ---
async function ensureDB() {
    if (state.conn) return state.conn;
    
    // Import langsung dari Import Map
    const duckdb = await import('@duckdb/duckdb-wasm');
    const bundles = duckdb.getJsDelivrBundles();
    const chosen = await duckdb.selectBundle(bundles);
    
    const workerUrl = URL.createObjectURL(
        new Blob([`importScripts("${chosen.mainWorker}");`], {type: 'text/javascript'})
    );
    
    const db = new duckdb.AsyncDuckDB(new duckdb.ConsoleLogger(), new Worker(workerUrl));
    await db.instantiate(chosen.mainModule, chosen.pthreadWorker);
    
    const conn = await db.connect();
    await conn.query('INSTALL httpfs; LOAD httpfs;'); // Penting untuk baca CSV remote
    state.conn = conn;
    return conn;
}

// --- Fungsi 2: Daftarkan CSV sebagai Tabel ---
async function registerViews() {
    if (state.initialized) return;
    const conn = await ensureDB();
    const root = getSiteRoot();
    
    try {
        // Ambil daftar file dari datasets.json
        const resp = await fetch(root + 'assets/datasets.json');
        if(!resp.ok) throw new Error("Gagal memuat assets/datasets.json");
        
        const data = await resp.json();
        const items = Array.isArray(data) ? data : (data.items || []);

        for (const item of items) {
            const file = item.file || item.path;
            if (!file || !file.endsWith('.csv')) continue;
            
            // Bersihkan nama file jadi nama tabel (misal: "data/file.csv" -> "file")
            const tableName = file.split('/').pop().replace('.csv', '').replace(/[^a-z0-9_]/g, '_');
            const fileUrl = window.location.origin + root + 'publish/' + file;
            
            await conn.query(`
                CREATE OR REPLACE VIEW "${tableName}" AS 
                SELECT * FROM read_csv_auto('${fileUrl}');
            `);
            log(`View registered: ${tableName}`);
        }
        state.initialized = true;
    } catch (e) {
        console.error("View Registration Error:", e);
        throw e;
    }
}

// --- Fungsi 3: Render Tabel HTML ---
function renderTable(arrowTable) {
    const mount = document.getElementById('result');
    if (!arrowTable || arrowTable.numRows === 0) {
        mount.innerHTML = '<p style="color:#666;">No rows returned.</p>';
        return;
    }

    // Ambil header
    const fields = arrowTable.schema.fields.map(f => f.name);
    let html = `<table class="dataframe"><thead><tr>${fields.map(f => `<th>${f}</th>`).join('')}</tr></thead><tbody>`;

    // Ambil data baris
    const rows = arrowTable.toArray();
    // Batasi display max 100 baris agar browser tidak crash
    const displayRows = rows.slice(0, 100); 
    
    displayRows.forEach(row => {
        html += "<tr>";
        fields.forEach(f => {
            html += `<td>${row[f] === null ? '' : row[f]}</td>`;
        });
        html += "</tr>";
    });
    
    html += "</tbody></table>";
    if(rows.length > 100) html += `<p style="font-size:0.8em; color:#666;">Showing first 100 of ${rows.length} rows.</p>`;
    mount.innerHTML = html;
}

// --- Fungsi Eksekusi (Dipanggil tombol Run) ---
async function runSQL(ev) {
    ev?.preventDefault();
    const btn = document.getElementById('run');
    const status = document.getElementById('status');
    const resultDiv = document.getElementById('result');
    const sql = document.getElementById('sql').value;

    try {
        btn.disabled = true;
        status.textContent = 'Processing...';
        resultDiv.innerHTML = '<div style="color:#666;">⏳ Running query...</div>';

        await ensureDB();
        await registerViews();

        const result = await state.conn.query(sql);
        renderTable(result);
        status.textContent = 'Done';
    } catch (err) {
        status.textContent = 'Error';
        resultDiv.innerHTML = `<div style="color:red; background:#fff0f0; padding:10px; border:1px solid red;"><strong>Error:</strong> ${err.message}</div>`;
        console.error(err);
    } finally {
        btn.disabled = false;
    }
}

// Expose ke global window agar tombol HTML bisa akses
window.__runSQL__ = runSQL;
</script>

<style>
/* Styling Tabel Sederhana */
.dataframe { border-collapse: collapse; width: 100%; font-size: 0.9rem; margin-top: 10px; }
.dataframe th { background: #eee; position: sticky; top: 0; text-align: left; font-weight: bold; }
.dataframe th, .dataframe td { border: 1px solid #ccc; padding: 6px 10px; }
.dataframe tr:nth-child(even) { background: #f9f9f9; }
</style>
