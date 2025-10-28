#!/usr/bin/env python3
"""
Ensure Hub Rank assets are present and consistent.

- Prefer CSV -> JSON
- If CSV empty and JSON exists -> JSON -> CSV
- If both missing/empty -> write a sensible Top-20 fallback (same as current chart)
"""

from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ASSETS = DOCS / "assets"
CSV = ASSETS / "hub_rank.csv"
JSONP = ASSETS / "hub_rank.json"

# Fallback (sesuai grafik yang tampil sekarang)
FALLBACK_X = [
    "FRA","CDG","AMS","IST","ATL","PEK","ORD","MUC","DME","DFW",
    "DXB","LHR","DEN","IAH","LGW","BCN","JFK","FCO","MAD","STN"
]
FALLBACK_Y = [
    477,470,463,457,433,412,409,380,378,372,
    370,342,337,337,330,326,322,316,314,305
]

def csv_has_rows(p: Path) -> bool:
    if not p.exists():
        return False
    try:
        df = pd.read_csv(p)
        if df.empty:
            return False
        # setidaknya ada satu kolom numerik
        return any(pd.api.types.is_numeric_dtype(df[c]) for c in df.columns)
    except Exception:
        return False

def json_has_xy(p: Path):
    if not p.exists():
        return False, [], []
    try:
        j = json.loads(p.read_text(encoding="utf-8"))
        data = (j or {}).get("data") or []
        if not data:
            return False, [], []
        d0 = data[0] or {}
        x = d0.get("x") or []
        y = d0.get("y") or []
        return (len(x) == len(y) and len(x) > 0), x, y
    except Exception:
        return False, [], []

def write_json_from_df(df: pd.DataFrame):
    # heuristik kolom
    label_pref = ["iata", "airport", "name", "node", "label"]
    val_pref = ["score", "degree", "pagerank", "value", "num_routes"]
    def pick(cols, pref):
        for c in pref:
            if c in cols: return c
        return cols[0] if cols else None
    cols = list(df.columns)
    label = pick(cols, label_pref)
    num_cols = [c for c in cols if pd.api.types.is_numeric_dtype(df[c])]
    val = pick(cols, val_pref) if any(c in cols for c in val_pref) else (num_cols[0] if num_cols else None)
    if not label or not val:
        raise ValueError("Cannot determine label/value columns for JSON build.")
    top = df.sort_values(val, ascending=False).head(20)
    fig = {
        "data": [{
            "type": "bar",
            "x": top[label].astype(str).tolist(),
            "y": top[val].astype(float).tolist(),
            "name": "Top-20",
            "hovertemplate": "%{x}: %{y:,}<extra></extra>"
        }],
        "layout": {
            "title": {"text": "Top-20 airport degree (total)"},
            "margin": {"l": 50, "r": 10, "t": 30, "b": 90},
            "xaxis": {"tickangle": -45, "automargin": True},
            "yaxis": {"title": val, "automargin": True, "tickformat": ",d"},
            "height": 520
        }
    }
    JSONP.write_text(json.dumps(fig), encoding="utf-8")
    print("[ok] wrote", JSONP)

def write_csv_from_xy(x, y):
    df = pd.DataFrame({"iata": list(map(str, x)), "score": y})
    ASSETS.mkdir(parents=True, exist_ok=True)
    df.to_csv(CSV, index=False)
    print("[ok] wrote", CSV)

def main():
    ASSETS.mkdir(parents=True, exist_ok=True)

    csv_ok = csv_has_rows(CSV)
    json_ok, xj, yj = json_has_xy(JSONP)

    if csv_ok:
        df = pd.read_csv(CSV)
        write_json_from_df(df)
        return 0

    if (not csv_ok) and json_ok:
        write_csv_from_xy(xj, yj)
        return 0

    # both missing/empty -> fallback
    write_csv_from_xy(FALLBACK_X, FALLBACK_Y)
    df = pd.DataFrame({"iata": FALLBACK_X, "score": FALLBACK_Y})
    write_json_from_df(df)
    print("[warn] both CSV/JSON missing or empty → wrote fallback data.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
