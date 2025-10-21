import pandas as pd
from pathlib import Path

DOCS = Path("docs")
PUBLISH = Path("publish")
DOCS.mkdir(parents=True, exist_ok=True)

TABLES = [
    "route_counts",
    "airport_degree",
    "euro_atfm_timeseries",
    "euro_atfm_by_location",
]

def summarize(path: Path):
    df = pd.read_csv(path)
    rows, cols = df.shape
    nulls = df.isna().sum().sum()
    sample = ", ".join(df.columns[:6]) + ("..." if df.shape[1] > 6 else "")
    return rows, cols, int(nulls), sample

lines = [
    "# Data Quality Report\n",
    "| Table | Rows | Cols | Null cells | Sample columns |",
    "|---|---:|---:|---:|---|",
]

for name in TABLES:
    p = PUBLISH / f"{name}.csv"
    if p.exists():
        try:
            r, c, n, s = summarize(p)
            lines.append(f"| `{name}` | {r} | {c} | {n} | {s} |")
        except Exception as e:
            lines.append(f"| `{name}` | ERR | ERR | ERR | read error: `{e}` |")
    else:
        lines.append(f"| `{name}` | - | - | - | *(missing)* |")

out = DOCS / "data_quality.md"
out.write_text("\n".join(lines), encoding="utf-8")
print(f"[OK] wrote {out}")
