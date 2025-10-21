#!/usr/bin/env python3
from pathlib import Path
import pandas as pd

CSV_DIR = Path("publish")
OUT_DIR = Path("docs/pages")

OUT_DIR.mkdir(parents=True, exist_ok=True)


def _first_existing(cols, candidates):
    """return first column name in cols that matches candidates (case-insensitive)
    also accept substring matches for 'icao' / 'airport' / 'location'
    """
    lower = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand in lower:
            return lower[cand]

    # fuzzy contains for common tokens
    tokens = ("icao", "airport", "location", "loc", "facility", "station", "name", "code")
    for c in cols:
        lc = c.lower()
        if any(tok in lc for tok in tokens):
            return c
    return None


def _pick_metric_column(df: pd.DataFrame) -> str:
    """prefer columns containing delay minutes; else first numeric"""
    num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    if not num_cols:
        raise ValueError("Tidak ada kolom numerik untuk diringkas.")

    prefs = ("delay_min", "delay minutes", "delay_minutes", "atfm", "minutes", "minute", "total_delay")
    lowmap = {c.lower(): c for c in num_cols}
    for p in prefs:
        for lc, orig in lowmap.items():
            if p in lc:
                return orig
    return num_cols[0]


def save_html_table(df: pd.DataFrame, title: str, outfile: Path):
    html = f"""<!doctype html>
<meta charset="utf-8" />
<title>{title}</title>
<h2>{title}</h2>
{df.to_html(index=False)}
"""
    outfile.write_text(html, encoding="utf-8")


def by_location():
    src = CSV_DIR / "euro_atfm_by_location.csv"
    if not src.exists():
        # Tidak fatal untuk portfolio — cukup lewati
        print(f"[SKIP] {src.name} tidak ditemukan")
        return

    df = pd.read_csv(src)
    # cari kolom lokasi
    loc_col = _first_existing(
        df.columns,
        [c for c in ("location", "loc", "location_name", "airport", "icao", "icao_code", "apt", "ref")],
    )
    if loc_col is None:
        raise ValueError(
            "Tidak bisa menemukan kolom lokasi di euro_atfm_by_location.csv. "
            "Tambahkan kolom seperti 'location' / 'airport' / 'icao'."
        )

    metric_col = _pick_metric_column(df)
    agg = (
        df.groupby(loc_col, dropna=False)[metric_col]
        .sum()
        .reset_index()
        .sort_values(metric_col, ascending=False)
    )

    # tampilkan top 30 biar ringkas
    topn = agg.head(30)
    save_html_table(topn, f"ATFM by location — top 30 by {metric_col}", OUT_DIR / "atfm_by_location.html")
    print("[OK] atfm_by_location.html")


def timeseries():
    src = CSV_DIR / "euro_atfm_timeseries.csv"
    if not src.exists():
        print(f"[SKIP] {src.name} tidak ditemukan")
        return

    df = pd.read_csv(src)

    # deteksi kolom tanggal sederhana
    date_col = None
    for c in df.columns:
        lc = c.lower()
        if lc in ("date", "period"):
            date_col = c
            break

    if date_col is None and {"year", "month"}.issubset({c.lower() for c in df.columns}):
        # rakit YYYY-MM-01 dari year,month
        year_col = next(c for c in df.columns if c.lower() == "year")
        month_col = next(c for c in df.columns if c.lower() == "month")
        tmp = df[[year_col, month_col]].copy()
        tmp["month"] = tmp[month_col].astype(int).clip(1, 12)
        df["date"] = pd.to_datetime(
            tmp[year_col].astype(int).astype(str) + "-" + tmp["month"].astype(str) + "-01",
            errors="coerce",
        )
        date_col = "date"
    elif date_col is not None:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    if date_col is None:
        # fallback: hanya rangkum total
        metric_col = _pick_metric_column(df)
        total = pd.DataFrame({metric_col: [df[metric_col].sum()]})
        save_html_table(total, f"ATFM total — {metric_col}", OUT_DIR / "atfm_timeseries.html")
        print("[OK] atfm_timeseries.html")
        return

    metric_col = _pick_metric_column(df)
    ts = (
        df.groupby(pd.Grouper(key=date_col, freq="MS"))[metric_col]
        .sum()
        .reset_index()
        .sort_values(date_col)
    )
    save_html_table(ts, f"ATFM timeseries (monthly) — {metric_col}", OUT_DIR / "atfm_timeseries.html")
    print("[OK] atfm_timeseries.html")


def main():
    timeseries()
    by_location()


if __name__ == "__main__":
    main()
