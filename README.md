# ✈️ Aviation Portfolio Pack
### *Automated Data Pipeline & Analytics Engine for Global Aviation Intelligence*

[![Deploy MkDocs to GitHub Pages](https://github.com/barata90/aviation-portfolio-pack/actions/workflows/pages.yml/badge.svg)](https://github.com/barata90/aviation-portfolio-pack/actions/workflows/pages.yml)
[![Data Quality](https://github.com/barata90/aviation-portfolio-pack/actions/workflows/data_quality.yml/badge.svg)](https://github.com/barata90/aviation-portfolio-pack/actions/workflows/data_quality.yml)

This repository is a production-grade **Data Engineering & Analytics** framework. It automates the collection, transformation, and modeling of real-world aviation datasets—turning raw files into BI-ready insights for network analysis, operational risk monitoring, and strategic planning.

---

## 🧭 Direct Access for Reviewers
If you are evaluating this project for an Analytics or Engineering role, please refer to the following:

* 📘 **Primary Case Study:** [Emirates — Data Analytics Specialist Case Study](docs/case_studies/emirates_data_analytics_specialist.md)
* 🧭 **Data Catalog:** [Comprehensive Data Dictionary & Lineage](docs/data_dictionary.md)
* 📊 **Quality Report:** [Automated Data Integrity Validation](docs/quality_report.md)
* 🌐 **Live Documentation:** [Visit the Project Microsite](https://barata90.github.io/aviation-portfolio-pack/)

---

## 🛠️ Technical Ecosystem
A lightweight yet scalable stack designed for speed and reliability:

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Engine** | Python 3.13 | Core ETL logic and automation scripts. |
| **Database** | DuckDB (In-Process) | High-performance OLAP for SQL-based transformations. |
| **Workflow** | Bash & GitHub Actions | Automated data fetching and CI/CD pipelines. |
| **Storage** | Parquet / CSV | Interoperable "Gold Layer" files ready for BI tools. |
| **DWH** | Snowflake (DDL ready) | Enterprise-ready data warehouse schemas and loading scripts. |
| **Reporting** | Power BI / MkDocs | Interactive dashboards and automated documentation. |

---

## 📂 Architecture & Structure
```text
aviation_portfolio_pack/
├─ scripts/            # ETL logic (Python, DuckDB, SQL)
├─ data/
│  ├─ openflights/     # Global airport, airline, and route networks
│  ├─ eurocontrol/     # Operational ATFM delay datasets
│  └─ derived/         # Modeled "Analytical" layer
├─ publish/            # Final "BI-ready" exports
├─ warehouse_local/    # Embedded DuckDB instance
└─ docs/               # Technical documentation & business case studies

---

## Getting Started
Execute the following commands to replicate the pipeline on your local machine (macOS/Linux/WSL):

### 1. Environment Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip -r requirements.txt

### 2. Trigger ETL & Data Capture
This script fetches real-world data from OpenFlights, EUROCONTROL, and OpenSky:
chmod +x get_data.sh
bash ./get_data.sh

### 3. Build the Analytics Model
Run the transformation engine to generate the BI-ready datasets and documentation:
python scripts/make_data_dictionary.py \
  --csv-dir publish \
  --duckdb warehouse_local/otp.duckdb

---

## Analytical Outputs

| Dataset | Key Metrics | Strategic Value |
| :--- | :--- | :--- |
| **airport_degree.csv** | In/Out/Total Degree | Identifying Hub & Spoke nodes and network vulnerabilities. |
| **euro_atfm_timeseries** | Daily Delay Minutes | Seasonal trend analysis for On-Time Performance (OTP). |
| **route_counts.csv** | Route Frequency | Market density analysis for specific Origin-Destination (OD) pairs. |
| **dim_airport_clean** | Coordinates & IATA | Geospatial master data for mapping and network visualization. |
