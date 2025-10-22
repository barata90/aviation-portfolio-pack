#!/usr/bin/env python3
from __future__ import annotations
import io
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PUBLISH = ROOT / "publish"
DOCS = ROOT / "docs"
DATASETS_DIR = DOCS / "datasets"
ASSETS_PLOTS = DOCS / "assets" / "plots"

DATASETS_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_PLOTS.mkdir(parents=True, exist_ok=True)

DATE_CANDIDATE_HINTS = {
    "date","dt","day","flight_date","operating_date","op_date","timestamp",
    "ts","depart_date","arrival_date","month","year_month","period"
}

def _try_parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        low = col.strip().lower()
        if ("date" in low) or (low in DATE_CANDIDATE_HINTS):
            df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)
    return df

def _detect_date_col(df: pd.DataFrame) -> str | None:
    best, best_nonnull = None, 0
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            nn = df[col].notna().sum()
            if nn > best_nonnull:
                best_nonnull, best = nn, col
    return best

def _filter_last_24_months(df: pd.DataFrame, date_col: str):
    s = df[date_col].dropna()
    if s.empty:
        return df, ""
    end = s.max().to_pydatetime().replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    if (end.year < 1900) or (end > now):
        end = now
    start = (pd.Timestamp(end).tz_convert(None) - pd.DateOffset(months=24)).to_pydatetime().replace(tzinfo=timezone.utc)
    f = df[df[date_col] >= pd.Timestamp(start)]
    period = f"{start.strftime('%Y-%m')} … {end.strftime('%Y-%m')}"
    return f, period

def _first_numeric(df: pd.DataFrame, exclude: set[str]) -> str | None:
    for col, dt in df.dtypes.items():
        if col in exclude: 
            continue
        if pd.api.types.is_numeric_dtype(dt):
            return col
    return None

def _plot_timeseries(df: pd.DataFrame, date_col: str, value_col: str | None, out_png: Path) -> bool:
    if df.empty: return False
    g = df.copy()
    g["_m"] = g[date_col].dt.to_period("M").dt.to_timestamp()
    if value_col:
        series = g.groupby("_m")[value_col].sum(min_count=1)
        ylabel = value_col
    else:
        series = g.groupby("_m").size()
        ylabel = "records"
    fig = plt.figure(figsize=(8, 3.5))
    ax = fig.add_subplot(111)
    series.plot(ax=ax)
    ax.set_xlabel("Month")
    ax.set_ylabel(ylabel)
    ax.set_title("")
    fig.tight_layout()
    fig.savefig(out_png)
    plt.close(fig)
    return True

def _sample_html_table(df: pd.DataFrame, max_rows: int = 2000, sample: int = 100) -> str:
    if len(df) > max_rows:
        return df.head(sample).to_html(index=False)
    return df.to_html(index=False)

def build_one(csv_path: Path):
    name = csv_path.stem
    rel_csv = f"/publish/{csv_path.name}"
    out_md = DATASETS_DIR / f"{name}.md"
    out_png = ASSETS_PLOTS / f"{name}.png"
    df = pd.read_csv(csv_path, encoding="utf-8-sig", low_memory=False)
    df = _try_parse_dates(df)
    date_col = _detect_date_col(df)
    period_txt = ""
    df2 = df
    if date_col:
        df2, period_txt = _filter_last_24_months(df, date_col)
    num_col = _first_numeric(df2, {date_col} if date_col else set())
    plotted = False
    if date_col:
        try:
            plotted = _plot_timeseries(df2, date_col, num_col, out_png)
        except Exception as e:
            print(f"[WARN] Plot failed for {csv_path.name}: {e}")
    title = name.replace("_"," ").title()
    if period_txt:
        title += f" (Last 24 months: {period_txt})"
    html_table = _sample_html_table(df2, max_rows=2000, sample=100)
    sio = io.StringIO()
    sio.write(f"# {title}\n\n")
    sio.write(f"**Source CSV:** [{csv_path.name}]({rel_csv})  \n")
    sio.write(f"**Rows:** {len(df2):,} (of total {len(df):,})  \n")
    if date_col: sio.write(f"**Date column:** `{date_col}`  \n")
    if num_col: sio.write(f"**Value column (plotted):** `{num_col}`  \n")
    sio.write("\n")
    if plotted and out_png.exists():
        sio.write(f"![Trend](/assets/plots/{out_png.name})\n\n")
    if len(df2) > 2000:
        sio.write("> Note: Large dataset – rendering a basic HTML preview (first 100 rows) to avoid DataTables warnings.\n\n")
    sio.write(html_table + "\n")
    out_md.write_text(sio.getvalue(), encoding="utf-8")
    print(f"Wrote {out_md.relative_to(ROOT)}")

def main():
    if not PUBLISH.exists():
        print("publish/ not found; nothing to do.")
        return 0
    for p in sorted(PUBLISH.glob("*.csv")):
        try:
            build_one(p)
        except Exception as e:
            print(f"[WARN] Skipping {p.name}: {e}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
