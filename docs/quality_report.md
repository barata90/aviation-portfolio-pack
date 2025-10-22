# Data Quality Report — overall: 🟠 WARN

Generated: 2025-10-22 02:14 UTC

| Dataset               | Owner    |   Rows | Status   |   Errors |   Warnings | File                                | MD5      |
|:----------------------|:---------|-------:|:---------|---------:|-----------:|:------------------------------------|:---------|
| euro_atfm_timeseries  | barata90 |     72 | 🟢 OK     |        0 |          0 | `publish/euro_atfm_timeseries.csv`  | 4846e12e |
| euro_atfm_by_location | barata90 |     28 | 🟢 OK     |        0 |          1 | `publish/euro_atfm_by_location.csv` | 4e9c242a |
| airport_degree        | barata90 |   3425 | 🟢 OK     |        0 |          0 | `publish/airport_degree.csv`        | fe76e229 |
| route_counts          | barata90 |  37595 | 🟢 OK     |        0 |          0 | `publish/route_counts.csv`          | b430349b |
| top_od_pairs          | barata90 |    100 | 🟢 OK     |        0 |          0 | `publish/top_od_pairs.csv`          | 1988bd25 |

### euro_atfm_timeseries 🟢

- Path: `publish/euro_atfm_timeseries.csv`  
- Owner: barata90  
- Rows: 72  
- PII: False  
- Cadence: monthly

- No issues detected.


### euro_atfm_by_location 🟢

- Path: `publish/euro_atfm_by_location.csv`  
- Owner: barata90  
- Rows: 28  
- PII: False  
- Cadence: monthly

- 🟠 delay_minutes out-of-range rows: 11


### airport_degree 🟢

- Path: `publish/airport_degree.csv`  
- Owner: barata90  
- Rows: 3425  
- PII: False  
- Cadence: static

- No issues detected.


### route_counts 🟢

- Path: `publish/route_counts.csv`  
- Owner: barata90  
- Rows: 37595  
- PII: False  
- Cadence: static

- No issues detected.


### top_od_pairs 🟢

- Path: `publish/top_od_pairs.csv`  
- Owner: barata90  
- Rows: 100  
- PII: False  
- Cadence: static

- No issues detected.

