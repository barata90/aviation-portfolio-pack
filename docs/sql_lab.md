# SQL Lab — Diagnostic Mode

Script ini akan mengecek:
1. Apakah file `datasets.json` bisa dibaca?
2. Apakah URL CSV sudah benar?
3. Apakah DuckDB berhasil membuat tabel?

<div id="lab" style="margin:.5rem 0; position:relative; z-index:3;">
<p style="margin-bottom: 5px;"><strong>👉 Klik tombol di bawah untuk memulai diagnosa.</strong></p>
<button id="run" type="button" class="md-button md-button--primary" onclick="window.__runDiagnostic__()">
    Jalankan Diagnosa & Query
</button>
</div>

<div id="debug-log" style="background:#1e1e1e; color:#00ff00; font-family:monospace; padding:15px; margin-top:10px; border-radius:5px; height:300px; overflow:auto; white-space:pre-wrap;">
Waiting to start...
</div>

<div id="result" style="margin-top:10px;"></div>

<script type="importmap">
{
  "imports": {
    "apache-arrow": "https://cdn.jsdelivr.net/npm/apache-arrow@14.0.2/+esm",
    "@duckdb/duckdb-wasm": "https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.29.0/dist/duckdb-browser.mjs"
  }
}
</script>

<script type="module">
// --- HELPER LOGGING KE LAYAR ---
const logDiv = document.getElementById('debug-log');
function print(msg, type='info') {
    const color = type === 'error' ? '#ff4444' : (type === 'success' ? '#00cc00' : '#cccccc');
    logDiv.innerHTML += `<div style="color:${color}; margin-bottom:2px;">> ${msg}</div>`;
    logDiv.scrollTop = logDiv.scrollHeight;
    console.log(`[Diagnostic] ${msg}`);
}

// --- FUNGSI DIAGNOSA UTAMA ---
async function runDiagnostic() {
    logDiv.innerHTML = ''; // Reset log
    const btn = document.getElementById('run');
    btn.disabled = true;
    
    try {
        print("1. Memulai DuckDB-WASM...", 'info');
        
        // 1. Load DuckDB
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
        print("✅ DuckDB Siap.", 'success');

        // 2. Cek datasets.json
        print("2. Mencari file 'assets/datasets.json'...", 'info');
        
        // Coba deteksi path
        let root = window.location.pathname;
        if (root.includes('/sql_lab')) root = root.split('/sql_lab')[0] + '/';
        else if (!root.endsWith('/')) root += '/';
        
        // Fix untuk GitHub Pages jika ada di root domain atau subfolder
        // Kita coba paksa path relatif yang umum
        const jsonUrl = new URL('assets/datasets.json', window.location.href.replace('sql_lab/', '')).href;
        
        print(`   Mencoba fetch URL: ${jsonUrl}`);
        
        const resp = await fetch(jsonUrl);
        if (!resp.ok) throw new Error(`Gagal ambil datasets.json (Status: ${resp.status})`);
        
        const data = await resp.json();
        print(`✅ datasets.json ditemukan! Isi: ${JSON.stringify(data).substring(0, 100)}...`, 'success');

        // 3. Register Views
        const items = Array.isArray(data) ? data : (data.items || []);
        if (items.length === 0) print("⚠️ PERINGATAN: datasets.json kosong atau format salah.", 'error');

        for (const item of items) {
            const file = item.file || item.path;
            if (!file) continue;
            
            // Konstruksi URL CSV
            // Asumsi file path di JSON adalah relative terhadap root repo, misal "publish/airport_degree.csv"
            // Kita harus hati-hati menyusun URL penuhnya
            
            // Coba cleaning path agar tidak double slash
            const cleanRoot = jsonUrl.replace('assets/datasets.json', ''); 
            // Biasanya datasets.json ada di /assets/, file ada di /publish/
            // Jadi base-nya adalah parent dari assets/
            
            const csvUrl = cleanRoot + 'publish/' + file; 
            const tableName = file.split('/').pop().replace('.csv', '').replace(/[^a-z0-9_]/g, '_');
            
            print(`   Mendaftarkan view: ${tableName} -> ${csvUrl}`);
            
            try {
                await conn.query(`CREATE OR REPLACE VIEW "${tableName}" AS SELECT * FROM read_csv_auto('${csvUrl}');`);
            } catch (err) {
                print(`❌ Gagal register ${tableName}: ${err.message}`, 'error');
            }
        }

        // 4. Cek Tabel yang Terdaftar
        print("4. Mengecek daftar tabel di DuckDB...", 'info');
        const tables = await conn.query("SHOW TABLES;");
        
        if (tables.numRows === 0) {
            print("❌ TIDAK ADA TABEL YANG TERDAFTAR! Query pasti gagal.", 'error');
        } else {
            const tableNames = tables.toArray().map(r => r.name).join(', ');
            print(`✅ Tabel tersedia: ${tableNames}`, 'success');
            
            // 5. Jalankan Query Test
            print("5. Menjalankan Query Test (SELECT * FROM airport_degree LIMIT 5)...", 'info');
            const result = await conn.query("SELECT * FROM airport_degree LIMIT 5;");
            
            // Render Simple Table
            const mount = document.getElementById('result');
            const header = result.schema.fields.map(f=>`<th>${f.name}</th>`).join('');
            const rows = result.toArray().map(r => 
                `<tr>${result.schema.fields.map(f=>`<td>${r[f.name]}</td>`).join('')}</tr>`
            ).join('');
            
            mount.innerHTML = `<table border="1" style="border-collapse:collapse; width:100%;">${header}${rows}</table>`;
            print("✅ Query Berhasil ditampilkan di bawah!", 'success');
        }

    } catch (e) {
        print(`⛔ CRITICAL ERROR: ${e.message}`, 'error');
        console.error(e);
    } finally {
        btn.disabled = false;
    }
}

window.__runDiagnostic__ = runDiagnostic;
</script>
