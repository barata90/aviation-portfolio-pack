<<<<<<< HEAD
#!/usr/bin/env python3
"""
Safely repair mkdocs.yml:
- Parse YAML
- Ensure extra_javascript is a list containing 'assets/site_hooks.js'
- Write back (preserve order)
"""
from __future__ import annotations
from pathlib import Path
import sys
import yaml

MKDOCS = Path("mkdocs.yml")
if not MKDOCS.exists():
    sys.exit("mkdocs.yml not found")

data = yaml.safe_load(MKDOCS.read_text(encoding="utf-8")) or {}
if not isinstance(data, dict):
    data = {}

ej = data.get("extra_javascript")
if ej is None:
    ej = []
elif isinstance(ej, (str, bytes)):
    ej = [ej.decode() if isinstance(ej, bytes) else ej]
elif isinstance(ej, tuple):
    ej = list(ej)
elif not isinstance(ej, list):
    ej = [str(ej)]

target = "assets/site_hooks.js"
if target not in ej:
    ej.append(target)
data["extra_javascript"] = ej

MKDOCS.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
print("mkdocs.yml repaired and ensured extra_javascript includes assets/site_hooks.js")
=======
<PASTE_REPAIR_YAML_PY>
>>>>>>> 9fd5aca (CI/site hardening: stable pages build; datasets index; Agg backend; 24M filter; instant-nav & cache-bust; mkdocs YAML repair)
