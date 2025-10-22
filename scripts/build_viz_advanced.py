#!/usr/bin/env python3
import json
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ASSETS = DOCS / "assets"
PUBLISH = ROOT / "publish"
ASSETS.mkdir(parents=True, exist_ok=True)

def month_floor(s):
    s = pd.to_datetime(s, errors="coerce", utc=True).dt.tz_localize(None)
    return s.dt.to_period("M").dt.to_timestamp()

def robust_anomalies(y, win=5, k=3.0):
    med = y.rolling(win, center=True, min_periods=1).median()
    mad = (y - med).abs().rolling(win, center=True, min_periods=1).median()
    mad = mad.replace(0, mad[mad>0].min() if (mad>0).any() else 1e-9)
    z = (y - med) / (1.4826 * mad)
    return z.abs() > k, med

def savefig(name):
    p = ASSETS / name
    plt.tight_layout()
    plt.savefig(p, dpi=144, bbox_inches="tight")
    plt.close()
    return f"assets/{name}"

def plot_ops_timeseries():
    csv = PUBLISH / "euro_atfm_timeseries.csv"
    if not csv.exists(): return None, None
    df = pd.read_csv(csv)
    col_date = next((c for c in ["period_start","date","period"] if c in df.columns), None)
    if col_date is None or "delay_minutes" not in df.columns: return None, None

    df["_m"] = month_floor(df[col_date])
    maxd = df["_m"].max()
    start = (maxd - pd.offsets.DateOffset(months=23)).to_pydatetime()
    d = df[df["_m"] >= start].groupby("_m", as_index=False)["delay_minutes"].sum()

    anom_mask, _ = robust_anomalies(d["delay_minutes"], win=5, k=3.0)
    ma = d["delay_minutes"].rolling(3, center=True, min_periods=1).mean()

    plt.figure(figsize=(8.8,3.2))
    plt.plot(d["_m"], d["delay_minutes"], marker="o", label="Delay (min)")
    plt.plot(d["_m"], ma, linestyle="--", label="3M moving avg")
    plt.scatter(d["_m"][anom_mask], d["delay_minutes"][anom_mask], s=48, zorder=5)
    for x,y in zip(d["_m"][anom_mask], d["delay_minutes"][anom_mask]):
        plt.annotate("anomaly", (x,y), textcoords="offset points", xytext=(0,8), ha="center", fontsize=8)
    plt.title("EUROCONTROL ATFM — 24 bulan (anomali & 3M MA)")
    plt.xlabel("Month"); plt.ylabel("Delay minutes"); plt.grid(True, alpha=.25)
    static_png = savefig("ops_delay_24m_advanced.png")

    def iso(x): return [str(ts.date()) for ts in x]
    fig = {
      "data":[
        {"type":"scatter","mode":"lines+markers","name":"Delay (min)","x":iso(d["_m"]), "y":d["delay_minutes"].round(2).tolist()},
        {"type":"scatter","mode":"lines","name":"3M MA","x":iso(d["_m"]), "y":ma.round(2).tolist(), "line":{"dash":"dash"}},
        {"type":"scatter","mode":"markers","name":"Anomalies","x":iso(d["_m"][anom_mask]), "y":d["delay_minutes"][anom_mask].round(2).tolist(),
         "marker":{"color":"crimson","size":9}}
      ],
      "layout":{
        "margin":{"l":40,"r":10,"t":20,"b":40},
        "xaxis":{"rangeslider":{"visible":True}},
        "yaxis":{"title":"Delay minutes"},
        "template":"plotly_white",
        "showlegend":True,
        "hovermode":"x unified"
      }
    }
    (ASSETS / "ops_delay_plotly.json").write_text(json.dumps(fig), encoding="utf-8")

    if len(d) >= 12:
        this12 = d.tail(12)["delay_minutes"].sum()
        prev12 = d.iloc[:-12].tail(12)["delay_minutes"].sum() if len(d) >= 24 else np.nan
        yoy = ((this12 - prev12)/prev12*100.0) if (isinstance(prev12,(int,float)) and prev12!=0) else np.nan
    else:
        this12, yoy = np.nan, np.nan

    kpis = {
      "last_month": float(d["delay_minutes"].iloc[-1]),
      "last_month_label": str(d["_m"].iloc[-1].date()),
      "rolling_12m": None if pd.isna(this12) else float(this12),
      "yoy_pct": None if pd.isna(yoy) else float(yoy)
    }
    (ASSETS / "ops_delay_kpis.json").write_text(json.dumps(kpis), encoding="utf-8")
    return static_png, kpis

def plot_small_multiples_top_locations():
    csv = PUBLISH / "euro_atfm_by_location.csv"
    if not csv.exists(): return None
    loc = pd.read_csv(csv)
    if not {"location","delay_minutes"}.issubset(loc.columns): return None
    top = loc.sort_values("delay_minutes", ascending=False).head(12)["location"].astype(str).tolist()
    plt.figure(figsize=(9,6))
    cols = 3; rows = int(np.ceil(len(top)/cols))
    for i, name in enumerate(top, 1):
        ax = plt.subplot(rows, cols, i)
        val = loc.loc[loc["location"]==name, "delay_minutes"].sum()
        ax.bar([name], [val])
        ax.set_title(name, fontsize=9)
        ax.set_xticks([]); ax.set_yticks([])
    plt.suptitle("Top-12 locations — total delay (mini panels)")
    return savefig("ops_delay_top_locations_smallmultiples.png")

def network_bars():
    deg_csv = PUBLISH / "airport_degree.csv"
    if not deg_csv.exists(): return None
    df = pd.read_csv(deg_csv)
    if not {"iata","deg_out","deg_in","deg_total"}.issubset(df.columns): return None
    top = df.sort_values("deg_total", ascending=False).head(20)
    plt.figure(figsize=(9,3.2))
    plt.bar(top["iata"].astype(str), top["deg_total"])
    for i,(x,y) in enumerate(zip(top["iata"], top["deg_total"])):
        plt.text(i, y, f"{int(y)}", ha="center", va="bottom", fontsize=8)
    plt.title("Top-20 airport degree (total)")
    plt.xticks(rotation=60, ha="right")
    plt.ylabel("Degree")
    plt.grid(axis="y", alpha=.2)
    return savefig("network_degree_top20.png")

def main():
    static_png, _ = plot_ops_timeseries()
    sm_png = plot_small_multiples_top_locations()
    deg_png = network_bars()
    created = [p for p in [static_png, sm_png, deg_png] if p]
    print("Assets created:", created)

if __name__ == "__main__":
    main()
