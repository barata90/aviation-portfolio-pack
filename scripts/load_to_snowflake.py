#!/usr/bin/env python3
"""
Snowflake loader (pro):
- --mode pandas|copy
- --dry-run
- --table-prefix RAW.
- Idempotent: stage overwrite + MATCH_BY_COLUMN_NAME
"""
import os, sys, argparse, glob, hashlib
from pathlib import Path
import pandas as pd

ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT")
USER    = os.getenv("SNOWFLAKE_USER")
PWD     = os.getenv("SNOWFLAKE_PASSWORD")
ROLE    = os.getenv("SNOWFLAKE_ROLE", "")
WH      = os.getenv("SNOWFLAKE_WAREHOUSE", "")
DB      = os.getenv("SNOWFLAKE_DATABASE", "")
SCHEMA  = os.getenv("SNOWFLAKE_SCHEMA", "")

def md5sum(p: Path) -> str:
    h = hashlib.md5()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1<<20), b""): h.update(chunk)
    return h.hexdigest()

def connect():
    import snowflake.connector as sf
    ctx = sf.connect(
        account=ACCOUNT, user=USER, password=PWD,
        role=ROLE or None, warehouse=WH or None, database=DB or None, schema=SCHEMA or None
    )
    return ctx

def ensure_table_from_csv(cur, table: str, csv_path: Path):
    df = pd.read_csv(csv_path, nrows=1000)
    cols = [f'"{c.upper()}" TEXT' for c in df.columns]
    cur.execute(f'CREATE TABLE IF NOT EXISTS {table} ({", ".join(cols)})')

def put_and_copy(cur, table: str, csv_path: Path, stage: str):
    cur.execute(f"CREATE STAGE IF NOT EXISTS {stage}")
    cur.execute(f"CREATE FILE FORMAT IF NOT EXISTS CSV_FMT TYPE=CSV SKIP_HEADER=1 FIELD_OPTIONALLY_ENCLOSED_BY='\"'")
    cur.execute(f"REMOVE @{stage}/{csv_path.name}")
    cur.execute(f"PUT file://{csv_path} @{stage} AUTO_COMPRESS=TRUE OVERWRITE=TRUE")
    cur.execute(f"""
        COPY INTO {table}
        FROM @{stage}/{csv_path.name}
        FILE_FORMAT=CSV_FMT
        MATCH_BY_COLUMN_NAME=CASE_INSENSITIVE
        ON_ERROR=ABORT_STATEMENT
    """)

def write_pandas(cur, table: str, csv_path: Path):
    from snowflake.connector.pandas_tools import write_pandas
    df = pd.read_csv(csv_path)
    ensure_table_from_csv(cur, table, csv_path)
    write_pandas(cur.connection, df, table_name=table.split(".")[-1], quote_identifiers=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["pandas","copy"], default=os.getenv("SF_MODE","copy"))
    ap.add_argument("--table-prefix", default=os.getenv("SF_TABLE_PREFIX","RAW."))
    ap.add_argument("--glob", default="publish/*.csv")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    files = [Path(p) for p in glob.glob(args.glob)]
    if not files:
        print("No CSV files found in publish/. Nothing to load.")
        return 0

    plan = []
    for p in files:
        tname = p.stem.upper()
        table = f"{args.table_prefix}{tname}"
        plan.append((p, table, md5sum(p)))
    print("Load plan:")
    for p, t, m in plan:
        print(f"- {p.name} → {t}  (md5={m[:8]})")

    if args.dry_run:
        print("Dry-run mode. Exiting without loading.")
        return 0

    ctx = connect()
    try:
        cur = ctx.cursor()
        if ROLE: cur.execute(f"USE ROLE {ROLE}")
        if WH:   cur.execute(f"USE WAREHOUSE {WH}")
        if DB:   cur.execute(f"USE DATABASE {DB}")
        if SCHEMA: cur.execute(f"USE SCHEMA {SCHEMA}")

        for p, table, _ in plan:
            if args.mode == "pandas":
                write_pandas(cur, table, p)
            else:
                stage = f"{SCHEMA}.CSV_STAGE" if SCHEMA else "CSV_STAGE"
                ensure_table_from_csv(cur, table, p)
                put_and_copy(cur, table, p, stage)
        print("Load completed.")
        return 0
    finally:
        try: ctx.close()
        except: pass

if __name__ == "__main__":
    sys.exit(main())
