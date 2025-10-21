import pandas as pd
from pathlib import Path
import plotly.express as px

DOCS = Path("docs")
PUBLISH = Path("publish")
DOCS.mkdir(parents=True, exist_ok=True)

def find_file(candidates):
    for c in candidates:
        p = PUBLISH / f"{c}.csv"
        if p.exists():
            return p
    return None

def top_bar(df, value_col, name_col, title, out_html):
    top = df.sort_values(value_col, ascending=False).head(20)
    fig = px.bar(top, x=value_col, y=name_col, orientation="h", title=title, height=600)
    fig.update_layout(yaxis=dict(autorange="reversed"))
    fig.write_html(DOCS / out_html, include_plotlyjs="cdn")
    print(f"[OK] {out_html}")

def route_counts():
    f = find_file(["route_counts"])
    if not f:
        print("[SKIP] publish/route_counts.csv tidak ditemukan")
        return
    df = pd.read_csv(f)
    # Heuristik kolom
    value_col = next((c for c in df.columns if c.lower() in ("count","counts","n")), None)
    if not value_col:
        # fallback: ambil kolom numerik terbesar
        nums = df.select_dtypes("number").columns
        value_col = nums[0] if len(nums) else None
    name_col = next((c for c in df.columns if "route" in c.lower() or "pair" in c.lower()), None)
    if not name_col:
        # fallback: kolom non-numerik pertama
        cats = df.select_dtypes(exclude="number").columns
        name_col = cats[0] if len(cats) else None

    if value_col and name_col:
        top_bar(df, value_col, name_col, "Top 20 Rute Terpadat", "route_counts_top20.html")
    else:
        print("[SKIP] route_counts: kolom tidak dikenali")

def airport_degree():
    f = find_file(["airport_degree"])
    if not f:
        print("[SKIP] publish/airport_degree.csv tidak ditemukan")
        return
    df = pd.read_csv(f)
    deg_col = next((c for c in df.columns if "degree" in c.lower() or "connections" in c.lower()), None)
    name_col = next((c for c in df.columns if "airport" in c.lower() or c.lower() in ("apt","icao","iata")), None)

    if not deg_col:
        nums = df.select_dtypes("number").columns
        deg_col = nums[0] if len(nums) else None
    if not name_col:
        cats = df.select_dtypes(exclude="number").columns
        name_col = cats[0] if len(cats) else None

    if deg_col and name_col:
        top_bar(df, deg_col, name_col, "Top 20 Airport by Degree", "airport_degree_top20.html")
    else:
        print("[SKIP] airport_degree: kolom tidak dikenali")

if __name__ == "__main__":
    route_counts()
    airport_degree()
