*** Begin Patch
*** Update File: scripts/ensure_mkdocs_extra_js.py
+#!/usr/bin/env python3
+"""
+Ensure mkdocs.yml has a valid top-level `extra_javascript` entry containing
+`assets/site_hooks.js` (path is relative to docs_dir). Works with:
+ - missing `extra_javascript` -> creates block list
+ - existing block list -> appends item if missing
+ - existing inline list -> appends item if missing
+Also upgrades any legacy 'docs/assets/site_hooks.js' to 'assets/site_hooks.js'.
+Idempotent and stdlib-only.
+"""
+from __future__ import annotations
+import re
+from pathlib import Path
+
+TARGET = "assets/site_hooks.js"
+LEGACY = "docs/assets/site_hooks.js"
+
+p = Path("mkdocs.yml")
+if not p.exists():
+    raise SystemExit("mkdocs.yml not found")
+
+text = p.read_text(encoding="utf-8")
+
+# Upgrade legacy reference if present
+if LEGACY in text and TARGET not in text:
+    text = text.replace(LEGACY, TARGET)
+    p.write_text(text, encoding="utf-8")
+    print(f"Replaced legacy path '{LEGACY}' with '{TARGET}'.")
+
+if TARGET in text:
+    print(f"Found {TARGET}; nothing to do.")
+    raise SystemExit(0)
+
+lines = text.splitlines()
+
+# Find top-level 'extra_javascript'
+ej_idx = None
+for i, ln in enumerate(lines):
+    if re.match(r'^extra_javascript\s*:', ln):
+        ej_idx = i
+        break
+
+def write_and_exit(new_lines):
+    p.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
+    print(f"Ensured extra_javascript includes {TARGET}")
+    raise SystemExit(0)
+
+if ej_idx is None:
+    add = ["", "extra_javascript:", f"  - {TARGET}"]
+    write_and_exit(lines + add)
+
+line = lines[ej_idx]
+m_inline = re.match(r'^extra_javascript\s*:\s*\[(.*)\]\s*$', line)
+if m_inline:
+    inside = m_inline.group(1).strip()
+    items = []
+    if inside:
+        raw = [x.strip() for x in inside.split(",")]
+        for x in raw:
+            items.append(x.strip().strip('"').strip("'"))
+    if TARGET not in items:
+        items.append(TARGET)
+    lines[ej_idx] = "extra_javascript: [" + ", ".join(items) + "]"
+    write_and_exit(lines)
+
+# Block list case
+i = ej_idx + 1
+inserted = False
+if i >= len(lines) or not re.match(r'^\s*-\s+', lines[i]):
+    lines.insert(i, f"  - {TARGET}")
+    inserted = True
+else:
+    while i < len(lines):
+        ln = lines[i]
+        if re.match(r'^\s*-\s+', ln):
+            if TARGET in ln:
+                inserted = True
+                break
+            i += 1
+            continue
+        if ln.strip() == "":
+            i += 1
+            continue
+        break
+    if not inserted:
+        lines.insert(i, f"  - {TARGET}")
+        inserted = True
+
+write_and_exit(lines)
*** End Patch
