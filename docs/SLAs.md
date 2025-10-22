# Data Reliability — SLI/SLO

**SLI** yang dipantau:
- Freshness: selisih hari antara `max(date_column)` dan waktu build.
- Schema drift: kolom hilang/tambahan terhadap kontrak.
- Null ratio: proporsi null pada kolom kunci.
- Uniqueness: duplikat pada primary key.
- Range: nilai di luar domain/angka negatif.

**SLO (default):**
- Freshness ≤ `freshness_max_lag_days` (lihat governance/datasets.yml)
- Nulls pada kolom kunci = 0%
- Uniqueness pelanggaran = 0
- Range: 0 baris negatif untuk metrik kumulatif

**Escalation**
- 🔴 ERROR → opsional mem-fail DQ (`--fail-on=error`) agar Pages/loader tidak jalan.
- 🟠 WARN → publikasi tetap jalan, tapi diberi badge di report.
