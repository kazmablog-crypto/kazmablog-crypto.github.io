#!/usr/bin/env bash
# Rebuilds data/out/ from data/raw/ and writes the results into ../index.html.
set -euo pipefail
cd "$(dirname "$0")"
WORK="${WORK:-$(mktemp -d)}"
echo "work dir: $WORK"
cp data/raw/pop2026.json data/raw/am_stats.json "$WORK/"
for f in data/raw/ruian/*.json.gz; do gunzip -c "$f" > "$WORK/$(basename "${f%.gz}")"; done
mkdir -p "$WORK/out"

python3 -I scripts/place_area.py data/raw/cz_border_naturalearth.json > data/out/places_area.json   # ~1 min
python3 -I scripts/build_grid.py "$WORK" "$WORK/out"                                          # ~3 min
python3 -I scripts/place_pop.py "$WORK/out" data/out/places_area.json                        # ~10 min
python3 -I scripts/labor.py "$WORK/out/C1200.npy" "$WORK/out/labor.json"
cp "$WORK/out/"{place.json,labor.json,border.json,towns.json} data/out/
python3 -I scripts/embed.py "$WORK/out" data/out ../index.html
echo "done: data/out and ../index.html updated"
