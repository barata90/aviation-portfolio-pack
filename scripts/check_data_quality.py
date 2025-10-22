#!/usr/bin/env python3
"""
Quality report lanjutan:
- Muat kontrak dari governance/datasets.yml
- Cek: presence, schema drift/typing, null ratio, uniqueness, expression rules, range, freshness
- Severity: error/warn → aggregate status per dataset & keseluruhan
- Output: docs/quality_report.md (tabel ringkas + detail)
- Exit code: 0 (default). Gunakan --fail-on=error untuk blokir pipeline bila ada error.
"""
import os, sys, hashlib, io
from pathlib import Path
from datetime import datetime
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
GOV = ROOT / "governance" / "datasets.yml"
DOCS = ROOT / "docs"
DOCS.mkdir(parents=True, exist_ok=True)

def _md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def _coerce_dtype(series: pd.Series, logical: str) -> pd.Series:
    t = logical.lower()
    if t in ("int", "integer"):
        return pd.to_numeric(series, errors="coerce").astype("Int64")
    if t in ("float", "double", "number"):
        return pd.to_numeric(series, errors="coerce")
    if t in ("date", "datetime", "timestamp"):
        return pd.to_datetime(series, errors="coerce", utc=True).dt.tz_localize(None)
    return series.astype("string")

def _fmt_status(ok: bool, lvl: str) -> str:
    return "🟢 OK" if ok else ("🟠 WARN" if lvl=="warn" else "🔴 ERROR")

