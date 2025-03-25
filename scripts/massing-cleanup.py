import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon
from shapely.errors import TopologicalError
from tqdm import tqdm
import warnings

# Ignore specific warning
warnings.filterwarnings('ignore', 'GeoSeries.notna', UserWarning)

# Input shapefile
input_file = "data/massing/3DMassingShapefile_2023_WGS84.shp"

# Load shapefile
print("📦 Loading data...")
gdf = gpd.read_file(input_file)

# Fix invalid and null geometries
gdf["geometry"] = gdf["geometry"].apply(lambda geom: geom.buffer(0) if not geom.is_valid else geom)
gdf = gdf[gdf.geometry.notnull()].copy()

# Explode MultiPolygons to individual polygons
gdf = gdf.explode(index_parts=False).reset_index(drop=True)

# Sort by value descending so higher-value features are processed first
gdf_sorted = gdf.sort_values(by="AVG_HEIGHT", ascending=False).reset_index(drop=True)

print(gdf_sorted)

# Spatial index for faster lookups
spatial_index = gdf_sorted.sindex

# Copy geometries for updating
updated_geoms = gdf_sorted.geometry.copy()

# Track number of features skipped or fixed
skipped = 0
fixed = 0

# Loop through features
print("✂️ Cutting overlaps...")
for i, row in tqdm(gdf_sorted.iterrows(), total=len(gdf_sorted), desc="Processing features"):
    geom_i = row.geometry

    if geom_i.is_empty or not geom_i.is_valid:
        continue

    # Find features that might intersect (bounding box check)
    possible_matches_index = list(spatial_index.intersection(geom_i.bounds))

    for j in possible_matches_index:
        if j <= i:
            continue

        try:
            # Skip already empty or invalid geometries
            if updated_geoms[j].is_empty or not updated_geoms[j].is_valid:
                continue

            if updated_geoms[j].intersects(geom_i):
                diff_geom = updated_geoms[j].difference(geom_i)

                # Clean up diff geometry if needed
                if not diff_geom.is_valid:
                    diff_geom = diff_geom.buffer(0)
                    fixed += 1

                updated_geoms[j] = diff_geom

        except TopologicalError:
            skipped += 1
            continue

# Update gdf_sorted with modified geometries
gdf_sorted.geometry = updated_geoms

# Remove empty, null, and non-polygonal geometries
gdf_sorted = gdf_sorted[~gdf_sorted.geometry.is_empty & gdf_sorted.geometry.notnull()]
gdf_sorted = gdf_sorted[gdf_sorted.geometry.apply(lambda geom: isinstance(geom, (Polygon, MultiPolygon)))]

# Save as shapefile
output_path = "results/massing/massing-cleaned.shp"
gdf_sorted.to_file(output_path, driver="ESRI Shapefile")

print(f"✅ Done! Saved to: {output_path}")
print(f"🧹 Skipped due to TopologicalError: {skipped}")
print(f"🛠️ Fixed invalid geometries during processing: {fixed}")
