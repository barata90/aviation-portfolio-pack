#!/usr/bin/env python3
"""
Create small placeholder assets referenced by docs so MkDocs --strict won't fail.
Only creates if missing.
"""
from __future__ import annotations
from pathlib import Path
import json

ROOT = Path("docs")
ASSETS = ROOT / "assets"
API = ROOT / "api"

def write_png(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    # 1x1 transparent PNG
    png = bytes.fromhex(
        "89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C489"
        "0000000A49444154789C6360000002000100FFFF03000006000557BF2A00000000"
        "49454E44AE426082"
    )
    path.write_bytes(png)

def main():
    # downloads.md expects these:
    (ASSETS / "hub_rank.csv").parent.mkdir(parents=True, exist_ok=True)
    if not (ASSETS / "hub_rank.csv").exists():
        (ASSETS / "hub_rank.csv").write_text("hub,score\nDXB,100\n", encoding="utf-8")
        print("[created] assets/hub_rank.csv")

    API.mkdir(parents=True, exist_ok=True)
    if not (API / "euro_atfm_timeseries_last24.json").exists():
        (API / "euro_atfm_timeseries_last24.json").write_text(
            json.dumps({"status":"placeholder","note":"replace with real export if available","series":[]}, indent=2),
            encoding="utf-8"
        )
        print("[created] api/euro_atfm_timeseries_last24.json")

    # visual_insights.md & pages/airport_degree.md expect images:
    for p in [
        ASSETS / "ops_delay_24m_advanced.png",
        ASSETS / "ops_delay_top_locations_smallmultiples.png",
        ASSETS / "network_degree_top20.png",
        ASSETS / "airport_degree" / "top15_degree.png",
        ASSETS / "airport_degree" / "degree_hist.png",
    ]:
        if not p.exists():
            write_png(p)
            print(f"[created] {p.relative_to(ROOT)}")

if __name__ == "__main__":
    raise SystemExit(main())
