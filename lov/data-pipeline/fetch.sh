#!/usr/bin/env bash
# Downloads the raw inputs into data/raw/. Needs network access to
# data.csu.gov.cz, ags.cuzk.gov.cz and registry.npmjs.org.
set -euo pipefail
cd "$(dirname "$0")/data/raw"
SVC="https://ags.cuzk.gov.cz/arcgis/rest/services/RUIAN/Prohlizeci_sluzba_nad_daty_RUIAN/MapServer"
mkdir -p ruian

# 1) ČSÚ, dataset OBY02A: population on 1 January, total of both sexes, 6-digit municipality codes
YEAR="${YEAR:-2026}"
curl -sS --max-time 900 "https://data.csu.gov.cz/opendata/sady/OBY02A/distribuce/csv" \
  | grep -E '^"Počet obyvatel k 1\. 1\. \(počáteční stav\)","2406P","Celkem"' > pop_jan1.csv
python3 - "$YEAR" <<'PY'
import csv, json, sys
y = sys.argv[1]
pop = {r[7]: int(r[8]) for r in csv.reader(open('pop_jan1.csv', encoding='utf-8'))
       if r[4] == y and r[7].isdigit() and len(r[7]) == 6}
json.dump(pop, open('pop2026.json', 'w'))
print('municipalities', len(pop), 'people', sum(pop.values()))
PY
rm pop_jan1.csv

# 2) RÚIAN: municipality boundaries (layer 12), generalised to ~150 m
for off in 0 1000 2000 3000 4000 5000 6000; do
  curl -sS --max-time 180 "$SVC/12/query?where=1%3D1&outFields=kod,nazev,okres&returnGeometry=true&outSR=4326&maxAllowableOffset=0.0015&geometryPrecision=5&resultOffset=$off&resultRecordCount=1000&orderByFields=kod&f=geojson" \
    | gzip -9 > "ruian/obce_$off.json.gz"
done

# 3) RÚIAN: voting district boundaries (layer 20), generalised to ~80 m
for off in 0 2000 4000 6000 8000 10000 12000 14000; do
  curl -sS --max-time 180 "$SVC/20/query?where=1%3D1&outFields=kod,obec&returnGeometry=true&outSR=4326&maxAllowableOffset=0.0008&geometryPrecision=5&resultOffset=$off&resultRecordCount=2000&orderByFields=kod&f=geojson" \
    | gzip -9 > "ruian/vo_$off.json.gz"
done

# 4) RÚIAN: number of address points per voting district (layer 1), counted on the server
curl -sS --max-time 300 -G "$SVC/1/query" --data-urlencode "where=1=1" \
  --data-urlencode 'outStatistics=[{"statisticType":"count","onStatisticField":"objectid","outStatisticFieldName":"n"}]' \
  --data-urlencode "groupByFieldsForStatistics=vo_kod" --data-urlencode "f=json" -o am_stats.json

# 5) Natural Earth country outline (used only by the "by area" placement)
tmp=$(mktemp -d); (cd "$tmp" && npm pack world-atlas@2.0.2 --silent >/dev/null && tar xzf world-atlas-2.0.2.tgz)
python3 - "$tmp/package/countries-10m.json" <<'PY'
import json, sys
t = json.load(open(sys.argv[1])); (sx, sy), (tx, ty) = t['transform']['scale'], t['transform']['translate']
arcs = []
for a in t['arcs']:
    x = y = 0; pts = []
    for dx, dy in a: x += dx; y += dy; pts.append((x*sx+tx, y*sy+ty))
    arcs.append(pts)
g = next(g for g in t['objects']['countries']['geometries'] if g.get('properties', {}).get('name') == 'Czechia')
ring = []
for i in g['arcs'][0]:
    a = arcs[i] if i >= 0 else arcs[~i][::-1]
    ring.extend(a if not ring else a[1:])
json.dump([[round(x, 4), round(y, 4)] for x, y in ring], open('cz_border_naturalearth.json', 'w'))
PY
rm -rf "$tmp"
echo "raw data ready in data/raw"
