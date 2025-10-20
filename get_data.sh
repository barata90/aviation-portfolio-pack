#!/usr/bin/env bash
set -euo pipefail

mkdir -p data/{openflights,opensky,eurocontrol,uk_caa,noaa_isd,asrs,era5}

echo "== OpenFlights (airports/airlines/routes) =="
curl -L -o data/openflights/airports.dat https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat
curl -L -o data/openflights/airlines.dat https://raw.githubusercontent.com/jpatokal/openflights/master/data/airlines.dat
curl -L -o data/openflights/routes.dat   https://raw.githubusercontent.com/jpatokal/openflights/master/data/routes.dat

echo "== EUROCONTROL ATFM delays (2024 annual) =="
curl -L -o data/eurocontrol/RP3_ERT_ATFM_2024_Jan_Dec.xlsx https://www.eurocontrol.int/prudata/dashboard/download/2024/RP3_ERT_ATFM_2024_Jan_Dec.xlsx

echo "== OpenSky sample near Dubai (real-time states) =="
python3 scripts/opensky_sample.py

echo "Done. Optional: run NOAA ISD downloader & ERA5 request script as needed."
