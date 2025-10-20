#!/usr/bin/env python3
"""Small ERA5 example via CDS API.
Prereqs:
- Register & create ~/.cdsapirc (see: https://cds.climate.copernicus.eu/how-to-api)
- pip install cdsapi
This pulls hourly 2m temperature for a UAE bbox on a single day.
"""
import cdsapi, os

c = cdsapi.Client()
c.retrieve(
    'reanalysis-era5-single-levels',
    {
        'product_type': 'reanalysis',
        'variable': ['2m_temperature'],
        'date': '2025-08-01/2025-08-01',
        'time': [f"{h:02d}:00" for h in range(24)],
        'area': [30, 45, 20, 60],  # N, W, S, E (approx UAE region)
        'format': 'netcdf',
    },
    'data/era5/era5_t2m_uae_2025-08-01.nc'
)
