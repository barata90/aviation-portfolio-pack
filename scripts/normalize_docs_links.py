#!/usr/bin/env python3
"""
Normalize internal links so MkDocs --strict won't fail.

Rules:
- Untuk semua file di docs/ (Markdown/HTML):
  * ](/assets/...)  → ](REL/assets/...)
  * ](/publish/...) → ](REL/publish/...)
  * src="/assets/..."  → src="REL/assets/..."
  * href="/assets/..." → href="REL/assets/..."
  * src="/publish/..." → src="REL/publish/..."
  * href="/publish/..."→ href="REL/publish/..."
- Khusus halaman datasets (docs/datasets/*.md):
  * '{{ base_url }}/assets/plots/'  → '../assets/plots/'
  * '{{ base_url }}/publish/'       → '../publish/'
- Khusus case study Emirates:
  * '../pages/(euro_*.md|top_od_pairs.md)' → '../datasets/...md'
Idempotent (aman dijalankan berkali-kali).
"""
from __future__ import annotations
import re
from pathlib import Path

DOCS = Path("docs")

def rel_from(p: Path) -> str:
    # hitung prefix relatif dari file p ke root docs/
    depth = len(p.relative_to(DOCS).parts) - 1
    return "../" * depth if depth > 0 else ""

def normalize_text(txt: str, prefix: str, path: Path) -> str:
    out = txt

    # Markdown link/image absolut → relatif
    out = re.sub(r'\]\(/assets/', f']({prefix}assets/', out)
    out = re.sub(r'\]\(/publish/', f']({prefix}publish/', out)
    out = re.sub(r'!\[\]\(/assets/', f'![]({prefix}assets/', out)
    out = re.sub(r'!\[\]\(/publish/', f'![]({prefix}publish/', out)

    # HTML atribut absolut → relatif
    out = re.sub(r'src="/assets/', f'src="{prefix}assets/', out)
    out = re.sub(r'href="/assets/', f'href="{prefix}assets/', out)
    out = re.sub(r'src="/publish/', f'src="{prefix}publish/', out)
    out = re.sub(r'href="/publish/', f'href="{prefix}publish/', out)

    # Dataset pages: hapus {{ base_url }} menjadi relatif
    if str(path).startswith(str(DOCS / "datasets")):
        out = out.replace("{{ base_url }}/assets/plots/", "../assets/plots/")
        out = out.replace("{{ base_url }}/publish/", "../publish/")

    # Case study emirates: ubah link ke datasets/
    if path.name == "emirates_data_analytics_specialist.md":
        out = out.replace("../pages/euro_atfm_timeseries.md", "../datasets/euro_atfm_timeseries.md")
        out = out.replace("../pages/euro_atfm_by_location.md", "../datasets/euro_atfm_by_location.md")
        out = out.replace("../pages/top_od_pairs.md", "../datasets/top_od_pairs.md")

    return out

def main() -> int:
    if not DOCS.exists():
        print("docs/ not found; nothing to normalize")
        return 0
    changed = 0
    for p in DOCS.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in {".md", ".html"}:
            continue
        before = p.read_text(encoding="utf-8", errors="ignore")
        after = normalize_text(before, rel_from(p), p)
        if after != before:
            p.write_text(after, encoding="utf-8")
            changed += 1
            print(f"[fixed] {p}")
    print(f"Normalized links in {changed} file(s).")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
