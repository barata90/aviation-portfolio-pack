# Data Dictionary

_Generated: 2025-10-22 00:52_

Dokumen ini berisi ringkasan struktur & statistik kolom untuk dataset yang dipakai di portfolio.

---
### airport_degree.csv

- **Source**: CSV: publish/airport_degree.csv
- **Rows**: 3425

**Preview (first 5 rows)**

| iata   |   deg_out |   deg_in |   deg_total |
|:-------|----------:|---------:|------------:|
| FRA    |       239 |      238 |         477 |
| CDG    |       237 |      233 |         470 |
| AMS    |       232 |      231 |         463 |
| IST    |       227 |      230 |         457 |
| ATL    |       217 |      216 |         433 |

|   # | Column    | DuckDB Type   |   Nulls |   Distinct | Min   | Max   | Mean/Examples                               |
|----:|:----------|:--------------|--------:|-----------:|:------|:------|:--------------------------------------------|
|   1 | iata      | VARCHAR       |       0 |       3425 |       |       | AAE (1); AAL (1); AAN (1); AAQ (1); AAR (1) |
|   2 | deg_out   | BIGINT        |       0 |        143 | 0.0   | 239.0 | 10.9766                                     |
|   3 | deg_in    | BIGINT        |       0 |        143 | 0.0   | 238.0 | 10.9766                                     |
|   4 | deg_total | BIGINT        |       0 |        224 | 1.0   | 477.0 | 21.9533                                     |


### dim_airport_clean.csv

- **Source**: CSV: publish/dim_airport_clean.csv
- **Rows**: 6072

**Preview (first 5 rows)**

| iata   | icao   | airport_name                                | city         | country          |      lat |     lon | tz                   |
|:-------|:-------|:--------------------------------------------|:-------------|:-----------------|---------:|--------:|:---------------------|
| GKA    | AYGA   | Goroka Airport                              | Goroka       | Papua New Guinea | -6.08169 | 145.392 | Pacific/Port_Moresby |
| MAG    | AYMD   | Madang Airport                              | Madang       | Papua New Guinea | -5.20708 | 145.789 | Pacific/Port_Moresby |
| HGU    | AYMH   | Mount Hagen Kagamuga Airport                | Mount Hagen  | Papua New Guinea | -5.82679 | 144.296 | Pacific/Port_Moresby |
| LAE    | AYNZ   | Nadzab Airport                              | Nadzab       | Papua New Guinea | -6.5698  | 146.726 | Pacific/Port_Moresby |
| POM    | AYPY   | Port Moresby Jacksons International Airport | Port Moresby | Papua New Guinea | -9.44338 | 147.22  | Pacific/Port_Moresby |

|   # | Column       | DuckDB Type   |   Nulls |   Distinct | Min            | Max               | Mean/Examples                                                                                                         |
|----:|:-------------|:--------------|--------:|-----------:|:---------------|:------------------|:----------------------------------------------------------------------------------------------------------------------|
|   1 | iata         | VARCHAR       |       0 |       6072 |                |                   | AAA (1); AAC (1); AAE (1); AAF (1); AAH (1)                                                                           |
|   2 | icao         | VARCHAR       |       0 |       6072 |                |                   | 03N (1); 07FA (1); 5A8 (1); AGAF (1); AGAR (1)                                                                        |
|   3 | airport_name | VARCHAR       |       0 |       6046 |                |                   | Capital City Airport (3); Newcastle Airport (3); San Pedro Airport (3); Santa Maria Airport (3); Bathurst Airport (2) |
|   4 | city         | VARCHAR       |      39 |       5602 |                |                   | None (39); London (7); San Jose (7); Columbus (6); Greenville (6)                                                     |
|   5 | country      | VARCHAR       |       0 |        235 |                |                   | United States (1251); Canada (380); Australia (282); China (235); Brazil (210)                                        |
|   6 | lat          | DOUBLE        |       0 |       6062 | -62.1907997131 | 82.51779937740001 | 24.1943                                                                                                               |
|   7 | lon          | DOUBLE        |       0 |       6064 | -179.876998901 | 179.951004028     | -1.8330                                                                                                               |
|   8 | tz           | VARCHAR       |     557 |        306 |                |                   | None (557); America/New_York (367); America/Chicago (297); Asia/Shanghai (185); America/Anchorage (168)               |


