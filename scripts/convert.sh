# convert geojson to pmtiles
input="results/far/buildings_split.geojson"
output="static/MASSING_FAR.pmtiles"

tippecanoe -zg -o "$output" --drop-densest-as-needed --extend-zooms-if-still-dropping "$input" --force