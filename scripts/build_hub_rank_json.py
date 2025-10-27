#!/usr/bin/env python3
"""
Create Plotly JSON for Hub Ranking page from docs/assets/hub_rank.csv

Output: docs/assets/hub_rank.json
"""
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ASSETS = DOCS / "assets"
CSV = ASSETS / "hub_rank.csv"
OUT = ASSETS / "hub_rank.json"

def pick_cols(df: pd.DataFrame):
    # label column: prefer iata/airport/name
    label_pref = ["iata", "airport", "name", "node", "airport_name"]
    y_pref = ["degree", "pagerank", "score", "value", "num_routes"]
    def first(cols):
        for c in cols:
            if c in df.columns: return c
        return None
    label = first(label_pref) or df.columns[0]
    # numeric column
    numeric = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    y = first(y_pref) or (numeric[0] if numeric else None)
    return label, y

def main():
    if not CSV.exists():
        print("[skip] docs/assets/hub_rank.csv not found")
        return 0
    df = pd.read_csv(CSV)
    if df.empty:
        print("[skip] hub_rank.csv empty")
        return 0

    label_col, y_col = pick_cols(df)
    if not y_col:
        print("[skip] no numeric column found")
        return 0

    top = df.sort_values(y_col, ascending=False).head(20)
    fig = {
        "data": [{
            "type": "bar",
            "x": top[label_col].astype(str).tolist(),
            "y": top[y_col].tolist(),
            "name": "Top-20",
            "hovertemplate": "%{x}: %{y}<extra></extra>"
        }],
        "layout": {
            "margin": {"l": 40, "r": 10, "t": 10, "b": 80},
            "xaxis": {"tickangle": -45, "automargin": True, "title": ""},
            "yaxis": {"title": y_col, "automargin": True},
            "height": 520,
            "barmode": "group"
        }
    }
    ASSETS.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(fig), encoding="utf-8")
    print("[ok] wrote", OUT)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
