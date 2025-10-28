# Data Reliability — SLI/SLO

**Monitored SLIs :**
- Freshness: day difference between max(date_column) and the build time.
- Schema drift: missing/extra columns compared to the contract.
- Null ratio: proportion of nulls in key columns.
- Uniqueness: duplicates on the primary key.
- Range: values outside the domain / negative numbers.

**SLO (default):**
- Freshness ≤ `freshness_max_lag_days` (see governance/datasets.yml)
- Nulls in key columns = 0%
- Uniqueness violations = 0
- Range: 0 negative rows for cumulative metrics

**Escalation**
- 🔴 ERROR → optionally fail DQ (`--fail-on=error`) so Pages deployment / data.
- 🟠 WARN → publication continues, but a badge is shown in the report.
