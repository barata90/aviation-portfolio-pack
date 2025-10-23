#!/usr/bin/env python3
from pathlib import Path
import base64

png1x1 = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO3L4ZkAAAAASUVORK5CYII=")

targets = [
    Path("docs/assets/airport_degree/top15_degree.png"),
    Path("docs/assets/airport_degree/degree_hist.png"),
]
for f in targets:
    f.parent.mkdir(parents=True, exist_ok=True)
    if not f.exists():
        f.write_bytes(png1x1)
        print("created", f)
print("placeholders ok")
