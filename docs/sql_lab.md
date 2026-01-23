# SQL Lab — Aviation Portfolio

<div id="lab" style="margin:1rem 0;">
    <textarea id="sql" style="width:100%;height:120px;font-family:monospace;padding:10px;border-radius:4px;border:1px solid #ddd;">
SELECT iata, deg_total FROM airport_degree ORDER BY deg_total DESC LIMIT 10;
    </textarea>
    <div style="margin-top:10px;">
        <button id="run" class="md-button md-button--primary" onclick="runSQL()">Run Query</button>
        <span id="status" style="margin-left:10px; color:gray;">Ready</span>
    </div>
</div>

<div id="result" style="overflow:auto; border-top:1px solid #eee; margin-top:15px;"></div>

<script type="module">
    // Konfigurasi Dasar
    const siteRoot = window.location.pathname.includes('/aviation-portfolio-pack/') ? '/aviation-portfolio-pack/' : '/';
    let db, conn;

    // 1. Inisialisasi DuckDB & Registrasi Tabel sekaligus
    async function initDB() {
        if (conn) return conn;
        const duckdb = await import('https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.29.0/dist/duckdb-browser.mjs');
        const bundle = await duckdb.selectBundle(duckdb.getJsDelivrBundles());
        
        const worker = new Worker(URL.createObjectURL(new Blob([`importScripts("${bundle.mainWorker}");`], {type: 'text/javascript'})));
        db = new duckdb.AsyncDuckDB(new duckdb.ConsoleLogger(), worker);
        await db.instantiate(bundle.mainModule);
        conn = await db.connect();
        await conn.query('INSTALL httpfs; LOAD httpfs;');

        // Registrasi otomatis dari datasets.json
        const ds = await (await fetch(`${siteRoot}assets/datasets.json`)).json();
        for (const it of (ds.items || ds)) {
            const name = it.file.replace('.csv', '').replace(/[^a-z0-9_]/g, '_');
            await conn.query(`CREATE OR REPLACE VIEW "${name}" AS SELECT * FROM read_csv_auto('${window.location.origin}${siteRoot}publish/${it.file}')`);
        }
        return conn;
    }

    // 2. Fungsi Eksekusi
    window.runSQL = async () => {
        const btn = document.getElementById('run');
        const status = document.getElementById('status');
        try {
            btn.disabled = true; status.textContent = 'Processing...';
            const c = await initDB();
            const res = await c.query(document.getElementById('sql').value);
            
            // Render Tabel
            const headers = res.schema.fields.map(f => f.name);
            let html = `<table class="df"><thead><tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr></thead><tbody>`;
            res.toArray().forEach(row => {
                html += `<tr>${headers.map(h => `<td>${row[h] ?? ''}</td>`).join('')}</tr>`;
            });
            document.getElementById('result').innerHTML = html + '</tbody></table>';
            status.textContent = 'Done';
        } catch (e) {
            document.getElementById('result').innerHTML = `<pre style="color:red;">${e.message}</pre>`;
            status.textContent = 'Error';
        } finally { btn.disabled = false; }
    };

    // Auto-load saat halaman dibuka
    initDB().then(() => document.getElementById('status').textContent = 'Database Loaded');
</script>

<style>
    .df { border-collapse: collapse; width: 100%; font-size: 0.85rem; }
    .df th, .df td { border: 1px solid #ddd; padding: 6px; text-align: left; }
    .df th { background: #f8f9fa; position: sticky; top: 0; }
</style>
