#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import base64
import json

ROOT = Path("docs")
ASSETS = ROOT / "assets"
API = ROOT / "api"

PNG_MINI = base64.b64decode(
    # 1x1 PNG transparan
    b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHWgKf5Q8cTQAAAABJRU5ErkJggg=='
)

def ensure_file(path: Path, data: bytes | str):
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str):
        if not path.exists():
            path.write_text(data, encoding="utf-8")
    else:
        if not path.exists():
            path.write_bytes(data)

def main() -> int:
    # CSV placeholder (download page)
    ensure_file(ASSETS / "hub_rank.csv", "airport,score\nDXB,100\nLHR,95\nSIN,93\n")

    # API placeholder json (download page)
    API.mkdir(parents=True, exist_ok=True)
    if not (API / "euro_atfm_timeseries_last24.json").exists():
        (API / "euro_atfm_timeseries_last24.json").write_text(
            json.dumps({"status":"placeholder","series":[]}, indent=2), encoding="utf-8"
        )

    # Images used by case studies (prevent strict warnings)
    for name in [
        "ops_delay_24m_advanced.png",
        "ops_delay_top_locations_smallmultiples.png",
        "network_degree_top20.png",
    ]:
        ensure_file(ASSETS / name, PNG_MINI)

    # If any “pages/airport_degree.md” references images under assets/airport_degree/…
    # make the folder and tiny pngs as well (harmless if unused).
    sub = ASSETS / "airport_degree"
    for n in ["top15_degree.png", "degree_hist.png"]:
        ensure_file(sub / n, PNG_MINI)

    print("Placeholder assets ensured.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
