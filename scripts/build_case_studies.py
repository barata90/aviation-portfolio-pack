#!/usr/bin/env python3
import os, sys, textwrap
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ASSETS = DOCS / "assets"
PUBLISH = ROOT / "publish"
CASE_DIR = DOCS / "case_studies"

ASSETS.mkdir(parents=True, exist_ok=True)
CASE_DIR.mkdir(parents=True, exist_ok=True)

def savefig(name):
    p = ASSETS / name
    plt.tight_layout()
    plt.savefig(p, dpi=144, bbox_inches="tight")
    plt.close()
    return f"assets/{name}"

def month_floor(s):
    s = pd.to_datetime(s, errors="coerce", utc=True).dt.tz_localize(None)
    return s.dt.to_period("M").dt.to_timestamp()

def write_md(path, title, body):
    path.write_text(f"# {title}\n\n{body}\n", encoding="utf-8")

# ---- Case 1: Ops Delay Watch
def case_ops_delay():
    csv = PUBLISH / "euro_atfm_timeseries.csv"
    if not csv.exists():
        return
    df = pd.read_csv(csv)
    # kolom tanggal fleksibel: period_start / date / period
    for cand in ["period_start", "date", "period"]:
        if cand in df.columns:
            dtcol = cand; break
    else:
        return
    if "delay_minutes" not in df.columns:
        return

    df["_month"] = month_floor(df[dtcol])
    # jendela 24 bulan terakhir berdasarkan data (bukan hari ini)
    maxd = df["_month"].max()
    start = (maxd - pd.offsets.DateOffset(months=23)).to_pydatetime()
    d24 = df[df["_month"] >= start].copy()
    monthly = d24.groupby("_month", as_index=False)["delay_minutes"].sum()

    # Line 24 bulan
    plt.figure(figsize=(8,3))
    plt.plot(monthly["_month"], monthly["delay_minutes"], marker="o")
    plt.title("ATFM delay (en-route) — 24 bulan terakhir")
    plt.xlabel("Month"); plt.ylabel("Delay minutes")
    line_fn = savefig("case_ops_delay_24m.png")

    # YoY bar (kalau ada >= 12 bulan)
    yoy_text = ""
    if len(monthly) >= 12:
        this12 = monthly.tail(12)["delay_minutes"].sum()
        prev12 = monthly.iloc[:-12]["delay_minutes"].tail(12).sum() if len(monthly) >= 24 else pd.NA
        yoy = ((this12 - prev12)/prev12*100) if pd.notna(prev12) and prev12!=0 else pd.NA
        yoy_text = f"**12m total**: {this12:,.0f} menit; **YoY**: {yoy:.1f}%\n\n" if pd.notna(yoy) else f"**12m total**: {this12:,.0f} menit\n\n"

    # Top locations (jika file by_location ada)
    top_tbl = ""
    loc_csv = PUBLISH / "euro_atfm_by_location.csv"
    if loc_csv.exists():
        loc = pd.read_csv(loc_csv)
        top = loc.sort_values("delay_minutes", ascending=False).head(10).copy()
        top_tbl = top.to_markdown(index=False)

    body = textwrap.dedent(f"""
    **Ringkasan**
    {yoy_text}
    Grafik 24 bulan terakhir:

    ![]({line_fn})

    {"\nTop 10 lokasi dengan delay (menit):\n\n" + top_tbl if top_tbl else ""}
    """)
    write_md(CASE_DIR / "ops_delay_watch.md", "Ops Delay Watch (EUROCONTROL)", body)

# ---- Case 2: Network Strength
def case_network_strength():
    deg_csv = PUBLISH / "airport_degree.csv"
    od_csv  = PUBLISH / "top_od_pairs.csv"
    if not deg_csv.exists():
        return
    deg = pd.read_csv(deg_csv)
    deg["deg_total"] = deg[[c for c in deg.columns if c.lower().startswith("deg")]].sum(axis=1)
    top20 = deg.sort_values("deg_total", ascending=False).head(20)

    # Bar top-20 degree
    plt.figure(figsize=(8,3))
    plt.bar(top20["iata"].astype(str), top20["deg_total"])
    plt.xticks(rotation=60, ha="right")
    plt.title("Top-20 airport by degree (total)")
    plt.xlabel("IATA"); plt.ylabel("Degree")
    bar_fn = savefig("case_network_degree_top20.png")

    od_tbl = ""
    if od_csv.exists():
        od = pd.read_csv(od_csv).sort_values("num_routes", ascending=False).head(20)
        od_tbl = od.to_markdown(index=False)

    body = textwrap.dedent(f"""
    **Ringkasan**
    Degree bandara mengindikasikan konektivitas jaringan (out+in). Top-20:

    ![]({bar_fn})

    {"\nTop 20 OD pairs (berdasar variasi rute):\n\n" + od_tbl if od_tbl else ""}
    """)
    write_md(CASE_DIR / "network_strength.md", "Network Strength (OpenFlights)", body)

if __name__ == "__main__":
    case_ops_delay()
    case_network_strength()
    print("Case studies built.")
