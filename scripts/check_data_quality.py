#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import numpy as np

CSV_DIR = Path("publish")
DOCS_DIR = Path("docs")
ASSETS = DOCS_DIR / "assets"
REPORT = DOCS_DIR / "quality_report.md"
ASSETS.mkdir(parents=True, exist_ok=True)

def profile_df(df: pd.DataFrame):
    prof = []
    for c in df.columns:
        s = df[c]
        nulls = int(s.isna().sum())
        null_pct = float(nulls) / max(len(s), 1) * 100
        dtype = str(s.dtype)
        dup = 0
        if df.columns.duplicated().any():
            pass
        # simple duplicate check on entire row set (heavy for big data; OK for small CSVs)
    prof = pd.DataFrame({
        "column": df.columns,
        "dtype": [str(df[c].dtype) for c in df.columns],
        "nulls": [int(df[c].isna().sum()) for c in df.columns],
        "null_pct": [float(df[c].isna().mean()*100) for c in df.columns],
        "min": [pd.to_datetime(df[c], errors="coerce").min() if np.issubdtype(df[c].dtype, np.datetime64)
                else (df[c].min() if pd.api.types.is_numeric_dtype(df[c]) else None) for c in df.columns],
        "max": [pd.to_datetime(df[c], errors="coerce").max() if np.issubdtype(df[c].dtype, np.datetime64)
                else (df[c].max() if pd.api.types.is_numeric_dtype(df[c]) else None) for c in df.columns],
        "unique": [df[c].nunique(dropna=True) for c in df.columns],
    })
    return prof

def to_md_table(df: pd.DataFrame) -> str:
    try:
        return df.to_markdown(index=False)
    except Exception:
        return "```\n" + df.to_string(index=False) + "\n```"

def main():
    lines = ["# Data Quality Report", ""]
    status_ok = True
    for csv in sorted(CSV_DIR.glob("*.csv")):
        try:
            df = pd.read_csv(csv)
        except Exception:
            try:
                df = pd.read_csv(csv, sep=";")
            except Exception as e:
                lines += [f"## {csv.name}", f"_Gagal baca CSV_: {e}", ""]
                status_ok = False
                continue

        prof = profile_df(df)
        # simple rules
        max_null_pct = prof["null_pct"].max() if not prof.empty else 0.0
        rule_pass = max_null_pct <= 20.0  # contoh ambang
        status = "✅ OK" if rule_pass else "❌ Attention"
        status_ok = status_ok and rule_pass

        lines += [
            f"## {csv.name} — {status}",
            f"- **Rows x Cols**: `{df.shape[0]} x {df.shape[1]}`",
            "",
            "### Kolom",
            to_md_table(prof.round(3)),
            ""
        ]

    lines.append(f"\n**Overall status**: {'✅ PASS' if status_ok else '❌ NEEDS ATTENTION'}\n")
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] Wrote {REPORT}")

if __name__ == "__main__":
    main()
