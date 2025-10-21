#!/usr/bin/env python3
import os
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt

DOCS_DIR = Path("docs")
PAGES_DIR = DOCS_DIR / "pages"
ASSETS_DIR = DOCS_DIR / "assets"
CSV_DIR = Path("publish")

DOCS_DIR.mkdir(exist_ok=True)
PAGES_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

def write_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def md_table(df: pd.DataFrame, n=10) -> str:
    try:
        return df.head(n).to_markdown(index=False)
    except Exception:
        return "```\n" + df.head(n).to_string(index=False) + "\n```"

def first_numeric_col(df: pd.DataFrame, exclude=None):
    exclude = set(exclude or [])
    for c in df.columns:
        if c in exclude: continue
        if pd.api.types.is_numeric_dtype(df[c]):
            return c
    return None

def detect_date_col(df: pd.DataFrame):
    for c in ["date","day","dt","timestamp"]:
        if c in df.columns:
            s = pd.to_datetime(df[c], errors="coerce")
            if s.notna().any():
                df[c] = s
                return c
    for c in df.columns:
        if df[c].dtype == "object":
            s = pd.to_datetime(df[c], errors="coerce")
            if s.notna().sum() > 0:
                df[c] = s
                return c
    return None

def save_hist(df: pd.DataFrame, col: str, title: str, fname: str):
    s = df[col].dropna()
    if s.empty: return None
    plt.figure()
    s.plot(kind="hist", bins=30)
    plt.title(title); plt.xlabel(col); plt.tight_layout()
    out = ASSETS_DIR / fname; plt.savefig(out, dpi=150); plt.close()
    return f"assets/{fname}"

def save_line(df: pd.DataFrame, date_col: str, value_col: str, title: str, fname: str):
    d = df[[date_col, value_col]].dropna()
    if d.empty: return None
    d = d.groupby(pd.to_datetime(d[date_col]).dt.date)[value_col].sum().reset_index()
    if d.empty: return None
    plt.figure()
    plt.plot(d[date_col], d[value_col])
    plt.title(title); plt.xlabel("Date"); plt.ylabel(value_col)
    plt.xticks(rotation=45, ha="right"); plt.tight_layout()
    out = ASSETS_DIR / fname; plt.savefig(out, dpi=150); plt.close()
    return f"assets/{fname}"

def summarize_numeric(df: pd.DataFrame) -> str:
    num = df.select_dtypes(include="number")
    if num.empty: return "_Tidak ada kolom numerik yang bisa dirangkum._"
    try:
        return num.describe().T.to_markdown()
    except Exception:
        return "```\n" + num.describe().T.to_string() + "\n```"

def title_from_csv(csv_path: Path) -> str:
    return csv_path.stem.replace("_", " ").title()

def make_page_for_csv(csv_path: Path) -> str:
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        try:
            df = pd.read_csv(csv_path, sep=";")
        except Exception:
            page = PAGES_DIR / f"{csv_path.stem}.md"
            write_text(page, f"# {title_from_csv(csv_path)}\n\n_Gagal membaca CSV_: {e}\n")
            return f"pages/{csv_path.stem}.md"

    title = title_from_csv(csv_path)
    page_path = PAGES_DIR / f"{csv_path.stem}.md"

    md = [f"# {title}\n"]
    md.append(f"- **File sumber**: `publish/{csv_path.name}`")
    md.append(f"- **Rows x Cols**: `{df.shape[0]} x {df.shape[1]}`")
    md.append(f"- **Columns**: {', '.join(map(str, df.columns.tolist()))}\n")

    md.append("## Ringkasan numerik")
    md.append(summarize_numeric(df) + "\n")

    md.append("## Sampel data")
    md.append(md_table(df, n=10) + "\n")

    num_col = first_numeric_col(df)
    if num_col:
        img = save_hist(df, num_col, f"Distribusi {num_col}", f"{csv_path.stem}__hist_{num_col}.png")
        if img:
            md.append(f"## Histogram `{num_col}`\n\n![{num_col}]({img})\n")

    date_col = detect_date_col(df)
    if date_col and num_col:
        img2 = save_line(df, date_col, num_col, f"Tren harian {num_col}", f"{csv_path.stem}__line_{num_col}.png")
        if img2:
            md.append(f"## Tren harian (`{date_col}` vs `{num_col}`)\n\n![trend]({img2})\n")

    write_text(page_path, "\n".join(md))
    return f"pages/{csv_path.stem}.md"

def build_index(pages_rel_paths):
    badge = "[![Build data dictionary](https://github.com/barata90/aviation-portfolio-pack/actions/workflows/build.yml/badge.svg)](https://github.com/barata90/aviation-portfolio-pack/actions/workflows/build.yml)"
    lines = [
        "# Aviation Portfolio Pack",
        "",
        badge,
        "",
        "Situs portfolio ini dirender otomatis dari CSV di folder `publish/`.",
        "",
        "## Navigasi cepat",
        "- [Data dictionary](data_dictionary.md)",
        "",
        "## Halaman dataset",
    ]
    for rel in sorted(pages_rel_paths):
        nm = Path(rel).stem.replace("_", " ").title()
        lines.append(f"- [{nm}]({rel})")
    write_text(DOCS_DIR / "index.md", "\n".join(lines) + "\n")

def main():
    csvs = sorted(CSV_DIR.glob("*.csv"))
    page_paths = [make_page_for_csv(c) for c in csvs]
    build_index(page_paths)
    print(f"[OK] Generated {len(page_paths)} pages under docs/pages/ and updated docs/index.md")

if __name__ == "__main__":
    main()
