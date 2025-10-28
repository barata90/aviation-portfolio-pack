#!/usr/bin/env python3
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
API = DOCS / "api"
PUBLISH = ROOT / "publish"
DOCS_PUBLISH = DOCS / "publish"
SRC = None

def find_src():
    # prefer root publish/, else docs/publish/
    for p in (PUBLISH, DOCS_PUBLISH):
        f = p / "euro_atfm_timeseries.csv"
        if f.exists():
            return f
    return None

def pick(cols, options):
    for c in options:
        if c in cols:
            return c
    return None

def main():
    global SRC
    SRC = find_src()
    API.mkdir(parents=True, exist_ok=True)
    out = API / "euro_atfm_timeseries_last24.json"

    if not SRC:
        out.write_text("[]", encoding="utf-8")
        print("[warn] source CSV not found; wrote empty []")
        return 0

    df = pd.read_csv(SRC)
    if df.empty:
        out.write_text("[]", encoding="utf-8")
        print("[warn] source empty; wrote []")
        return 0

    # cari kolom tanggal/bulan
    date_col = pick(df.columns, ["month", "date", "period", "ym"])
    if not date_col:
        # ambil kolom pertama yang terlihat seperti periode
        date_col = df.columns[0]

    # parse ke datetime (robust)
    df["_month"] = pd.to_datetime(df[date_col], errors="coerce").dt.to_period("M").dt.to_timestamp()

    # pilih metrik delay (fallback ke numeric pertama)
    candidates = ["delay", "delay_min", "delay_minutes", "atfm_delay", "value"]
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    val_col = pick(df.columns, candidates) or (numeric_cols[0] if numeric_cols else None)
    if not val_col:
        out.write_text("[]", encoding="utf-8")
        print("[warn] no numeric value column; wrote []")
        return 0

    # ambil 24 bulan terakhir
    df = df.dropna(subset=["_month"])
    if df.empty:
        out.write_text("[]", encoding="utf-8")
        print("[warn] no valid months; wrote []")
        return 0

    last = df["_month"].max()
    start = (last.to_period("M") - 23).to_timestamp()
    df24 = df[df["_month"] >= start].sort_values("_month")

    # bentuk payload ringan
    items = []
    for _, r in df24.iterrows():
        items.append({
            "month": r["_month"].strftime("%Y-%m"),
            "delay_min": float(r[val_col]) if pd.notna(r[val_col]) else None
        })

    out.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
    print(f"[ok] wrote {out} with {len(items)} rows")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
