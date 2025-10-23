#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

p = Path("docs/assets/datasets.json")
if not p.exists():
    print("datasets.json not found; nothing to fix"); raise SystemExit(0)
data = json.loads(p.read_text(encoding="utf-8"))

def fix_obj(o):
    if isinstance(o, dict):
        for k,v in list(o.items()):
            if isinstance(v, str) and v.startswith("/publish/"):
                o[k] = v[1:]
        for v in o.values(): fix_obj(v)
    elif isinstance(o, list):
        for v in o: fix_obj(v)

fix_obj(data)
p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print("fixed:", p)
