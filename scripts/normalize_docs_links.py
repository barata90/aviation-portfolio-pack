#!/usr/bin/env python3
"""
Normalize internal links so MkDocs --strict won't fail:

- Markdown links/images starting with /assets/ or /publish/ -> {{ base_url }}/assets|publish
- HTML <img|script|a> src|href starting with /assets/ or /publish/ -> {{ base_url }}/...

Idempotent (safe to run multiple times).
"""
from __future__ import annotations
import re
from pathlib import Path

DOCS = Path("docs")
BASE = "{{ base_url }}"

MD_PATTERNS = [
    # Markdown link/image: ](/assets/...) or ](/publish/...)
    (re.compile(r'\]\(/assets/'), f']({BASE}/assets/'),
    ),
    (re.compile(r'\]\(/publish/'), f']({BASE}/publish/'),
    ),
    # Markdown image: ![](/assets/...) or ![](/publish/...)
    (re.compile(r'!\[\]\(/assets/'), f'![]({BASE}/assets/'),
    ),
    (re.compile(r'!\[[^\]]*\]\(/assets/'), f'![']({BASE}/assets/'),  # handled by first pattern anyway
    ),
    (re.compile(r'!\[\]\(/publish/'), f'![]({BASE}/publish/'),
    ),
]

HTML_PATTERNS = [
    # src="/assets/..."  -> src="{{ base_url }}/assets/..."
    (re.compile(r'src="/assets/'), f'src="{BASE}/assets/'),
    (re.compile(r'href="/assets/'), f'href="{BASE}/assets/'),
    (re.compile(r'src="/publish/'), f'src="{BASE}/publish/'),
    (re.compile(r'href="/publish/'), f'href="{BASE}/publish/'),
]

def normalize_text(txt: str) -> str:
    out = txt
    for pat, repl in MD_PATTERNS:
        out = pat.sub(repl, out)
    for pat, repl in HTML_PATTERNS:
        out = pat.sub(repl, out)
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
        after = normalize_text(before)
        if after != before:
            p.write_text(after, encoding="utf-8")
            changed += 1
            print(f"[fixed] {p}")
    print(f"Normalized links in {changed} file(s).")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
