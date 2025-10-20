#!/usr/bin/env python3
import json, time, os, urllib.request, datetime

# Rough bbox around UAE
params = {
    "lamin": 20.0,   # south lat
    "lamax": 30.0,   # north lat
    "lomin": 45.0,   # west lon
    "lomax": 60.0,   # east lon
}
url = ("https://opensky-network.org/api/states/all"
       f"?lamin={params['lamin']}&lamax={params['lamax']}"
       f"&lomin={params['lomin']}&lomax={params['lomax']}")

print("Fetching:", url)
with urllib.request.urlopen(url, timeout=30) as resp:
    data = json.loads(resp.read().decode("utf-8"))

ts = datetime.datetime.utcfromtimestamp(data.get("time", int(time.time())))
outdir = "data/opensky"
os.makedirs(outdir, exist_ok=True)
outpath = os.path.join(outdir, f"states_uae_{ts:%Y%m%dT%H%M}Z.json")
with open(outpath, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print("Saved:", outpath)
