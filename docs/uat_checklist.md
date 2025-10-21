# UAT Checklist — Emirates Domain

## Scope
- Ingestion `publish/*.csv` → Snowflake (tables, types)
- Data Dictionary & Catalog page
- Dashboards (Power BI prototype)

## Test Cases
1. **Completeness** — row count sink vs source
2. **Schema** — column names, types, nullability
3. **Quality** — null% thresholds, unique keys
4. **Timeliness** — SLA update ≤ X hours after source refresh
5. **Dashboards** — numbers tie to backing tables (±0.1%)
6. **Security** — role can/cannot access tables as designed

## Acceptance Criteria
- Semua test PASS; dev notes dicapture di PR.
