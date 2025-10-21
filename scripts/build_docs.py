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
        if c in exclude:
            continue
        if pd.api.types.is_numeric_dtype(df[c]):
            return c
    return None

def detect_date_col(df: pd.DataFrame):
    """Cari kolom tanggal & konversi ke datetime bila ada."""
    # kandidat umum
    for c in ["date", "day", "dt", "timestamp", "period_start", "period_end"]:
        if c in df.columns:
            s = pd.to_datetime(df[c], errors="coerce", utc=False)
            if s.notna().any():
                df[c] = s
                return c
    # fallback: scan object columns
    for c in df.columns:
        if df[c].dtype == "object":
            s = pd.to_datetime(df[c], errors="coerce", utc=False)
            if s.notna().sum() > 0:
                df[c] = s
                return c
    return None

def compute_coverage(df: pd.DataFrame, date_col: str):
    s = pd.to_datetime(df[date_col], errors="coerce")
    s = s.dropna()
    if s.empty:
        return None, None
    return s.min().date(), s.max().date()

def filter_last_two_years(df: pd.DataFrame, date_col: str):
    """Kembalikan df_view (2 tahun terakhir) + tanggal start/end view."""
    s = pd.to_datetime(df[date_col], errors="coerce")
    s = s.dropna()
    if s.empty:
        return df, None, None

    max_dt = s.max()
    cutoff = max_dt - pd.DateOffset(years=2)
    df_view = df[df[date_col] >= cutoff].copy()
    if df_view.empty:
        # kalau aneh (mis. kurang data), pakai semua
        return df, None, None

    v = pd.to_datetime(df_view[date_col], errors="coerce").dropna()
    v_start = v.min().date() if not v.empty else None
    v_end = v.max().date() if not v.empty else None
    return df_view, v_start, v_end

def save_hist(df: pd.DataFrame, col: str, title: str, fname: str):
    s = df[col].dropna()
    if s.empty:
        return None
    plt.figure()
    s.plot(kind="hist", bins=30)
    plt.title(title)
    plt.xlabel(col)
    plt.tight_layout()
    out = ASSETS_DIR / fname
    plt.savefig(out, dpi=150)
    plt.close()
    return f"assets/{fname}"

def save_line(df: pd.DataFrame, date_col: str, value_col: str, title: str, fname: str):
    d = df[[date_col, value_col]].dropna()
    if d.empty:
        return None
    d = (
        d.groupby(pd.to_datetime(d[date_col]).dt.date)[value_col]
        .sum()
        .reset_index()
        .sort_values(date_col)
    )
    if d.empty:
        return None
    plt.figure()
    plt.plot(d[date_col], d[value_col])
    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel(value_col)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    out = ASSETS_DIR / fname
    plt.savefig(out, dpi=150)
    plt.close()
    return f"assets/{fname}"

def summarize_numeric(df: pd.DataFrame) -> str:
    num = df.select_dtypes(include="number")
    if num.empty:
        return "_Tidak ada kolom numerik yang bisa dirangkum._"
    try:
        return num.describe().T.to_markdown()
    except Exception:
        return "```\n" + num.describe().T.to_string() + "\n```"

def title_from_csv(csv_path: Path) -> str:
    return csv_path.stem.replace("_", " ").title()

def make_page_for_csv(csv_path: Path) -> str:
    # --- load CSV ---
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

    # --- deteksi kolom tanggal + coverage + filter 2 tahun terakhir ---
    date_col = detect_date_col(df)
    cov_min, cov_max = (None, None)
    df_view = df.copy()
    view_start, view_end = (None, None)

    if date_col:
        cov_min, cov_max = compute_coverage(df, date_col)
        df_view, view_start, view_end = filter_last_two_years(df, date_col)

    # --- header info ---
    md = [f"# {title}\n"]
    md.append(f"- **File sumber**: `publish/{csv_path.name}`")
    md.append(f"- **Rows x Cols**: `{df_view.shape[0]} x {df_view.shape[1]}`")
    md.append(f"- **Columns**: {', '.join(map(str, df_view.columns.tolist()))}")

    if date_col:
        if cov_min and cov_max:
            md.append(f"- **Periode data (di file)**: `{cov_min} — {cov_max}`")
        if view_start and view_end:
            md.append(f"- **Ditampilkan**: _2 tahun terakhir_ → `{view_start} — {view_end}`")
        else:
            md.append("- **Ditampilkan**: seluruh periode (data < 2 tahun)")

    md.append("")  # spacer

    # --- ringkasan numerik & sampel (berdasarkan df_view) ---
    md.append("## Ringkasan numerik")
    md.append(summarize_numeric(df_view) + "\n")

    md.append("## Sampel data")
    md.append(md_table(df_view, n=10) + "\n")

    # --- visualisasi ---
    num_col = first_numeric_col(df_view, exclude=[date_col] if date_col else None)
    if num_col:
        img = save_hist(
            df_view, num_col, f"Distribusi {num_col}", f"{csv_path.stem}__hist_{num_col}.png"
        )
        if img:
            md.append(f"## Histogram `{num_col}`\n\n![{num_col}]({img})\n")

    if date_col and num_col:
        img2 = save_line(
            df_view,
            date_col,
            num_col,
            f"Tren harian {num_col}",
            f"{csv_path.stem}__line_{num_col}.png",
        )
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
