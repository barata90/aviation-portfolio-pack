#!/usr/bin/env python3
"""
Build advanced assets for:
- Scenario Simulator (what-if on ATFM delays)
- Hub Ranking (PageRank on route network)
- Static API shards

Safe: gracefully skips if required CSVs are missing.
"""
from pathlib import Path
import json
import pandas as pd
import numpy as np

ROOT = Path(".")
DOCS = ROOT / "docs"
ASSETS = DOCS / "assets"
API = DOCS / "api"
PUB = ROOT / "publish"

ASSETS.mkdir(parents=True, exist_ok=True)
API.mkdir(parents=True, exist_ok=True)

def build_scenario_assets():
    ts_path = PUB / "euro_atfm_timeseries.csv"
    loc_path = PUB / "euro_atfm_by_location.csv"
    if not ts_path.exists() or not loc_path.exists():
        print(f"[skip] scenario: missing {ts_path.name if not ts_path.exists() else ''} {loc_path.name if not loc_path.exists() else ''}")
        return

    ts = pd.read_csv(ts_path, parse_dates=["period_start"]).sort_values("period_start")
    if ts.empty or "delay_minutes" not in ts.columns:
        print("[skip] scenario: timeseries empty or no delay_minutes")
        return

    last24 = ts["period_start"].max() - pd.DateOffset(months=23)
    ts24 = ts[ts["period_start"] >= last24].copy()
    ts24["month"] = ts24["period_start"].dt.strftime("%Y-%m")

    byloc = pd.read_csv(loc_path).rename(columns=str.lower)
    if not {"location","delay_minutes"}.issubset(byloc.columns):
        print("[skip] scenario: by_location missing required cols")
        return
    byloc = byloc[["location","delay_minutes"]].dropna()
    byloc["delay_minutes"] = byloc["delay_minutes"].astype(float).clip(lower=0)
    if byloc["delay_minutes"].sum() == 0:
        print("[skip] scenario: by_location total = 0")
        return
    byloc = byloc.sort_values("delay_minutes", ascending=False)
    byloc["share"] = byloc["delay_minutes"] / byloc["delay_minutes"].sum()

    months = ts24["month"].tolist()
    total = ts24["delay_minutes"].astype(float).round(2).tolist()

    locs = byloc["location"].tolist()[:25]
    shares = dict(zip(byloc["location"], byloc["share"]))
    locations = {loc: [] for loc in locs}
    for mval in ts24["delay_minutes"].tolist():
        for loc in locs:
            locations[loc].append(round(float(mval) * float(shares[loc]), 2))

    out = {"months": months, "total": total, "locations": locations, "top_locations": locs}
    (ASSETS / "scenario_timeseries.json").write_text(json.dumps(out), encoding="utf-8")
    print("[ok] scenario_timeseries.json")

def build_hub_rank():
    rc_path = PUB / "route_counts.csv"
    if not rc_path.exists():
        print("[skip] hub_rank: missing route_counts.csv")
        return
    rc = pd.read_csv(rc_path).rename(columns=str.lower)
    if not {"src_iata","dst_iata","num_routes"}.issubset(rc.columns):
        print("[skip] hub_rank: route_counts missing required cols")
        return
    rc = rc[["src_iata","dst_iata","num_routes"]].dropna()
    if rc.empty:
        print("[skip] hub_rank: route_counts empty")
        return
    rc["num_routes"] = rc["num_routes"].astype(float).clip(lower=0)

    nodes = sorted(set(rc["src_iata"]) | set(rc["dst_iata"]))
    n = len(nodes)
    if n == 0:
        print("[skip] hub_rank: no nodes")
        return
    idx = {n:i for i,n in enumerate(nodes)}

    # Column-stochastic adjacency (source in columns)
    A = np.zeros((n, n), dtype=float)
    for s, d, w in rc.itertuples(index=False):
        A[idx[d], idx[s]] += float(w)
    colsum = A.sum(axis=0)
    colsum[colsum == 0] = 1.0
    P = A / colsum

    # PageRank
    dmp = 0.85
    pr = np.ones(n) / n
    v = np.ones(n) / n
    for _ in range(100):
        pr_new = dmp * (P @ pr) + (1 - dmp) * v
        if np.linalg.norm(pr_new - pr, 1) < 1e-9:
            pr = pr_new
            break
        pr = pr_new

    df = pd.DataFrame({"iata": nodes, "pagerank": pr}).sort_values("pagerank", ascending=False)
    df.to_csv(ASSETS / "hub_rank.csv", index=False)

    top = df.head(30)
    fig = {
        "data": [{
            "type": "bar", "orientation": "h",
            "x": [round(float(x), 6) for x in top["pagerank"].tolist()],
            "y": top["iata"].tolist()
        }],
        "layout": {
            "margin": {"l": 80, "r": 10, "t": 20, "b": 40},
            "xaxis": {"title": "PageRank"},
            "yaxis": {"title": "Airport (IATA)"},
            "height": 520
        }
    }
    (ASSETS / "hub_rank.json").write_text(json.dumps(fig), encoding="utf-8")
    print("[ok] hub_rank.csv, hub_rank.json")

def build_static_api():
    (DOCS / "api").mkdir(parents=True, exist_ok=True)

    # last 24 months timeseries
    ts_path = PUB / "euro_atfm_timeseries.csv"
    if ts_path.exists():
        ts = pd.read_csv(ts_path, parse_dates=["period_start"]).sort_values("period_start")
        if not ts.empty:
            last24 = ts["period_start"].max() - pd.DateOffset(months=23)
            ts = ts[ts["period_start"] >= last24].copy()
            ts["period_start"] = ts["period_start"].dt.strftime("%Y-%m-%d")
            (DOCS / "api" / "euro_atfm_timeseries_last24.json").write_text(ts.to_json(orient="records"), encoding="utf-8")

    # top-100 degree
    deg_path = PUB / "airport_degree.csv"
    if deg_path.exists():
        deg = pd.read_csv(deg_path)
        if not deg.empty and "deg_total" in deg.columns:
            deg_top = deg.sort_values("deg_total", ascending=False).head(100)
            (DOCS / "api" / "airport_degree_top100.json").write_text(deg_top.to_json(orient="records"), encoding="utf-8")

    # index
    idx = []
    if (DOCS / "api" / "euro_atfm_timeseries_last24.json").exists():
        idx.append({"path": "api/euro_atfm_timeseries_last24.json"})
    if (DOCS / "api" / "airport_degree_top100.json").exists():
        idx.append({"path": "api/airport_degree_top100.json"})
    (DOCS / "api" / "index.json").write_text(json.dumps(idx), encoding="utf-8")
    print("[ok] api shards")

def main():
    build_scenario_assets()
    build_hub_rank()
    build_static_api()

if __name__ == "__main__":
    main()
