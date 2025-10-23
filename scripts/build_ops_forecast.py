#!/usr/bin/env python3
from __future__ import annotations
import os, json
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd
import numpy as np

PUBLISH_DIR = Path(os.environ.get("PUBLISH_DIR","publish"))
OUTPUT_JSON = Path(os.environ.get("OUTPUT_JSON","docs/assets/ops_forecast.json"))

def write_payload(payload):
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT_JSON} (status={payload.get('status')})")

def main():
    now = datetime.now(timezone.utc).isoformat()
    try:
        src = PUBLISH_DIR/"euro_atfm_timeseries.csv"
        if not src.exists():
            write_payload({"status":"no_input","generated_at":now,"series":[],"fitted":[],"forecast":[],"anomalies":[],"seasonality":[]})
            return 0
        df = pd.read_csv(src)
        date_col = next((c for c in df.columns if 'period' in c.lower() or 'date' in c.lower()), df.columns[0])
        num_col = next((c for c in df.columns if c != date_col and pd.api.types.is_numeric_dtype(df[c])), None)
        if num_col is None:
            write_payload({"status":"no_numeric","generated_at":now,"series":[],"fitted":[],"forecast":[],"anomalies":[],"seasonality":[]})
            return 0
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        s = pd.Series(df[num_col].values, index=pd.DatetimeIndex(df[date_col])).sort_index().dropna()
        if len(s) < 8:
            write_payload({"status":"too_short","generated_at":now,"series":[],"fitted":[],"forecast":[],"anomalies":[],"seasonality":[]})
            return 0
        by_m = s.groupby(s.index.month).mean()
        si = s.index.to_series().apply(lambda t: by_m.get(t.month, by_m.mean()))
        t = np.arange(len(s), dtype=float)
        y_ds = (s/si).replace([np.inf,-np.inf], np.nan).bfill().ffill()
        X = np.column_stack([np.ones_like(t), t])
        beta, *_ = np.linalg.lstsq(X, y_ds.to_numpy(), rcond=None)
        trend = pd.Series(beta[0]+beta[1]*t, index=s.index)
        fitted = trend*si
        h = 6
        fut_idx = pd.date_range(s.index[-1]+pd.offsets.MonthBegin(), periods=h, freq="MS")
        fut_trend = pd.Series(beta[0]+beta[1]*np.arange(len(s), len(s)+h, dtype=float), index=fut_idx)
        fut_si = fut_idx.to_series().apply(lambda x: by_m.get(x.month, by_m.mean()))
        forecast = (fut_trend*fut_si).clip(lower=0)
        def pairs(a): return [{"t": int(pd.Timestamp(i).timestamp()*1000), "y": float(v)} for i,v in a.dropna().items()]
        payload = {
            "status":"ok","generated_at":now,
            "series":pairs(s),"fitted":pairs(fitted),"forecast":pairs(forecast),
            "anomalies":[], "seasonality":[{"m":int(i),"si":float(v)} for i,v in by_m.items()]
        }
        write_payload(payload)
        return 0
    except Exception as e:
        write_payload({"status":"error","generated_at":now,"error":str(e),"series":[],"fitted":[],"forecast":[],"anomalies":[],"seasonality":[]})
        return 0

if __name__ == "__main__":
    raise SystemExit(main())
