#!/usr/bin/env python3
"""
Build Ops Forecast JSON for the site.

Behavior:
- Scan PUBLISH_DIR for a CSV with a date-like column and a numeric metric.
- Aggregate monthly, estimate simple linear+seasonal model, detect anomalies
  via robust Z (MAD), and forecast next 6 months.
- If no suitable data is found, write a minimal, valid JSON placeholder.
- Never fail the CI; always write OUTPUT_JSON.

Allowed libs: pandas, numpy
"""
from __future__ import annotations
import os, json
from pathlib import Path
from dataclasses import dataclass
import numpy as np
import pandas as pd
from datetime import datetime, timezone

PUBLISH_DIR = Path(os.environ.get("PUBLISH_DIR", "publish"))
OUTPUT_JSON = Path(os.environ.get("OUTPUT_JSON", "docs/assets/ops_forecast.json"))

DATE_HINTS = {"date","dt","day","flight_date","operating_date","op_date","timestamp","ts","period","month","year_month"}

@dataclass
class SeriesPack:
    ts: pd.DatetimeIndex
    y: pd.Series  # monthly total
    name: str

def _coerce_dates(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        low = str(col).lower()
        if ("date" in low) or (low in DATE_HINTS):
            df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)
    return df

def _pick_series() -> SeriesPack | None:
    if not PUBLISH_DIR.exists():
        return None
    for csv_path in sorted(PUBLISH_DIR.glob("*.csv")):
        try:
            df = pd.read_csv(csv_path, encoding="utf-8-sig", low_memory=False)
            df = _coerce_dates(df)
            # choose date col
            date_col = None
            for c in df.columns:
                if pd.api.types.is_datetime64_any_dtype(df[c]):
                    date_col = c
                    break
            if not date_col:
                continue
            # choose numeric col (if any), else count rows
            value_col = None
            for c in df.columns:
                if c == date_col: 
                    continue
                if pd.api.types.is_numeric_dtype(df[c]):
                    value_col = c
                    break
            d = df[[date_col] + ([value_col] if value_col else [])].dropna(subset=[date_col]).copy()
            if d.empty:
                continue
            d["_m"] = d[date_col].dt.to_period("M").dt.to_timestamp()
            if value_col:
                y = d.groupby("_m")[value_col].sum(min_count=1)
            else:
                y = d.groupby("_m").size()
                y = pd.Series(y, index=y.index)
            y = y.sort_index()
            if len(y) < 6:
                continue
            return SeriesPack(ts=y.index, y=y, name=csv_path.name)
        except Exception:
            # Skip problematic CSVs
            continue
    return None

def _robust_z(x: pd.Series) -> pd.Series:
    med = x.median()
    mad = (x - med).abs().median()
    if mad == 0 or np.isnan(mad):
        return pd.Series(np.zeros(len(x)), index=x.index)
    return 0.6745 * (x - med) / mad

def _seasonal_index(y: pd.Series) -> pd.Series:
    # monthly seasonality (12)
    if len(y) < 12:
        return pd.Series(np.ones_like(y, dtype=float), index=y.index)
    df = y.to_frame("y")
    df["m"] = df.index.month
    # multiplicative SI
    monthly_avg = df.groupby("m")["y"].mean()
    si = df["m"].map(monthly_avg) / df["y"].mean()
    si.index = y.index
    return si

def _fit_forecast(y: pd.Series, horizon: int = 6):
    # Prepare time index as 0..n-1
    t = np.arange(len(y), dtype=float)
    # De-seasonalize (multiplicative)
    si = _seasonal_index(y).replace([np.inf, -np.inf], np.nan).bfill().ffill()
    y_ds = (y / si).replace([np.inf, -np.inf], np.nan).bfill().ffill()
    # Linear trend via OLS on y_ds ~ [1, t]
    X = np.column_stack([np.ones_like(t), t])
    beta, *_ = np.linalg.lstsq(X, y_ds.to_numpy(), rcond=None)
    trend = pd.Series(beta[0] + beta[1] * t, index=y.index)
    fitted = trend * si
    # Forecast indices
    h_t = np.arange(len(y), len(y) + horizon, dtype=float)
    # seasonal for future months
    last = y.index[-1]
    fut_months = [((last.to_period("M") + i).to_timestamp()) for i in range(1, horizon + 1)]
    fut_m = pd.Index(fut_months)
    # Build seasonal index for future by re-using monthly means
    base = y.to_frame("y")
    base["m"] = base.index.month
    monthly_avg = base.groupby("m")["y"].mean()
    fut_si = pd.Series([monthly_avg.get(dt.month, monthly_avg.mean()) for dt in fut_m], index=fut_m)
    fut_trend = pd.Series(beta[0] + beta[1] * h_t, index=fut_m)
    forecast = (fut_trend * fut_si).clip(lower=0)
    # anomalies on residuals
    resid = (y - fitted)
    rz = _robust_z(resid.fillna(0))
    anomalies = y[rz.abs() >= 3.5]  # threshold
    return fitted, forecast, si, anomalies

def _serialize(pack: SeriesPack | None):
    now = datetime.now(timezone.utc).isoformat()
    if pack is None:
        return {
            "status": "no_input",
            "generated_at": now,
            "series": [],
            "fitted": [],
            "forecast": [],
            "anomalies": [],
            "seasonality": [],
            "meta": {"note": "No suitable dataset found in publish/; placeholder written."}
        }
    y = pack.y
    fitted, forecast, si, anomalies = _fit_forecast(y, horizon=6)
    def to_pairs(s: pd.Series):
        return [{"t": int(pd.Timestamp(i).timestamp()*1000), "y": float(v)} for i, v in s.dropna().items()]
    return {
        "status": "ok",
        "generated_at": now,
        "source": pack.name,
        "series": to_pairs(y),
        "fitted": to_pairs(fitted),
        "forecast": to_pairs(forecast),
        "anomalies": to_pairs(anomalies),
        "seasonality": [{"m": int(i.month), "si": float(v)} for i, v in si.dropna().items()]
    }

def main():
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    pack = _pick_series()
    payload = _serialize(pack)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as w:
        json.dump(payload, w, indent=2)
    print(f"Wrote {OUTPUT_JSON} (status={payload['status']})")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
