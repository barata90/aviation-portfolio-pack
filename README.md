> **For Emirates reviewers:**  
> - 📘 Case study: [Emirates — Data Analytics Specialist](docs/case_studies/emirates_data_analytics_specialist.md)  
> - 🧭 Data catalog: [Data Dictionary](docs/data_dictionary.md) • [Quality Report](docs/quality_report.md)  
> - 🌐 Live site: https://barata90.github.io/aviation-portfolio-pack/

[[![Build data dictionary](https://github.com/barata90/aviation-portfolio-pack/actions/workflows/build.yml)
[![Deploy site](https://github.com/barata90/aviation-portfolio-pack/actions/workflows/pages.yml/badge.svg)](…/actions/workflows/pages.yml)
[![Data Quality](https://github.com/barata90/aviation-portfolio-pack/actions/workflows/data_quality.yml/badge.svg)](…/actions/workflows/data_quality.yml)


# Aviation Portfolio Data Pack

This pack to **collect real aviation datasets in minutes** :
- OpenFlights (airports/airlines/routes) – for networks & geocoding
- EUROCONTROL ATFM delays (2024 annual) – for operations/capacity analysis
- OpenSky real-time sample (states near Dubai) – for live tracking flavor
- NOAA ISD weather (scripted, by ICAO & year) – for weather/OTP studies

> **How to use (macOS/Linux/WSL):**
1) Open Terminal and cd to the folder where you downloaded this zip.
2) Run: `bash get_data.sh`
3) (Optional weather) Run: `python3 scripts/download_isd.py --icaos OMDB EGLL --year 2025`
4) Explore the data folder. If you use DuckDB: `duckdb :memory: -c ".read scripts/duckdb_setup.sql"`

**Notes**
- EUROCONTROL file is a public download (annual 2024). 2025 YTD files are available on their site.
- UK CAA punctuality CSV is not auto-downloaded (links change); visit their 2025 page and download monthly CSV(s) that you want, then drop them into `data/uk_caa/`.
- ERA5 (Copernicus) requires a free CDS API key. See `scripts/era5_request.py` and their docs.
- NASA ASRS has a web UI for custom CSV exports. Save outputs into `data/asrs/`.

# Aviation Analytics Portfolio — Emirates Data Analytics Specialist

**TL;DR**
- ETL ringan dengan **Python + DuckDB** dari OpenFlights & EUROCONTROL
- Model **network** (route OD, airport degree) & **ops delay** (ATFM timeseries / location)
- Output **CSV siap-BI** (`publish/`) → di-*plug* ke **Power BI** / **MicroStrategy**
- Contoh DDL & COPY ke **Snowflake** untuk warehousing

---

## 1) Stack
- Runtime: Python 3.13, Virtualenv
- Data engine: DuckDB (embedded SQL)
- Lib: `pandas`, `duckdb`, `openpyxl`
- BI: Power BI / MicroStrategy (upload CSV)
- (Opsional) DWH: Snowflake

## 2) Struktur Folder
aviation_portfolio_pack/
├─ README.md
├─ get_data.sh
├─ scripts/
│ ├─ opensky_sample.py
│ ├─ duckdb_setup.sql
│ └─ make_data_dictionary.py # <— script yang membuat data dictionary (dibuat di langkah ini)
├─ data/
│ ├─ openflights/ # airports.dat, airlines.dat, routes.dat
│ ├─ eurocontrol/ # RP3_ERT_ATFM_2024_Jan_Dec.xlsx
│ └─ derived/ # hasil transform
├─ warehouse_local/
│ └─ otp.duckdb # database DuckDB lokal
└─ publish/ # CSV final untuk BI (copy dari data/derived)


## 3) Quickstart
```bash
# 0) (opsional) venv
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip pandas duckdb openpyxl

# 1) Ambil data (OpenFlights, EUROCONTROL subset, OpenSky sample)
chmod +x get_data.sh scripts/*.py
bash ./get_data.sh

# 2) Bangun DuckDB + turunan (jalanin snippet SQL/Python yang sudah kamu pakai)
#    Hasil utamanya tersimpan di data/derived:
#      - route_counts.csv
#      - dim_airport_clean.csv
#      - airport_degree.csv
#      - top_od_pairs.csv
#      - euro_atfm_timeseries.csv
#      - euro_atfm_by_location.csv

# 3) Rapikan untuk BI
mkdir -p publish
cp -f data/derived/{route_counts.csv,dim_airport_clean.csv,airport_degree.csv,top_od_pairs.csv,euro_atfm_timeseries.csv,euro_atfm_by_location.csv} publish/

# 4) (Opsional) Buat Data Dictionary
python scripts/make_data_dictionary.py \
  --csv-dir publish \
  --duckdb warehouse_local/otp.duckdb \
  --tables route_counts,airport_degree,euro_atfm_timeseries,euro_atfm_by_location \
  --out docs/data_dictionary.md

4) Dataset Utama
Network (OpenFlights)

route_counts.csv — jumlah varian rute per pasangan origin–destination
Kolom: src_iata, dst_iata, num_routes

airport_degree.csv — degree per bandara (out/in/total)
Kolom: iata, deg_out, deg_in, deg_total

dim_airport_clean.csv — dimensi bandara (nama, kota, negara, koordinat)

top_od_pairs.csv — 100 OD dengan num_routes terbesar

Ops Delay (EUROCONTROL)

euro_atfm_timeseries.csv — time series en-route ATFM delay
Kolom: period_start (date), delay_minutes (double)

euro_atfm_by_location.csv — total delay per lokasi/ANSP
Kolom: location, delay_minutes

Catatan sumber & lisensi:

OpenFlights (airports/airlines/routes) — data publik (atribusi: OpenFlights)

EUROCONTROL PRU — ringkasan indikator publik (untuk tujuan edukasi/portfolio)

5) Power BI / MicroStrategy (ringkas)

Power BI

Upload publish/*.csv.

Halaman:

Ops Overview: Cards (Total/Avg Delay), Line period_start vs delay_minutes, Table Top location.

Airport Network: Matrix src_iata × dst_iata = num_routes, Map iata bubble dari airport_degree.

Disruption Watch: Bar location vs delay_minutes, slicer location.

MicroStrategy

New → Add External Data → upload CSV → Dossier 2 halaman (Overview & Network).

6) Snowflake (opsional)
CREATE DATABASE IF NOT EXISTS AV_PORTFOLIO;
CREATE SCHEMA IF NOT EXISTS AV_PORTFOLIO.RAW;

CREATE OR REPLACE TABLE RAW.EURO_ATFM_TIMESERIES (PERIOD_START DATE, DELAY_MINUTES DOUBLE);
CREATE OR REPLACE TABLE RAW.EURO_ATFM_BY_LOCATION (LOCATION STRING, DELAY_MINUTES DOUBLE);
CREATE OR REPLACE TABLE RAW.AIRPORT_DEGREE (IATA STRING, DEG_OUT INT, DEG_IN INT, DEG_TOTAL INT);
CREATE OR REPLACE TABLE RAW.ROUTE_COUNTS (SRC_IATA STRING, DST_IATA STRING, NUM_ROUTES INT);

CREATE OR REPLACE STAGE RAW.CSV_STAGE FILE_FORMAT=(TYPE=CSV SKIP_HEADER=1 FIELD_OPTIONALLY_ENCLOSED_BY='"');

-- PUT file://publish/*.csv @RAW.CSV_STAGE AUTO_COMPRESS=TRUE;  -- jalankan dari SnowSQL/Worksheet

COPY INTO RAW.EURO_ATFM_TIMESERIES      FROM @RAW.CSV_STAGE/euro_atfm_timeseries.csv;
COPY INTO RAW.EURO_ATFM_BY_LOCATION     FROM @RAW.CSV_STAGE/euro_atfm_by_location.csv;
COPY INTO RAW.AIRPORT_DEGREE            FROM @RAW.CSV_STAGE/airport_degree.csv;
COPY INTO RAW.ROUTE_COUNTS              FROM @RAW.CSV_STAGE/route_counts.csv;

7) What I Demonstrate (untuk recruiter)

Data capture & QC (XLSX → normalisasi → SQLable)

Data modeling (network degree, OD matrix, ops delay)

Self-service BI (dashboard & slicer)

Warehousing mindset (Snowflake DDL, load)

Governance (struktur folder, dictionary otomatis)
