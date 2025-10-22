#!/usr/bin/env python3
from __future__ import annotations
import os, json, csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLISH = ROOT / "publish"
ASSETS = ROOT / "docs" / "assets"
SCHEMA_DIR = ASSETS / "schema"
DATASETS_JSON = ASSETS / "datasets.json"

def header_columns(csv_path: Path) -> list[str]:
    with open(csv_path, "r", encoding="utf-8-sig", errors="replace", newline="") as f:
        row = next(csv.reader(f), [])
    cols = [ (c or "").strip() for c in row if c is not None ]
    seen, out = set(), []
    for c in cols or ["column"]:
        base = c or "column"
        name, i = base, 2
        while name in seen:
            name = f"{base}_{i}"
            i += 1
        seen.add(name)
        out.append(name)
    return out

def row_count(csv_path: Path) -> int:
    with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
        n = sum(1 for _ in f)
    return max(0, n-1)

def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    items = []
    for csv_path in sorted(PUBLISH.glob("*.csv")):
        cols = header_columns(csv_path)
        rc = row_count(csv_path)
        st = csv_path.stat()
        items.append({
            "name": csv_path.name,
            "path": f"/publish/{csv_path.name}",
            "columns": cols,
            "row_count": rc,
            "bytes": st.st_size,
            "last_modified": int(st.st_mtime),
        })
        with open(SCHEMA_DIR / (csv_path.stem + ".columns.json"), "w", encoding="utf-8") as w:
            json.dump({"columns": cols}, w, indent=2)
    with open(DATASETS_JSON, "w", encoding="utf-8") as w:
        json.dump(items, w, indent=2)
    print(f"Wrote {DATASETS_JSON} with {len(items)} dataset(s).")

if __name__ == "__main__":
    main()
