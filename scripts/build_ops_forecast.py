
#!/usr/bin/env python3
import pandas as pd, numpy as np, json
from pathlib import Path

ROOT = Path('.'); DOCS = ROOT/'docs'; ASSETS = DOCS/'assets'; PUB = ROOT/'publish'
ASSETS.mkdir(parents=True, exist_ok=True)

def seasonality_index(y, months):
    # index musiman 12 bulan, berbasis rasio ke tren (MA12)
    ma = y.rolling(12, min_periods=6, center=True).mean()
    ratio = y / ma.replace(0, np.nan)
    si = ratio.groupby(months).mean().fillna(1.0)
    # normalisasi agar rata-rata 1
    si = si * (12.0 / si.sum())
    return si

def forecast_linear_seasonal(y, months, horizon=6):
    # trend linear (polyfit orde 1) + indeks musiman 12
    t = np.arange(len(y))
    coeff = np.polyfit(t[~y.isna()], y.dropna(), 1) if (~y.isna()).sum()>=3 else [0.0, float(np.nanmean(y))]
    slope, intercept = coeff[0], coeff[1]
    si = seasonality_index(y, months)
    # nilai deseasonal
    ds = y / si.reindex(months).values
    ds = ds.replace([np.inf, -np.inf], np.nan).fillna(method='bfill').fillna(method='ffill')
    # residual untuk anomaly
    trend = slope*t + intercept
    fitted = si.reindex(months).values * trend
    resid = y - fitted
    # robust z
    med = np.nanmedian(resid)
    mad = np.nanmedian(np.abs(resid - med))
    z = (resid - med) / (1.4826*(mad if mad>0 else (np.nanstd(resid)+1e-9)))
    anomalies = []
    for i,(val,zi) in enumerate(zip(y, z)):
        if np.isfinite(zi) and abs(zi) >= 2.5:
            anomalies.append({"idx": i, "z": round(float(zi),2), "value": float(val)})
    # forecast
    last_t = len(y)-1
    fh_months = []
    fh_values = []
    for h in range(1, horizon+1):
        tt = last_t + h
        mo = int(months.iloc[-1-h+1]) if len(months)>0 else ((tt)%12)+1
        # ambil bulan-ke (1..12) dari urutan kalender
        mo = ((int(months.iloc[-1]) + h -1) % 12) + 1 if len(months)>0 else mo
        trend_h = slope*tt + intercept
        fh = float(trend_h) * float(si.loc.get(mo, 1.0))
        fh_months.append(mo); fh_values.append(fh)
    return fitted, anomalies, si, fh_values

def main():
    p = PUB/'euro_atfm_timeseries.csv'
    if not p.exists():
        print('[skip] timeseries not found'); return 0
    df = pd.read_csv(p, parse_dates=['period_start'])
    if df.empty or 'delay_minutes' not in df.columns:
        print('[skip] no data'); return 0
    df = df.sort_values('period_start')
    # asumsi monthly; kalau tidak, resample monthly
    m = df.set_index('period_start')['delay_minutes']
    if m.index.inferred_freq is None:
        m = m.resample('MS').sum()
    months_num = m.index.month
    fitted, anomalies, si, fh_vals = forecast_linear_seasonal(m, months_num, horizon=6)
    out = {
      "months": [d.strftime('%Y-%m') for d in m.index],
      "actual": [float(x) if pd.notna(x) else None for x in m.values],
      "fitted": [float(x) if pd.notna(x) else None for x in fitted],
      "anomalies": [{"month": out_idx, "label": m.index[z['idx']].strftime('%Y-%m'), "z": z["z"], "value": z["value"]} for out_idx, z in enumerate(anomalies)],
      "seasonal_index": {str(k): float(v) for k,v in si.to_dict().items()},  # 1..12
      "forecast": {
        "months_ahead": 6,
        "values": [float(v) for v in fh_vals]
      }
    }
    (ASSETS/'ops_forecast.json').write_text(json.dumps(out), encoding='utf-8')
    print('[ok] assets/ops_forecast.json written')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
