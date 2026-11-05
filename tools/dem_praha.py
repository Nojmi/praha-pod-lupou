#!/usr/bin/env python3
"""Stáhne výšky terénu Prahy (Copernicus DEM 90 m přes Open-Meteo, bez klíče) do elevation.json.
Spuštění: python3 dem_praha.py   (jen standardní knihovna, trvá cca 7 minut)"""
import json, math, time, urllib.request, urllib.error

LAT0, LAT1, LON0, LON1 = 49.93, 50.19, 14.20, 14.75
STEP_M = 600.0
dlat = STEP_M / 110574.0
dlon = STEP_M / (math.cos(math.radians(50.08)) * 111320.0)
lats = [round(LAT0 + i * dlat, 6) for i in range(int((LAT1 - LAT0) / dlat) + 1)]
lons = [round(LON0 + j * dlon, 6) for j in range(int((LON1 - LON0) / dlon) + 1)]
pts = [(la, lo) for la in lats for lo in lons]
print(f"mřížka {len(lons)} x {len(lats)} = {len(pts)} bodů")

def fetch(chunk):
    url = ("https://api.open-meteo.com/v1/elevation?latitude=" + ",".join(str(p[0]) for p in chunk)
           + "&longitude=" + ",".join(str(p[1]) for p in chunk))
    for attempt in range(40):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.load(r)["elevation"]
        except urllib.error.HTTPError as e:
            wait = 65 if e.code == 429 else 3
            print("HTTP", e.code, "čekám", wait, "s"); time.sleep(wait)
        except Exception as e:
            print("chyba", e); time.sleep(3)
    raise SystemExit("Nepodařilo se stáhnout data.")

elev = []
for i in range(0, len(pts), 100):
    elev += fetch(pts[i:i + 100])
    print(f"{len(elev)}/{len(pts)}", end="\r", flush=True)
    time.sleep(13)  # limit Open-Meteo: 600 bodů/min, 5000/hod
json.dump({"lat0": LAT0, "lon0": LON0, "dlat": dlat, "dlon": dlon, "nx": len(lons), "ny": len(lats),
           "z": [round(v, 1) for v in elev]}, open("elevation.json", "w"))
print("\nHotovo: elevation.json, min", min(elev), "max", max(elev))
