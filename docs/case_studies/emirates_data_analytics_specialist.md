# Case Study — Emirates: Data Analytics Specialist

[![Build dictionary](https://github.com/barata90/aviation-portfolio-pack/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/barata90/aviation-portfolio-pack/actions/workflows/build.yml)
[![Deploy site](https://github.com/barata90/aviation-portfolio-pack/actions/workflows/pages.yml/badge.svg?branch=main)](https://github.com/barata90/aviation-portfolio-pack/actions/workflows/pages.yml)
[![Data Quality](https://github.com/barata90/aviation-portfolio-pack/actions/workflows/data_quality.yml/badge.svg?branch=main)](https://github.com/barata90/aviation-portfolio-pack/actions/workflows/data_quality.yml)

**Tujuan:** demo kemampuan end-to-end yang relevan untuk Emirates — *capture → model → quality → catalog → publish → BI → (opsional) warehouse*.

---

## 1) Ringkasan Eksekutif

- **Use cases utama**
  - *Ops Delay Watch (EUROCONTROL)*: tren 24 bulan, YoY/MoM, lokasi penyumbang tertinggi.
  - *Network Strength (OpenFlights)*: hub sentral (degree tinggi), OD pairs teratas.
- **Deliverables**
  - **Catalog & Dictionary** otomatis: [Data Dictionary](../data_dictionary.md) + [Quality Report](../quality_report.md).
  - **Dataset siap-BI**: CSV di `publish/` (tidak perlu ODBC; cocok untuk Power BI & MicroStrategy).
  - **Situs & CI/CD**: MkDocs + GitHub Pages; build otomatis; tanggal revisi git terlokalisasi (ID).
  - **Warehouse (opsional)**: loader Snowflake **manual** dengan auto-skip bila rahasia tidak ada (workflow tetap hijau).

---

## 2) Dataset & Periode

Sumber data: folder `publish/`. Setiap halaman dataset menampilkan **periode data asli** dan **periode tampilan** (default **24 bulan terakhir** bila ada kolom tanggal).

- [Euro ATFM Timeseries](../pages/euro_atfm_timeseries.md) — `period_start`, `delay_minutes`  
- [Euro ATFM By Location](../pages/euro_atfm_by_location.md) — `location`, `delay_minutes`  
- [Airport Degree](../pages/airport_degree.md) — `deg_out`, `deg_in`, `deg_total`  
- [Top OD Pairs](../pages/top_od_pairs.md) — `src_iata`, `dst_iata`, `num_routes`

> Penyaringan 24 bulan dihitung relatif ke **tanggal maksimum di data**, bukan “hari ini”, sehingga konsisten walau dataset statis.

---

## 3) Arsitektur & Operasional

CSV (publish/) ──┬──▶ Data Quality (report → docs/quality_report.md)
├──▶ Data Dictionary (docs/data_dictionary.md)
└──▶ Build Docs (dataset pages + charts) ─▶ MkDocs ─▶ GitHub Pages
└──(opsional) Snowflake Loader (manual)


- **Build dictionary**: hanya jalan jika `publish/*.csv` ada; kalau tidak ada → **skip** bersih.
- **Snowflake loader**: trigger **manual**; jika secrets tidak ada → **precheck** menandai run **Success** dan job utama **skip**.

---

## 4) KPI & Insight (siap dashboard)

### 4.1 Ops Delay (EUROCONTROL)
- **KPI**: `Total Delay 12M`, `YoY %`, `MoM %`, `Top 10 Locations`.
- **Navigasi cepat**:
  - Tren 24 bulan: buka [Euro ATFM Timeseries](../pages/euro_atfm_timeseries.md)
  - Peringkat lokasi: buka [Euro ATFM By Location](../pages/euro_atfm_by_location.md)

### 4.2 Network Strength (OpenFlights)
- **KPI**: `Top-20 Airport Degree`, `Top OD pairs`.
- **Navigasi cepat**:
  - Degree: [Airport Degree](../pages/airport_degree.md)
  - OD: [Top OD Pairs](../pages/top_od_pairs.md)

---

## 5) BI — Power BI & MicroStrategy

### 5.1 Power BI (ringkas)
Buat **Date table** dan measures berikut untuk tren 12–24 bulan.

```DAX
Date =
  ADDCOLUMNS(
    CALENDAR(DATE(2015,1,1), TODAY()),
    "Year", YEAR([Date]),
    "Month", FORMAT([Date], "YYYY-MM"),
    "Month Start", STARTOFMONTH([Date])
  )

Delay Minutes = SUM ( 'euro_atfm_timeseries'[delay_minutes] )

Delay 12M Rolling :=
VAR CurrentDate = MAX ( 'Date'[Date] )
RETURN CALCULATE ( [Delay Minutes], DATESINPERIOD ( 'Date'[Date], CurrentDate, -12, MONTH ) )

Delay MoM % :=
VAR Curr = CALCULATE ( [Delay Minutes], 'Date'[Date] = MAX ( 'Date'[Month Start] ) )
VAR Prev = CALCULATE ( [Delay Minutes], DATEADD ( 'Date'[Date], -1, MONTH ) )
RETURN DIVIDE ( Curr - Prev, Prev )

Delay YoY % :=
VAR Curr = CALCULATE ( [Delay Minutes], 'Date'[Year] = MAX ( 'Date'[Year] ) )
VAR Prev = CALCULATE ( [Delay Minutes], 'Date'[Year] = MAX ( 'Date'[Year] ) - 1 )
RETURN DIVIDE ( Curr - Prev, Prev )

Visual: area/line (24 bulan), card (Last Month), KPI (12M rolling), slicer Year/Month.

5.2 MicroStrategy (outline)

Attributes: Year, Month, Airport (IATA), Country.

Metrics: Delay Minutes, Delay 12M Rolling, Deg Out, Deg In, Deg Total.

Documents: Ops Overview (KPI + tren) → drill ke Locations & Routes.

6) Ingestion ke Snowflake (opsional, demo)

CLI Python: scripts/load_to_snowflake.py memuat CSV. Workflow manual dengan auto-skip bila secrets tidak ada (run hijau).

DDL ringkas:

CREATE DATABASE IF NOT EXISTS AV_PORTFOLIO;
CREATE SCHEMA IF NOT EXISTS AV_PORTFOLIO.RAW;
CREATE OR REPLACE TABLE RAW.EURO_ATFM_TIMESERIES (PERIOD_START DATE, DELAY_MINUTES DOUBLE);
CREATE OR REPLACE TABLE RAW.EURO_ATFM_BY_LOCATION (LOCATION STRING, DELAY_MINUTES DOUBLE);
CREATE OR REPLACE TABLE RAW.AIRPORT_DEGREE (IATA STRING, DEG_OUT INT, DEG_IN INT, DEG_TOTAL INT);
CREATE OR REPLACE TABLE RAW.ROUTE_COUNTS (SRC_IATA STRING, DST_IATA STRING, NUM_ROUTES INT);7) Data Quality & Governance

Quality Report: docs/quality_report.md
 — null %, tipe, min/max, duplikat.

Freshness (opsional): tandai dataset “stale” jika max(date) > 45 hari dari build.

UAT: ceklis & kriteria keberterimaan → UAT Checklist
.

Metadata: owner, PII flag, update cadence terdokumentasi di Data Dictionary.

8) Cara Reproduksi (lokal)
python3 -m venv .venv && source .venv/bin/activate
pip install -U pip -r requirements.txt
chmod +x get_data.sh scripts/*.py
bash get_data.sh                                 # ambil & siapkan dataset
python scripts/make_data_dictionary.py --csv-dir publish --out docs/data_dictionary.md
mkdocs build --strict && mkdocs serve            # lihat lokal

