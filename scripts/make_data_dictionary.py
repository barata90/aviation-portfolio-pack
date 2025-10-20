#!/usr/bin/env python3
"""
Generate a Markdown data dictionary dari:
  - CSV dalam sebuah folder (mis. publish/)
  - DuckDB database (opsional) untuk tabel-tabel tertentu

Contoh pakai:
  python scripts/make_data_dictionary.py \
    --csv-dir publish \
    --duckdb warehouse_local/otp.duckdb \
    --tables route_counts,airport_degree,euro_atfm_timeseries,euro_atfm_by_location \
    --out docs/data_dictionary.md
"""

import argparse, os, sys, textwrap, datetime, pathlib
from typing import List, Dict, Optional
import duckdb
import pandas as pd

NUMERIC_KEYWORDS = ("INT", "DECIMAL", "DOUBLE", "REAL", "HUGEINT", "UBIGINT", "UTINYINT", "USMALLINT", "UINTEGER")
DATETIME_KEYWORDS = ("DATE", "TIME", "TIMESTAMP")

def is_numeric(duck_type: str) -> bool:
    t = duck_type.upper()
    return any(k in t for k in NUMERIC_KEYWORDS)

def is_datetime(duck_type: str) -> bool:
    t = duck_type.upper()
    return any(k in t for k in DATETIME_KEYWORDS)

def qident(name: str) -> str:
    # Quote identifier for SQL (simple double-quote; assumes ASCII names are fine)
    return '"' + name.replace('"', '""') + '"'

def ensure_parent(path: str):
    pathlib.Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)

def preview_markdown(df: pd.DataFrame, max_rows: int = 5) -> str:
    df2 = df.head(max_rows).copy()
    # Keep small width
    return df2.to_markdown(index=False)

def describe_relation(con: duckdb.DuckDBPyConnection, rel_sql: str, src_label: str) -> Dict:
    """
    rel_sql: e.g. read_csv_auto('path', header=true)  OR  (SELECT * FROM my_table)
    Returns dict with: row_count, columns: [{name, type, stats, topk}]
    """
    # Get schema via DESCRIBE
    desc = con.execute(f"DESCRIBE SELECT * FROM {rel_sql}").df()
    cols = [{"name": r["column_name"], "type": r["column_type"]} for _, r in desc.iterrows()]

    # Row count
    n_rows = con.execute(f"SELECT COUNT(*) FROM {rel_sql}").fetchone()[0]

    # Preview
    prev = con.execute(f"SELECT * FROM {rel_sql} LIMIT 5").df()

    # Column stats
    out_cols = []
    for c in cols:
        name = c["name"]
        dtype = c["type"]
        col_sql = f"{rel_sql}"
        stats = {}
        # nulls & distinct
        stats_df = con.execute(
            f"""
            SELECT 
              COUNT(*) AS n_total,
              (COUNT(*) - COUNT({qident(name)}))::BIGINT AS n_nulls,
              COUNT(DISTINCT {qident(name)})::BIGINT AS n_distinct
            FROM {col_sql}
            """
        ).df().iloc[0]
        stats["n_total"] = int(stats_df["n_total"])
        stats["n_nulls"] = int(stats_df["n_nulls"])
        stats["n_distinct"] = int(stats_df["n_distinct"])

        if is_numeric(dtype):
            num_df = con.execute(
                f"""
                SELECT 
                  MIN({qident(name)}) AS min_v,
                  MAX({qident(name)}) AS max_v,
                  AVG({qident(name)}) AS avg_v
                FROM {col_sql}
                """
            ).df().iloc[0]
            stats["min"] = num_df["min_v"]
            stats["max"] = num_df["max_v"]
            stats["avg"] = float(num_df["avg_v"]) if pd.notna(num_df["avg_v"]) else None
            topk_list = []  # for numeric, show no topk by default
        elif is_datetime(dtype):
            dt_df = con.execute(
                f"""
                SELECT 
                  MIN({qident(name)}) AS min_v,
                  MAX({qident(name)}) AS max_v
                FROM {col_sql}
                """
            ).df().iloc[0]
            stats["min"] = dt_df["min_v"]
            stats["max"] = dt_df["max_v"]
            stats["avg"] = None
            topk_list = []
        else:
            # text-ish: show top-5 values
            try:
                topk_df = con.execute(
                    f"""
                    SELECT {qident(name)} AS val, COUNT(*) AS c
                    FROM {col_sql}
                    GROUP BY 1
                    ORDER BY c DESC NULLS LAST, val
                    LIMIT 5
                    """
                ).df()
                topk_list = [f"{str(v)} ({int(c)})" for v, c in zip(topk_df["val"], topk_df["c"])]
            except Exception:
                topk_list = []

            stats["min"] = None
            stats["max"] = None
            stats["avg"] = None

        out_cols.append({
            "name": name,
            "type": dtype,
            "stats": stats,
            "topk": topk_list
        })

    return {
        "source": src_label,
        "row_count": int(n_rows),
        "preview": prev,
        "columns": out_cols
    }

