#!/usr/bin/env python3
import csv, os, sys, argparse, urllib.request, gzip, shutil

HIST_CSV = "data/noaa_isd/isd-history.csv"
BASE_URL = "https://www.ncei.noaa.gov/pub/data/noaa"

def download(url, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    print("Downloading:", url)
    with urllib.request.urlopen(url, timeout=60) as r, open(out_path, "wb") as f:
        f.write(r.read())
    print("Saved:", out_path)

def ensure_history():
    if not os.path.exists(HIST_CSV):
        download("https://www.ncei.noaa.gov/pub/data/noaa/isd-history.csv", HIST_CSV)

def find_usaf_wban(icaos):
    out = []
    with open(HIST_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # Columns typically include: USAF,WBAN,CTRY,ST,ICAO,LAT,LON,ELEV...,BEGIN,END
        for row in reader:
            icao = (row.get("ICAO") or "").strip()
            if icao in icaos:
                usaf = (row.get("USAF") or "").strip()
                wban = (row.get("WBAN") or "").strip()
                if usaf and wban:
                    out.append((icao, usaf, wban))
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--icaos", nargs="+", required=True, help="ICAO codes, e.g., OMDB EGLL")
    ap.add_argument("--year", type=int, required=True, help="Year, e.g., 2025")
    args = ap.parse_args()

    ensure_history()
    stations = find_usaf_wban(set([c.upper() for c in args.icaos]))
    if not stations:
        print("No stations found; check ICAO codes.")
        sys.exit(2)

    for icao, usaf, wban in stations:
        fname = f"{usaf}-{wban}-{args.year}.gz"
        url = f"{BASE_URL}/{args.year}/{fname}"
        out_path = os.path.join("data", "noaa_isd", fname)
        try:
            download(url, out_path)
        except Exception as e:
            print(f"Failed {icao} {url}: {e}")

if __name__ == "__main__":
    main()
