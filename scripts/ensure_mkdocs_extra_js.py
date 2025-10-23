<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> 52085bf (CI/site hardening: stable pages build; datasets index; Agg backend; 24M filter; instant-nav & cache-bust; mkdocs YAML repair)
#!/usr/bin/env python3
"""
Idempotently ensure mkdocs.yml contains:
extra_javascript:
  - assets/site_hooks.js
"""
from __future__ import annotations
from pathlib import Path
import yaml

MK = Path("mkdocs.yml")
data = yaml.safe_load(MK.read_text(encoding="utf-8")) or {}
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

MK.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
print("Ensured mkdocs.yml has extra_javascript: assets/site_hooks.js")
<<<<<<< HEAD
=======
<PASTE_ENSURE_JS_PY>
>>>>>>> 9fd5aca (CI/site hardening: stable pages build; datasets index; Agg backend; 24M filter; instant-nav & cache-bust; mkdocs YAML repair)
=======
>>>>>>> 52085bf (CI/site hardening: stable pages build; datasets index; Agg backend; 24M filter; instant-nav & cache-bust; mkdocs YAML repair)
