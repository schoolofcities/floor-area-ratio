# convert geojson to pmtiles
input="results/far/far.geojson"
output="static/FAR_PROPERTY.pmtiles"

# tippecanoe -zg -o "$output" --drop-densest-as-needed --extend-zooms-if-still-dropping "$input" --force

# drop less
tippecanoe -zg -o "$output" --no-feature-limit --extend-zooms-if-still-dropping "$input" --force