### euro_atfm_by_location.csv

- **Source**: CSV: publish/euro_atfm_by_location.csv
- **Rows**: 28

**Preview (first 5 rows)**

| location            |   delay_minutes |
|:--------------------|----------------:|
| HungaroControl (EC) |            2.64 |
| Croatia Control     |            1.34 |
| DFS + MUAC-DE       |            1.3  |
| DSNA                |            1.14 |
| ENAIRE              |            0.83 |

|   # | Column        | DuckDB Type   |   Nulls |   Distinct | Min   | Max   | Mean/Examples                                                                             |
|----:|:--------------|:--------------|--------:|-----------:|:------|:------|:------------------------------------------------------------------------------------------|
|   1 | location      | VARCHAR       |       0 |         28 |       |       | ANS CR (1); AirNav Ireland (1); Austro Control (1); Avinor Flysikring AS (1); BULATSA (1) |
|   2 | delay_minutes | DOUBLE        |       0 |         23 | -0.14 | 2.64  | 0.3307                                                                                    |


### euro_atfm_timeseries.csv

- **Source**: CSV: publish/euro_atfm_timeseries.csv
- **Rows**: 72

**Preview (first 5 rows)**

| period_start        |   delay_minutes |
|:--------------------|----------------:|
| 2019-01-01 00:00:00 |               1 |
| 2019-02-01 00:00:00 |               1 |
| 2019-03-01 00:00:00 |               1 |
| 2019-04-01 00:00:00 |               1 |
| 2019-05-01 00:00:00 |               1 |

|   # | Column        | DuckDB Type   |   Nulls |   Distinct | Min                 | Max                 | Mean/Examples   |
|----:|:--------------|:--------------|--------:|-----------:|:--------------------|:--------------------|:----------------|
|   1 | period_start  | DATE          |       0 |         72 | 2019-01-01 00:00:00 | 2024-12-01 00:00:00 |                 |
|   2 | delay_minutes | DOUBLE        |       0 |          1 | 1.0                 | 1.0                 | 1.0000          |


### route_counts.csv

- **Source**: CSV: publish/route_counts.csv
- **Rows**: 37595

**Preview (first 5 rows)**

| src_iata   | dst_iata   |   num_routes |
|:-----------|:-----------|-------------:|
| EGO        | KZN        |            1 |
| LED        | KZN        |            3 |
| IKT        | BTK        |            1 |
| IKT        | ULK        |            3 |
| IQT        | TPP        |            2 |

|   # | Column     | DuckDB Type   |   Nulls |   Distinct | Min   | Max   | Mean/Examples                                         |
|----:|:-----------|:--------------|--------:|-----------:|:------|:------|:------------------------------------------------------|
|   1 | src_iata   | VARCHAR       |       0 |       3409 |       |       | FRA (239); CDG (237); AMS (232); IST (227); ATL (217) |
|   2 | dst_iata   | VARCHAR       |       0 |       3418 |       |       | FRA (238); CDG (233); AMS (231); IST (230); ATL (216) |
|   3 | num_routes | BIGINT        |       0 |         15 | 1.0   | 20.0  | 1.7998                                                |


### top_od_pairs.csv

- **Source**: CSV: publish/top_od_pairs.csv
- **Rows**: 100

**Preview (first 5 rows)**

| src_iata   | dst_iata   |   num_routes |
|:-----------|:-----------|-------------:|
| ORD        | ATL        |           20 |
| ATL        | ORD        |           19 |
| HKT        | BKK        |           13 |
| ORD        | MSY        |           13 |
| ATL        | MIA        |           12 |

|   # | Column     | DuckDB Type   |   Nulls |   Distinct | Min   | Max   | Mean/Examples                                |
|----:|:-----------|:--------------|--------:|-----------:|:------|:------|:---------------------------------------------|
|   1 | src_iata   | VARCHAR       |       0 |         54 |       |       | ATL (16); BKK (6); HGH (5); JFK (4); CDG (3) |
|   2 | dst_iata   | VARCHAR       |       0 |         56 |       |       | ATL (8); JFK (7); SIN (5); BKK (4); HGH (4)  |
|   3 | num_routes | BIGINT        |       0 |          7 | 9.0   | 20.0  | 10.2700                                      |

