<<<<<<< HEAD
#!/usr/bin/env python3
"""
Build dataset pages (Markdown) and static plots for MkDocs.

- Scans publish/*.csv
- For each CSV:
  * Reads robustly (UTF-8-SIG, low_memory=False)
  * Detects a date column (by dtype or name hints) and >= 1 numeric column
  * Aggregates monthly totals, filters to last 24 months for plots/tables
  * Saves a time-series PNG under docs/assets/plots/
  * Writes a Markdown page in docs/datasets/<name>.md
  * Writes schema JSON in docs/assets/schema/<name>.columns.json
- For large CSVs, renders a simple Markdown preview (no DataTables JS)
- Uses {{ base_url }} for asset links (subpath-safe on GitHub Pages)
- Never fails the workflow: per-file try/except and overall exit 0
"""
from __future__ import annotations
import json
from io import StringIO
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd

# Headless Matplotlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DOCS_DIR = Path("docs")
PUBLISH_DIR = Path("publish")
DATASETS_DIR = DOCS_DIR / "datasets"
ASSETS_DIR = DOCS_DIR / "assets"
PLOTS_DIR = ASSETS_DIR / "plots"
SCHEMA_DIR = ASSETS_DIR / "schema"

BASE_URL = "{{ base_url }}"

DATE_HINTS = (
    "date", "dt", "day", "flight_date", "operating_date",
    "op_date", "timestamp", "ts", "period", "month", "year_month",
)

for d in (DATASETS_DIR, PLOTS_DIR, SCHEMA_DIR):
    d.mkdir(parents=True, exist_ok=True)

def _read_csv(csv_path: Path) -> pd.DataFrame:
    return pd.read_csv(csv_path, encoding="utf-8-sig", low_memory=False)

def _is_datetime_series(s: pd.Series) -> bool:
    if pd.api.types.is_datetime64_any_dtype(s):
        return True
    try:
        pd.to_datetime(s.dropna().head(100), errors="raise")
        return True
    except Exception:
        return False

def _pick_date_column(df: pd.DataFrame) -> Optional[str]:
    for c in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[c]):
            return c
    candidates = [c for c in df.columns if any(h in str(c).lower() for h in DATE_HINTS)]
    for c in candidates:
        if _is_datetime_series(df[c]):
            return c
    for c in df.columns:
        if _is_datetime_series(df[c]):
            return c
    return None

def _numeric_columns(df: pd.DataFrame, exclude: Optional[List[str]] = None) -> List[str]:
    exclude = set(exclude or [])
    return [c for c in df.columns if c not in exclude and pd.api.types.is_numeric_dtype(df[c])]

def _monthly_series(df: pd.DataFrame, date_col: str, value_cols: List[str]) -> pd.Series:
    d = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(d[date_col]):
        d[date_col] = pd.to_datetime(d[date_col], errors="coerce")
    d = d.dropna(subset=[date_col])
    if d.empty:
        return pd.Series(dtype=float)

    d["_m"] = d[date_col].dt.to_period("M").dt.to_timestamp()
    if value_cols:
        y = d.groupby("_m")[value_cols].sum(min_count=1).sum(axis=1)
    else:
        y = d.groupby("_m").size()
        y = pd.Series(y, index=y.index)
    return y.sort_index()

def _last_24_months(s: pd.Series) -> pd.Series:
    if s.empty:
        return s
    end = s.index.max()
    start = end - pd.DateOffset(months=24)
    start = pd.Timestamp(year=start.year, month=start.month, day=1)
    return s.loc[s.index >= start]

def _save_plot(series: pd.Series, out_png: Path) -> None:
    if series.empty:
        return
    plt.figure(figsize=(8, 3))
    series.plot(kind="line", marker="o")
    plt.title("Monthly trend (last 24 months)")
    plt.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_png, dpi=150)
    plt.close()