def dict_to_markdown(title: str, dd: Dict) -> str:
    lines = []
    lines.append(f"### {title}")
    lines.append("")
    lines.append(f"- **Source**: {dd['source']}")
    lines.append(f"- **Rows**: {dd['row_count']}")
    lines.append("")
    lines.append("**Preview (first 5 rows)**")
    lines.append("")
    try:
        lines.append(preview_markdown(dd["preview"]))
    except Exception:
        lines.append("_preview not available_")
    lines.append("")

    header = ["#", "Column", "DuckDB Type", "Nulls", "Distinct", "Min", "Max", "Mean/Examples"]
    rows = []
    for i, col in enumerate(dd["columns"], start=1):
        s = col["stats"]
        if col["topk"]:
            mean_or_ex = "; ".join(col["topk"])
        else:
            mean_or_ex = (f"{s['avg']:.4f}" if isinstance(s.get("avg"), (int, float)) and s["avg"] is not None else "")
        rows.append([
            i,
            col["name"],
            col["type"],
            s["n_nulls"],
            s["n_distinct"],
            "" if s["min"] is None else s["min"],
            "" if s["max"] is None else s["max"],
            mean_or_ex
        ])

    try:
        md_table = pd.DataFrame(rows, columns=header).to_markdown(index=False)
    except Exception:
        # fallback
        md_table = "\n".join([" | ".join(map(str, header))] + [" | ".join(map(str, r)) for r in rows])

    lines.append(md_table)
    lines.append("")
    return "\n".join(lines)

def main():
    ap = argparse.ArgumentParser(description="Generate Markdown data dictionary for CSV folder & DuckDB tables.")
    ap.add_argument("--csv-dir", type=str, default=None, help="Folder berisi CSV (mis. publish/)")
    ap.add_argument("--duckdb", type=str, default=None, help="Path DuckDB (mis. warehouse_local/otp.duckdb)")
    ap.add_argument("--tables", type=str, default="", help="Comma-separated list tabel DuckDB yang mau didokumentasi")
    ap.add_argument("--out", type=str, default="docs/data_dictionary.md", help="Output Markdown path")
    args = ap.parse_args()

    ensure_parent(args.out)

    sections = []
    con = duckdb.connect(args.duckdb) if args.duckdb else duckdb.connect(":memory:")

    # 1) CSVs
    if args.csv_dir:
        csv_dir = pathlib.Path(args.csv_dir)
        if not csv_dir.exists():
            print(f"[WARN] CSV dir {csv_dir} tidak ditemukan, skip.", file=sys.stderr)
        else:
            csv_files = sorted([p for p in csv_dir.glob("*.csv")])
            for p in csv_files:
                path_escaped = str(p).replace("'", "''")  # escape single-quote untuk SQL string
                rel = f"read_csv_auto('{path_escaped}', header=true)"
                dd = describe_relation(con, rel, f"CSV: {p}")
                sections.append(dict_to_markdown(p.name, dd))

    # 2) DuckDB tables
    if args.duckdb and args.tables.strip():
        wanted = [t.strip() for t in args.tables.split(",") if t.strip()]
        for t in wanted:
            rel = f"(SELECT * FROM {qident(t)})"
            dd = describe_relation(con, rel, f"DuckDB table: {t}")
            sections.append(dict_to_markdown(f"{t} (DuckDB)", dd))

    # Assemble markdown
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    header = textwrap.dedent(f"""\
    # Data Dictionary

    _Generated: {now}_

    Dokumen ini berisi ringkasan struktur & statistik kolom untuk dataset yang dipakai di portfolio.

    ---
    """)
    content = header + "\n\n".join(sections) + "\n"
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[OK] Data dictionary ditulis ke: {args.out}")

if __name__ == "__main__":
    main()