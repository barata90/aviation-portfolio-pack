#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re

DOCS = Path("docs")

# Ganti link .. /pages/<name>.md -> .. /datasets/<name>.md (khusus di case_studies)
def fix_case_studies_links(text: str) -> str:
    # markdown link: [label](../pages/foo.md)  -> [label](../datasets/foo.md)
    text = re.sub(r'\((\.\./)pages/([A-Za-z0-9_\-]+)\.md\)', r'(\1datasets/\2.md)', text)
    return text

def main() -> int:
    cs_dir = DOCS / "case_studies"
    if not cs_dir.exists():
        print("No docs/case_studies, nothing to normalize.")
        return 0

    changed = 0
    for md in cs_dir.glob("*.md"):
        before = md.read_text(encoding="utf-8", errors="ignore")
        after = fix_case_studies_links(before)
        if after != before:
            md.write_text(after, encoding="utf-8")
            changed += 1
            print(f"[normalized] {md}")
    print(f"Normalized {changed} file(s).")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
