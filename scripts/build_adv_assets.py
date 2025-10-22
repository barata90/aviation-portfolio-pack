#!/usr/bin/env python3
import pandas as pd, numpy as np, json
from pathlib import Path

ROOT = Path('.'); DOCS = ROOT/'docs'; ASSETS = DOCS/'assets'; API = DOCS/'api'; PUB = ROOT/'publish'
ASSETS.mkdir(parents=True, exist_ok=True); API.mkdir(parents=True, exist_ok=True)

def build_scenario_assets():
    ts = pd.read_csv(PUB/'euro_atfm_timeseries.csv', parse_dates=['period_start']).sort_values('period_start')
    last24 = ts['period_start'].max() - pd.DateOffset(months=23)
    ts = ts[ts['period_start']>=last24].copy()
    ts['month'] = ts['period_start'].dt.strftime('%Y-%m')
    months = ts['month'].tolist()
    total = ts['delay_minutes'].astype(float).round(2).tolist()

    byloc = pd.read_csv(PUB/'euro_atfm_by_location.csv')
    byloc = byloc.rename(columns=str.lower)[['location','delay_minutes']].dropna()
    byloc['delay_minutes'] = byloc['delay_minutes'].astype(float).clip(lower=0)
    byloc = byloc.sort_values('delay_minutes', ascending=False)
    byloc['share'] = byloc['delay_minutes'] / byloc['delay_minutes'].sum()

    locs = byloc['location'].tolist()[:25]
    shares = dict(zip(byloc['location'], byloc['share']))
    locations = {}
    for mval in ts['delay_minutes'].tolist():
        for loc in locs:
            locations.setdefault(loc, []).append(round(float(mval)*float(shares[loc]), 2))

    out = {'months': months, 'total': total, 'locations': locations, 'top_locations': locs}
    (ASSETS/'scenario_timeseries.json').write_text(json.dumps(out), encoding='utf-8')
    print('[assets] scenario_timeseries.json')

def build_hub_rank():
    rc = pd.read_csv(PUB/'route_counts.csv').rename(columns=str.lower)[['src_iata','dst_iata','num_routes']].dropna()
    rc['num_routes'] = rc['num_routes'].astype(float).clip(lower=0)
    nodes = sorted(set(rc['src_iata'])|set(rc['dst_iata']))
    idx = {n:i for i,n in enumerate(nodes)}
    n = len(nodes)
    if n==0:
        return
    A = np.zeros((n,n), dtype=float)  # column-stochastic (source in columns)
    for s,d,w in rc.itertuples(index=False):
        A[idx[d], idx[s]] += float(w)
    colsum = A.sum(axis=0); colsum[colsum==0]=1.0
    P = A/colsum
    d=0.85; pr=np.ones(n)/n; v=np.ones(n)/n
    for _ in range(100):
        pr_new = d*(P@pr) + (1-d)*v
        if np.linalg.norm(pr_new-pr,1) < 1e-9:
            pr = pr_new; break
        pr = pr_new
    import pandas as pd
    df = pd.DataFrame({'iata':nodes,'pagerank':pr}).sort_values('pagerank', ascending=False)
    df.to_csv(ASSETS/'hub_rank.csv', index=False)
    top = df.head(30)
    fig = {'data':[{'type':'bar','orientation':'h','x':[round(float(x),6) for x in top['pagerank'].tolist()], 'y':top['iata'].tolist()}],
           'layout':{'margin':{'l':80,'r':10,'t':20,'b':40},'xaxis':{'title':'PageRank'},'yaxis':{'title':'Airport (IATA)'},'height':520}}
    (ASSETS/'hub_rank.json').write_text(json.dumps(fig), encoding='utf-8')
    print('[assets] hub_rank.csv, hub_rank.json')

def build_static_api():
    ts = pd.read_csv(PUB/'euro_atfm_timeseries.csv', parse_dates=['period_start']).sort_values('period_start')
    last24 = ts['period_start'].max() - pd.DateOffset(months=23)
    ts = ts[ts['period_start']>=last24].copy()
    ts['period_start'] = ts['period_start'].dt.strftime('%Y-%m-%d')
    (DOCS/'api').mkdir(parents=True, exist_ok=True)
    (DOCS/'api'/'euro_atfm_timeseries_last24.json').write_text(ts.to_json(orient='records'), encoding='utf-8')

    deg = pd.read_csv(PUB/'airport_degree.csv').sort_values('deg_total', ascending=False).head(100)
    (DOCS/'api'/'airport_degree_top100.json').write_text(deg.to_json(orient='records'), encoding='utf-8')

    idx = [{'path':'api/euro_atfm_timeseries_last24.json','rows':len(ts)},
           {'path':'api/airport_degree_top100.json','rows':len(deg)}]
    (DOCS/'api'/'index.json').write_text(json.dumps(idx), encoding='utf-8')
    print('[api] index.json + shards')

if __name__ == '__main__':
    build_scenario_assets(); build_hub_rank(); build_static_api()
