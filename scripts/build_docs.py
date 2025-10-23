#!/usr/bin/env python3
# scripts/build_docs.py
# Runtime: Python 3.12
# Deps: pandas, matplotlib

import io
from pathlib import Path
import json
import re
import warnings

# Headless backend for CI
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PUBLISH_DIR = ROOT / "publish"
DOCS = ROOT / "docs"
DATASETS_DIR = DOCS / "datasets"
PLOTS_DIR = DOCS / "assets" / "plots"
SCHEMA_DIR = DOCS / "assets" / "schema"

DATASETS_DIR.mkdir(parents=True, exist_ok=True)
PLOTS_DIR.mkdir(parents=True, exist_ok=True)
SCHEMA_DIR.mkdir(parents=True, exist_ok=True)

def _read_csv(csv_path: Path) -> pd.DataFrame:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        df = pd.read_csv(csv_path)
    return df

DATE_CANDIDATES = re.compile(r"(date|day|period|month|dt|timestamp|flight_date|ds)$", re.I)

def _pick_date_column(df: pd.DataFrame) -> str | None:
    # 1) by name
    for c in df.columns:
        if DATE_CANDIDATES.search(str(c)):
            return c
    # 2) try parse
    for c in df.columns:
        s = df[c]
        try:
            pd.to_datetime(s.dropna().head(50), errors="raise")
            return c
        except Exception:
            pass
    return None

def _numeric_columns(df: pd.DataFrame, exclude=None):
    exclude = set(exclude or [])
    return [c for c in df.columns if c not in exclude and pd.api.types.is_numeric_dtype(df[c])]

def _monthly_series(df: pd.DataFrame, dt_col: str, num_cols):
    d = df.copy()
    d[dt_col] = pd.to_datetime(d[dt_col], errors="coerce")
    d = d.dropna(subset=[dt_col]).sort_values(dt_col).set_index(dt_col)

    pref = [x for x in num_cols if re.search(r"(value|count|delay|minutes|flights|passenger|qty|num)$", str(x), re.I)]
    ycol = pref[0] if pref else (num_cols[0] if num_cols else None)
    if ycol:
        s = d[ycol].resample("MS").sum(min_count=1)
    else:
        s = d.resample("MS").size().rename("rows")
    return s

def _last_24_months(s: pd.Series) -> pd.Series:
    if s.empty:
        return s
    last = s.dropna().index.max()
    if pd.isna(last):
        return s
    start = (last.to_period("M") - 23).to_timestamp()
    return s.loc[start:]

def _save_plot(series: pd.Series, out_png: Path, title: str):
    out_png.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(8, 3))
    series.plot()
    plt.title(title)
    plt.xlabel("Month")
    plt.ylabel(series.name or "value")
    plt.tight_layout()
    plt.savefig(out_png)
    plt.close()

def _markdown_table(df: pd.DataFrame, limit: int = 20) -> str:
    try:
        return df.head(limit).to_markdown(index=False)
    except Exception:
        return "*(preview unavailable)*"

def _write_schema(csv_path: Path, df: pd.DataFrame):
    schema = [{"name": str(c), "dtype": str(df[c].dtype)} for c in df.columns]
    (SCHEMA_DIR / f"{csv_path.stem}.columns.json").write_text(
        json.dumps(schema, indent=2), encoding="utf-8"
    )

def _write_markdown(csv_path: Path, df: pd.DataFrame, monthly: pd.Series, filtered: pd.Series):
    md_path = DATASETS_DIR / f"{csv_path.stem}.md"

    # SELALU pakai link relatif dari folder datasets/
    rel_csv = f"../publish/{csv_path.name}"
    rel_png = f"../assets/plots/{csv_path.stem}_timeseries.png"

    period = ""
    if not filtered.empty:
        lo = filtered.index.min().strftime("%Y-%m")
        hi = filtered.index.max().strftime("%Y-%m")
        period = f" (Last 24 months: {lo} … {hi})"

    out = io.StringIO()
    out.write(f"# {csv_path.stem.replace('_',' ').title()}{period}\n\n")
    out.write(f"**Source CSV:** [{csv_path.name}]({rel_csv})\n\n")

    if (PLOTS_DIR / f"{csv_path.stem}_timeseries.png").exists():
        out.write(f"![trend]({rel_png})\n\n")

    out.write("## Summary\n\n")
    n_rows_total = len(df)
    n_cols = len(df.columns)
    n_rows_24m = int(filtered.dropna().shape[0]) if isinstance(filtered, pd.Series) else n_rows_total
    out.write(f"- **Rows (preview scope):** {n_rows_24m:,} of total {n_rows_total:,}\n")
    out.write(f"- **Columns:** {n_cols}\n\n")

    out.write("## Schema\n\n```\n")
    for c in df.columns:
        out.write(f"- {c}: {df[c].dtype}\n")
    out.write("```\n\n")

    out.write("## Preview\n\n")
    out.write(_markdown_table(df))
    out.write("\n")

    md_path.write_text(out.getvalue(), encoding="utf-8")

def _process_csv(csv_path: Path) -> None:
    try:
        df = _read_csv(csv_path)
        _write_schema(csv_path, df)
        dt_col = _pick_date_column(df)
        num_cols = _numeric_columns(df, exclude=[dt_col] if dt_col else None)

        monthly = pd.Series(dtype=float)
        filtered = pd.Series(dtype=float)

        if dt_col:
            if not pd.api.types.is_datetime64_any_dtype(df[dt_col]):
                df[dt_col] = pd.to_datetime(df[dt_col], errors="coerce")
            monthly = _monthly_series(df, dt_col, num_cols)
            filtered = _last_24_months(monthly)
            if not filtered.empty:
                _save_plot(filtered, PLOTS_DIR / f"{csv_path.stem}_timeseries.png", title=f"{csv_path.stem} – Monthly")
            # Batasi preview tabel ke 24 bulan terakhir
            mx = df[dt_col].max()
            if pd.notnull(mx):
                df = df[df[dt_col] >= (pd.Timestamp(mx) - pd.DateOffset(months=24))]

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
        _process_csv(csv_path)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
