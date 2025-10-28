#!/usr/bin/env python3
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ASSETS = DOCS / "assets"
CSV = ASSETS / "hub_rank.csv"
JSONP = ASSETS / "hub_rank.json"

def csv_has_rows(p: Path) -> bool:
    if not p.exists():
        return False
    try:
        df = pd.read_csv(p)
        return df.dropna().shape[0] > 0
    except Exception:
        return False

def main():
    ASSETS.mkdir(parents=True, exist_ok=True)

    if csv_has_rows(CSV):
        print("[ok] hub_rank.csv already has rows")
        return 0

    if JSONP.exists():
        j = json.loads(JSONP.read_text(encoding="utf-8"))
        data = (j or {}).get("data", [])
        if data:
            d0 = data[0]
            x = d0.get("x", [])
            y = d0.get("y", [])
            if x and y and len(x) == len(y):
                df = pd.DataFrame({"iata": x, "score": y})
                df.to_csv(CSV, index=False)
                print("[ok] wrote hub_rank.csv from hub_rank.json")
                return 0

    # last resort: ensure file exists with header
    if not CSV.exists():
        CSV.write_text("iata,score\n", encoding="utf-8")
        print("[warn] created empty hub_rank.csv (header only)")
    else:
        print("[warn] hub_rank.csv remains header-only (no source)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
