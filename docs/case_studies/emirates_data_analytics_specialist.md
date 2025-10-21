# Case Study — Emirates: Data Analytics Specialist

**Tujuan:** demo kemampuan end-to-end: capture → model → DQ → publish → dashboard.

## Dataset & Periode
- Sumber: folder `publish/`
- Periode tiap dataset (otomatis dari generator):
  - Ditampilkan pada header masing-masing halaman dataset.
  - Default tampilan grafik: **2 tahun terakhir**.

## Produk yang di-deliver
1. **Data Catalog & Dictionary**
   - `docs/data_dictionary.md` (otomatis) + ringkasan kolom per tabel.
   - `docs/quality_report.md` (otomatis) — null %, type, min/max, duplikat.

2. **Dashboards (prototype)**
   - *Power BI*: 
     - Measures:
       ```DAX
       Delay Minutes = SUM('euro_atfm_timeseries'[delay_minutes])
       Month = STARTOFMONTH('Date'[Date])
       Delay 12M Rolling =
         VAR CurrentDate = MAX('Date'[Date])
         RETURN CALCULATE([Delay Minutes],
           DATESINPERIOD('Date'[Date], CurrentDate, -12, MONTH))
       ```
     - Visual: area chart (Delay Minutes), card (Last Month), KPI (12M rolling), slicer Tahun/Bulan.
     - Date table:
       ```DAX
       Date = ADDCOLUMNS(
         CALENDAR(DATE(2015,1,1), TODAY()),
         "Year", YEAR([Date]), "Month", FORMAT([Date], "YYYY-MM")
       )
       ```
   - *MicroStrategy (outline)*:
     - **Attributes**: Year, Month, Airport, Country.
     - **Metrics**: Delay Minutes, Delay 12M Rolling, Deg Out/In/Total.
     - **Documents**: Landing KPI + Drill to Route/Station.

3. **Ingestion ke Snowflake (demo)**
   - Python `scripts/load_to_snowflake.py` → buat schema & load CSV dengan `write_pandas`.
   - Tersedia SQL contoh untuk view materialized & role-based access.

4. **UAT & Governance**
   - `docs/uat_checklist.md`: skenario UAT, acceptance criteria.
   - Metadata/owners/PII flag tercermin di catalog dan dictionary.

## Operasional & Keandalan
- **CI Pages** build otomatis saat ada update data/docs.
- **Data Quality** job jalan di push ke `publish/**` dan commit report ke docs (memicu redeploy site).
- Badge status DQ & Pages ditampilkan di README.

> Link: halaman ini merupakan ringkasan yang mengantar reviewer ke artefak yang relevan (data, kualitas, dan contoh dashboard).
