import pandas as pd
from pathlib import Path
import plotly.express as px

DOCS = Path("docs")
PUBLISH = Path("publish")
DOCS.mkdir(parents=True, exist_ok=True)

def find_file(name):
    p = PUBLISH / f"{name}.csv"
    return p if p.exists() else None

def infer_date_col(df):
    for c in df.columns:
        try:
            pd.to_datetime(df[c])
            return c
        except Exception:
            continue
    return None

def infer_value_col(df):
    # cari kolom yang mengindikasikan delay
    for key in ("delay", "minutes", "atfm", "mins"):
        for c in df.columns:
            if key in c.lower() and pd.api.types.is_numeric_dtype(df[c]):
                return c
    # fallback: kolom numerik pertama
    nums = df.select_dtypes("number").columns
    return nums[0] if len(nums) else None

def timeseries():
    f = find_file("euro_atfm_timeseries")
    if not f:
        print("[SKIP] euro_atfm_timeseries.csv tidak ditemukan")
        return
    df = pd.read_csv(f)
    dcol = infer_date_col(df)
    vcol = infer_value_col(df)
    if not (dcol and vcol):
        print("[SKIP] timeseries: kolom tidak dikenali")
        return
    df[dcol] = pd.to_datetime(df[dcol])
    ts = df.groupby(pd.Grouper(key=dcol, freq="D"))[vcol].sum().reset_index()
    fig = px.line(ts, x=dcol, y=vcol, title="ATFM Delay – Harian")
    fig.write_html(DOCS / "atfm_timeseries.html", include_plotlyjs="cdn")
    print("[OK] atfm_timeseries.html")

def by_location():
    f = find_file("euro_atfm_by_location")
    if not f:
        print("[SKIP] euro_atfm_by_location.csv tidak ditemukan")
        return
    df = pd.read_csv(f)
    vcol = infer_value_col(df)
    loc_col = None
    for k in ("airport","icao","iata","location","sector"):
        for c in df.columns:
            if k in c.lower():
                loc_col = c; breakÂ
        if loc_col: break
    if not (vcol and loc_col):
        print("[SKIP] by_location: kolom tidak dikenali")
        return
    top = df.groupby(loc_col)[vcol].sum().sort_values(ascending=False).head(15).reset_index()
    fig = px.bar(top, x=vcol, y=loc_col, orientation="h", title="Top 15 Lokasi ATFM Delay")
    fig.update_layout(yaxis=dict(autorange="reversed"))
    fig.write_html(DOCS / "atfm_top_locations.html", include_plotlyjs="cdn")
    print("[OK] atfm_top_locations.html")

if __name__ == "__main__":
    timeseries()
    by_location()
