<<<<<<< HEAD
#!/usr/bin/env python3
"""
Write docs/assets/datasets.json listing exactly publish/*.csv.

Format:
{
  "datasets": [
    {"name": "table_name", "path": "publish/table_name.csv"}
  ]
}
"""
from __future__ import annotations
from pathlib import Path
import json

PUBLISH = Path("publish")
OUT = Path("docs/assets/datasets.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

datasets = []
for p in sorted(PUBLISH.glob("*.csv")):
    datasets.append({"name": p.stem, "path": f"publish/{p.name}"})  # no leading slash

OUT.write_text(json.dumps({"datasets": datasets}, indent=2), encoding="utf-8")
print(f"Wrote {OUT} with {len(datasets)} dataset(s).")
=======
<PASTE_DATASETS_INDEX_PY>
>>>>>>> 9fd5aca (CI/site hardening: stable pages build; datasets index; Agg backend; 24M filter; instant-nav & cache-bust; mkdocs YAML repair)