def load_governance():
    if not GOV.exists():
        print(f"[WARN] Governance file not found: {GOV}", file=sys.stderr)
        return {"datasets": {}}
    with open(GOV, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def check_dataset(did: str, cfg: dict) -> dict:
    path = ROOT / cfg["path"]
    res = {
        "dataset": did,
        "path": str(cfg["path"]),
        "exists": path.exists(),
        "owner": cfg.get("owner", ""),
        "pii": bool(cfg.get("pii", False)),
        "cadence": cfg.get("cadence", ""),
        "status": "OK",
        "errors": 0,
        "warnings": 0,
        "md5": None,
        "row_count": None,
        "columns": [],
        "checks": [],
    }
    if not path.exists():
        res["status"] = "ERROR"; res["errors"] += 1
        res["checks"].append(("presence", "🔴 file not found"))
        return res

    res["md5"] = _md5(path)
    df = pd.read_csv(path)
    res["row_count"] = len(df)
    schema = cfg.get("schema", {}) or {}

    # Coerce + schema drift
    cols = list(df.columns)
    res["columns"] = cols
    drift_missing = [c for c in schema.keys() if c not in df.columns]
    drift_new = [c for c in df.columns if c not in schema.keys()]
    if drift_missing:
        res["status"] = "ERROR"; res["errors"] += 1
        res["checks"].append(("schema", f"🔴 missing cols: {drift_missing}"))
    if drift_new:
        res["warnings"] += 1
        res["checks"].append(("schema", f"🟠 extra cols: {drift_new}"))

    # Typing + nulls
    type_issues = []
    null_issues = []
    for col, logical in schema.items():
        if col not in df.columns: 
            continue
        coerced = _coerce_dtype(df[col], logical)
        bad = coerced.isna() & df[col].notna()
        if bad.sum() > 0:
            type_issues.append((col, logical, int(bad.sum())))
        df[col] = coerced
        null_ratio = df[col].isna().mean()
        if null_ratio > 0:
            null_issues.append((col, null_ratio))

    if type_issues:
        res["warnings"] += 1
        res["checks"].append(("typing", f"🟠 coercion issues: {type_issues}"))
    if null_issues:
        key_cols = set(sum([cfg.get("primary_key", [])], []))
        critical = [c for (c, r) in null_issues if c in key_cols]
        if critical:
            res["status"] = "ERROR"; res["errors"] += 1
            res["checks"].append(("nulls", f"🔴 nulls in key columns: {critical}"))
        else:
            res["warnings"] += 1
            res["checks"].append(("nulls", f"🟠 null ratios: {[(c, round(r,3)) for (c,r) in null_issues]}"))

    # Uniqueness
    pk = cfg.get("primary_key")
    if pk:
        dup = df.duplicated(subset=pk).sum()
        if dup > 0:
            res["status"] = "ERROR"; res["errors"] += 1
            res["checks"].append(("unique", f"🔴 duplicates on {pk}: {dup}"))

    # Expression & range
    for rule in cfg.get("checks", []):
        if rule.get("type") == "expression":
            ok_mask = df.eval(rule["sql"])
            bad = (~ok_mask).sum()
            if bad > 0:
                if rule.get("severity","error")=="warn":
                    res["warnings"] += 1
                    res["checks"].append(("expr", f"🟠 {rule['sql']} failed rows: {bad}"))
                else:
                    res["errors"] += 1; res["status"] = "ERROR"
                    res["checks"].append(("expr", f"🔴 {rule['sql']} failed rows: {bad}"))
        if rule.get("type") == "range":
            col = rule["column"]
            if col in df.columns:
                ge = rule.get("ge"); le = rule.get("le")
                bad = pd.Series(False, index=df.index)
                if ge is not None: bad |= df[col] < ge
                if le is not None: bad |= df[col] > le
                nbad = bad.sum()
                if nbad > 0:
                    if rule.get("severity","warn")=="warn":
                        res["warnings"] += 1
                        res["checks"].append(("range", f"🟠 {col} out-of-range rows: {nbad}"))
                    else:
                        res["errors"] += 1; res["status"] = "ERROR"
                        res["checks"].append(("range", f"🔴 {col} out-of-range rows: {nbad}"))

    # Freshness
    date_col = cfg.get("date_column")
    if date_col and date_col in df.columns:
        try:
            dt = pd.to_datetime(df[date_col], errors="coerce", utc=True).dt.tz_localize(None)
            maxd = dt.max()
            lag = (datetime.utcnow() - maxd).days
            limit = int(cfg.get("freshness_max_lag_days", 90))
            if lag > limit:
                res["warnings"] += 1
                res["checks"].append(("freshness", f"🟠 stale: max({date_col})={maxd.date()} lag={lag}d > {limit}d"))
        except Exception as e:
            res["warnings"] += 1
            res["checks"].append(("freshness", f"🟠 cannot parse {date_col}: {e}"))

    return res

def badge(status: str) -> str:
    return {"OK":"🟢","ERROR":"🔴","WARN":"🟠"}.get(status, "🟢")

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--fail-on", choices=["none","warn","error"], default=os.getenv("DQ_FAIL_ON","none"))
    args = ap.parse_args()

    gov = load_governance()
    datasets = gov.get("datasets", {})
    rows, details = [], []
    global_errors = 0
    global_warns = 0

    for did, cfg in datasets.items():
        r = check_dataset(did, cfg)
        rows.append({
            "Dataset": did,
            "Owner": r["owner"],
            "Rows": r["row_count"],
            "Status": r["status"],
            "Errors": r["errors"],
            "Warnings": r["warnings"],
            "File": f"`{r['path']}`",
            "MD5": (r["md5"] or "")[:8] if r["md5"] else "",
        })
        global_errors += r["errors"]
        global_warns += r["warnings"]
        buf = io.StringIO()
        buf.write(f"### {did} {badge(r['status'])}\n\n")
        buf.write(f"- Path: `{r['path']}`  \n- Owner: {r['owner']}  \n- Rows: {r['row_count']}  \n- PII: {r['pii']}  \n- Cadence: {r['cadence']}\n\n")
        if r["checks"]:
            for _, msg in r["checks"]:
                buf.write(f"- {msg}\n")
        else:
            buf.write("- No issues detected.\n")
        details.append(buf.getvalue())

    overall = "OK"
    if global_errors > 0: overall = "ERROR"
    elif global_warns > 0: overall = "WARN"

    DOCS.mkdir(exist_ok=True, parents=True)
    out = DOCS / "quality_report.md"
    df = pd.DataFrame(rows)
    if not df.empty:
        df["Status"] = df["Status"].map(lambda s: f"{badge(s)} {s}")
        table = df.to_markdown(index=False)
    else:
        table = "_No datasets configured in governance/datasets.yml_"
    header = f"# Data Quality Report — overall: {badge(overall)} {overall}\n\nGenerated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n\n"
    doc = header + table + "\n\n" + "\n\n".join(details) + "\n"
    out.write_text(doc, encoding="utf-8")
    print(f"Wrote {out}")

    if args.fail_on == "error" and global_errors > 0:
        sys.exit(1)
    if args.fail_on == "warn" and (global_errors > 0 or global_warns > 0):
        sys.exit(2)
    sys.exit(0)

if __name__ == "__main__":
    main()
