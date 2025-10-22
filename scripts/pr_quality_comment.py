
import os, sys, glob, hashlib, pandas as pd
from pathlib import Path

PUB = Path("publish")

def md5sum(p: Path):
    h = hashlib.md5()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1<<20), b""):
            h.update(chunk)
    return h.hexdigest()

def summarize_csv(p: Path):
    try:
        df = pd.read_csv(p, nrows=2000)  # sample for speed
    except Exception as e:
        return {"file": p.name, "error": str(e)}
    cols = list(df.columns)
    n = len(df)
    # simple stats for first few numeric cols
    num = df.select_dtypes(include=["number"]).iloc[:2000]
    stats = []
    for c in list(num.columns)[:5]:
        v = num[c].dropna()
        stats.append(f"{c}: mean={v.mean():.2f}, std={v.std():.2f}, min={v.min():.2f}, max={v.max():.2f}")
    nulls = []
    for c in cols[:8]:
        r = df[c].isna().mean()*100
        nulls.append(f"{c}: {r:.1f}% null")
    return {
        "file": p.name, "rows_sampled": len(df), "columns": len(cols),
        "nulls": nulls, "stats": stats, "md5": md5sum(p)[:8]
    }

def main():
    files = [Path(p) for p in glob.glob("publish/*.csv")]
    if not files:
        print("No CSVs under publish/.", flush=True); return 0
    lines = []
    lines.append("### Data Quality Snapshot (PR)\n")
    lines.append("| File | Columns | Rows (sampled) | MD5 |")
    lines.append("|---|---:|---:|---|")
    for p in files:
        s = summarize_csv(p)
        if "error" in s:
            lines.append(f"| `{s['file']}` | - | - | error: {s['error']} |")
        else:
            lines.append(f"| `{s['file']}` | {s['columns']} | {s['rows_sampled']:,} | `{s['md5']}` |")
    lines.append("\n<details><summary>Null ratios (top columns)</summary>\n\n")
    for p in files:
        s = summarize_csv(p)
        if "error" in s: continue
        lines.append(f"- **{s['file']}** → " + "; ".join(s["nulls"]))
    lines.append("\n</details>\n")
    lines.append("<details><summary>Numeric stats (sample)</summary>\n\n")
    for p in files:
        s = summarize_csv(p)
        if "error" in s: continue
        if s["stats"]:
            lines.append(f"- **{s['file']}** → " + "; ".join(s["stats"]))
    lines.append("\n</details>\n")
    print("\\n".join(lines), flush=True)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
