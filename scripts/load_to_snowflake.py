#!/usr/bin/env python3
import os
from pathlib import Path
import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas

CSV_DIR = Path("publish")

CFG = dict(
    account=os.getenv("SNOWFLAKE_ACCOUNT"),
    user=os.getenv("SNOWFLAKE_USER"),
    password=os.getenv("SNOWFLAKE_PASSWORD"),
    warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
    database=os.getenv("SNOWFLAKE_DATABASE", "AVIATION"),
    schema=os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC"),
    role=os.getenv("SNOWFLAKE_ROLE"),
)

def ensure_db_objects(cur, db, schema):
    cur.execute(f"CREATE DATABASE IF NOT EXISTS {db}")
    cur.execute(f"CREATE SCHEMA IF NOT EXISTS {db}.{schema}")

def load_csv(cur, conn, db, schema, path: Path):
    df = pd.read_csv(path)
    table = path.stem.upper()
    cur.execute(f"USE DATABASE {db}")
    cur.execute(f"USE SCHEMA {schema}")
    # buat table jika belum ada — semua kolom default TEXT, lalu Snowflake auto-cast saat query
    cols = ", ".join([f'"{c.upper()}" TEXT' for c in df.columns])
    cur.execute(f'CREATE TABLE IF NOT EXISTS "{table}" ({cols})')
    success, nchunks, nrows, _ = write_pandas(conn, df, table_name=table, database=db, schema=schema, quote_identifiers=True)
    print(f"[{table}] loaded rows={nrows} chunks={nchunks} success={success}")

def main():
    conn = snowflake.connector.connect(
        account=CFG["account"],
        user=CFG["user"],
        password=CFG["password"],
        warehouse=CFG["warehouse"],
        role=CFG["role"]
    )
    try:
        cur = conn.cursor()
        ensure_db_objects(cur, CFG["database"], CFG["schema"])
        for csv in sorted(CSV_DIR.glob("*.csv")):
            load_csv(cur, conn, CFG["database"], CFG["schema"], csv)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
