# Data Quality Report

## airport_degree.csv — ✅ OK
- **Rows x Cols**: `3425 x 4`

### Kolom
| column    | dtype   |   nulls |   null_pct |   min |   max |   unique |
|:----------|:--------|--------:|-----------:|------:|------:|---------:|
| iata      | object  |       0 |          0 |   nan |   nan |     3425 |
| deg_out   | int64   |       0 |          0 |     0 |   239 |      143 |
| deg_in    | int64   |       0 |          0 |     0 |   238 |      143 |
| deg_total | int64   |       0 |          0 |     1 |   477 |      224 |

## dim_airport_clean.csv — ✅ OK
- **Rows x Cols**: `6072 x 8`

### Kolom
| column       | dtype   |   nulls |   null_pct |      min |     max |   unique |
|:-------------|:--------|--------:|-----------:|---------:|--------:|---------:|
| iata         | object  |       0 |      0     |  nan     | nan     |     6072 |
| icao         | object  |       0 |      0     |  nan     | nan     |     6072 |
| airport_name | object  |       0 |      0     |  nan     | nan     |     6046 |
| city         | object  |      39 |      0.642 |  nan     | nan     |     5602 |
| country      | object  |       0 |      0     |  nan     | nan     |      235 |
| lat          | float64 |       0 |      0     |  -62.191 |  82.518 |     6062 |
| lon          | float64 |       0 |      0     | -179.877 | 179.951 |     6064 |
| tz           | object  |     557 |      9.173 |  nan     | nan     |      306 |

## euro_atfm_by_location.csv — ✅ OK
- **Rows x Cols**: `28 x 2`

### Kolom
| column        | dtype   |   nulls |   null_pct |    min |    max |   unique |
|:--------------|:--------|--------:|-----------:|-------:|-------:|---------:|
| location      | object  |       0 |          0 | nan    | nan    |       28 |
| delay_minutes | float64 |       0 |          0 |  -0.14 |   2.64 |       23 |

## euro_atfm_timeseries.csv — ✅ OK
- **Rows x Cols**: `72 x 2`

### Kolom
| column        | dtype   |   nulls |   null_pct |   min |   max |   unique |
|:--------------|:--------|--------:|-----------:|------:|------:|---------:|
| period_start  | object  |       0 |          0 |   nan |   nan |       72 |
| delay_minutes | float64 |       0 |          0 |     1 |     1 |        1 |

## route_counts.csv — ✅ OK
- **Rows x Cols**: `37595 x 3`

### Kolom
| column     | dtype   |   nulls |   null_pct |   min |   max |   unique |
|:-----------|:--------|--------:|-----------:|------:|------:|---------:|
| src_iata   | object  |       0 |          0 |   nan |   nan |     3409 |
| dst_iata   | object  |       0 |          0 |   nan |   nan |     3418 |
| num_routes | int64   |       0 |          0 |     1 |    20 |       15 |

## top_od_pairs.csv — ✅ OK
- **Rows x Cols**: `100 x 3`

### Kolom
| column     | dtype   |   nulls |   null_pct |   min |   max |   unique |
|:-----------|:--------|--------:|-----------:|------:|------:|---------:|
| src_iata   | object  |       0 |          0 |   nan |   nan |       54 |
| dst_iata   | object  |       0 |          0 |   nan |   nan |       56 |
| num_routes | int64   |       0 |          0 |     9 |    20 |        7 |


**Overall status**: ✅ PASS