def _markdown_table(df: pd.DataFrame, max_rows: int = 2000, preview_rows: int = 50) -> str:
    total = len(df)
    if total > max_rows:
        df = df.head(preview_rows)
        note = f"_Showing first {preview_rows} of {total:,} rows._\n\n"
    else:
        note = ""

    df2 = df.copy()
    for c in df2.columns:
        if pd.api.types.is_datetime64_any_dtype(df2[c]):
            df2[c] = pd.to_datetime(df2[c], errors="coerce").dt.strftime("%Y-%m-%d")
        else:
            df2[c] = df2[c].astype(str)

    buf = StringIO()
    cols = [str(c) for c in df2.columns]
    buf.write("| " + " | ".join(cols) + " |\n")
    buf.write("|" + "|".join(["---"] * len(cols)) + "|\n")
    for _, row in df2.iterrows():
        vals = [str(row[c]).replace("|", r"\|") for c in df2.columns]
        buf.write("| " + " | ".join(vals) + " |\n")
    return note + buf.getvalue()

def _write_schema(csv_path: Path, df: pd.DataFrame) -> None:
    schema = []
    for c in df.columns:
        dtype = str(df[c].dtype)
        schema.append({"name": str(c), "dtype": dtype})
    out = SCHEMA_DIR / f"{csv_path.stem}.columns.json"
    out.write_text(json.dumps(schema, indent=2), encoding="utf-8")

def _write_markdown(csv_path: Path, df: pd.DataFrame, monthly: pd.Series, filtered_monthly: pd.Series) -> None:
    stem = csv_path.stem
    md_path = DATASETS_DIR / f"{stem}.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)

    rel_csv = f"{BASE_URL}/publish/{csv_path.name}"
    plot_png = PLOTS_DIR / f"{stem}_timeseries.png"
    rel_png = f"{BASE_URL}/assets/plots/{plot_png.name}"

    title_suffix = ""
    if not filtered_monthly.empty:
        title_suffix = f" (Last 24 months: {filtered_monthly.index.min().strftime('%Y-%m')} … {filtered_monthly.index.max().strftime('%Y-%m')})"

    out = StringIO()
    out.write(f"# {stem.replace('_', ' ').title()}{title_suffix}\n\n")
    out.write(f"**Source CSV:** [{csv_path.name}]({rel_csv})  \n")
    out.write(f"**Rows:** {len(df):,}  \n")
    out.write(f"**Columns:** {', '.join(map(str, df.columns))}\n\n")

    if not filtered_monthly.empty and plot_png.exists():
        out.write(f"![Time series]({rel_png})\n\n")

    out.write("### Schema\n\n")
    out.write("```\n")
    for c in df.columns:
        out.write(f"- {c}: {df[c].dtype}\n")
    out.write("```\n\n")

    out.write("### Preview\n\n")
    out.write(_markdown_table(df))
    out.write("\n")

    md_path.write_text(out.getvalue(), encoding="utf-8")

def process_csv(csv_path: Path) -> None:
    try:
        df = _read_csv(csv_path)
        _write_schema(csv_path, df)

        date_col = _pick_date_column(df)
        num_cols = _numeric_columns(df, exclude=[date_col] if date_col else None)

        monthly = pd.Series(dtype=float)
        filtered = pd.Series(dtype=float)

        if date_col:
            if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
                df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
            monthly = _monthly_series(df, date_col, num_cols)
            filtered = _last_24_months(monthly)
            if not filtered.empty:
                out_png = PLOTS_DIR / f"{csv_path.stem}_timeseries.png"
                _save_plot(filtered, out_png)

            # also filter raw df for preview
            max_dt = df[date_col].max()
            if pd.notnull(max_dt):
                start_dt = pd.Timestamp(max_dt) - pd.DateOffset(months=24)
                df = df[df[date_col] >= start_dt]

        _write_markdown(csv_path, df, monthly, filtered)

        print(f"[OK] Built page for {csv_path.name}")
    except Exception as e:
        print(f"[WARN] Skipping {csv_path.name}: {e}")

def main() -> int:
    csvs = sorted(PUBLISH_DIR.glob("*.csv"))
    if not csvs:
        print("No CSVs found in publish/ — nothing to build.")
        return 0
    for csv_path in csvs:
        process_csv(csv_path)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
=======
<PASTE_BUILD_DOCS_PY>
>>>>>>> 9fd5aca (CI/site hardening: stable pages build; datasets index; Agg backend; 24M filter; instant-nav & cache-bust; mkdocs YAML repair)
