#!/usr/bin/env python3
import json, hashlib
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / "publish"
DOCS = ROOT / "docs"
ASSETS = DOCS / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)

def md5sum(p: Path) -> str:
    h = hashlib.md5()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1<<20), b""): h.update(chunk)
    return h.hexdigest()

def guess_lat_lon(df: pd.DataFrame):
    lat_cands = ["latitude","lat","LAT","y","Y"]
    lon_cands = ["longitude","lon","lng","LONGITUDE","x","X"]
    lat = next((c for c in lat_cands if c in df.columns), None)
    lon = next((c for c in lon_cands if c in df.columns), None)
    return lat, lon

def build_airports_geojson():
    deg_csv = PUB / "airport_degree.csv"
    dim_alt = PUB / "dim_airport_clean.csv"
    if not deg_csv.exists():
        print("[map] airport_degree.csv not found → skip")
        return
    deg = pd.read_csv(deg_csv)
    if not dim_alt.exists():
        print("[map] dim_airport_clean.csv not found in publish → skip")
        return
    d = pd.read_csv(dim_alt)
    for c in d.columns:
        if c.lower() == "iata":
            d = d.rename(columns={c:"iata"})
    lat, lon = guess_lat_lon(d)
    if not lat or not lon or "iata" not in d.columns:
        print("[map] lat/lon/iata not found → skip")
        return
    m = pd.merge(d, deg, on="iata", how="inner").dropna(subset=[lat, lon])
    features = []
    for _, r in m.iterrows():
        try:
            latv = float(r[lat]); lonv = float(r[lon])
        except: 
            continue
        props = {k: (None if pd.isna(v) else v) for k,v in r.items()}
        features.append({
            "type":"Feature",
            "geometry":{"type":"Point","coordinates":[lonv, latv]},
            "properties":props
        })
    fc = {"type":"FeatureCollection", "features":features}
    out = ASSETS / "airports.geojson"
    out.write_text(json.dumps(fc), encoding="utf-8")
    print(f"[map] wrote {out}")

def build_sankey_json():
    p = PUB / "top_od_pairs.csv"
    if not p.exists():
        print("[sankey] top_od_pairs.csv not found → skip")
        return
    df = pd.read_csv(p).dropna()
    df = df.sort_values("num_routes", ascending=False).head(30)
    nodes = sorted(set(df["src_iata"].astype(str)) | set(df["dst_iata"].astype(str)))
    index = {n:i for i,n in enumerate(nodes)}
    links = {
        "source":[index[s] for s in df["src_iata"].astype(str)],
        "target":[index[t] for t in df["dst_iata"].astype(str)],
        "value": df["num_routes"].astype(float).tolist()
    }
    fig = {
      "data":[{
        "type":"sankey",
        "node":{"label":nodes,"pad":10,"thickness":10},
        "link":links
      }],
      "layout":{"margin":{"l":10,"r":10,"t":20,"b":20}, "font":{"size":10}}
    }
    out = ASSETS / "route_flow_sankey.json"
    out.write_text(json.dumps(fig), encoding="utf-8")
    print(f"[sankey] wrote {out}")

def build_explorer_manifest_and_downloads():
    files = sorted((ROOT / "publish").glob("*.csv"))
    manifest = []
    lines = ["# Downloads", "", "| File | Size (KB) | MD5 |", "|---|---:|---|"]
    for f in files:
        size = f.stat().st_size
        md5 = __import__("hashlib").md5(f.read_bytes()).hexdigest()
        # preview columns (optional manifest)
        try:
            import pandas as pd
            cols = pd.read_csv(f, nrows=5).columns.tolist()
        except Exception:
            cols = []
        manifest.append({"file":f.name, "size":size, "md5":md5, "columns":cols})
        lines.append(f"| [{f.name}](publish/{f.name}) | {size/1024:.1f} | {md5[:8]} |")
    (ASSETS / "datasets.json").write_text(__import__("json").dumps(manifest), encoding="utf-8")
    (DOCS / "downloads.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("[explorer] wrote datasets.json and downloads.md")

def main():
    build_airports_geojson()
    build_sankey_json()
    build_explorer_manifest_and_downloads()

    build_airports_geojson()
    build_sankey_json()
    build_explorer_manifest_and_downloads()

if __name__ == "__main__":
    main()
