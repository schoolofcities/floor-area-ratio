import geopandas as gpd
from tqdm import tqdm
import pandas as pd
import time

# Enable tqdm for pandas
tqdm.pandas()

# Input shapefiles
massing_file = "results/massing/massing-cleaned.shp"
boundary_file = "data/property/PROPERTY_BOUNDARIES_WGS84.shp"
boundaryid = "OBJECTID"
floor_height = 3

# Output files
output_csv = "static/toronto_far.csv"
output_shp = "results/far/far.shp"
output_geojson = "results/far/far.geojson"
output_geopackage = "results/far/far.gpkg"

# Load shapefiles
print("📂 Loading shapefiles...")
buildings = gpd.read_file(massing_file)
boundary = gpd.read_file(boundary_file)

# Use existing parcel ID
print("🔢 Using existing parcel ID...")
boundary = boundary.reset_index(drop=True)
boundary["boundary_id"] = boundary[boundaryid]

# Reproject to projected CRS (meters)
print("🗺️ Reprojecting to EPSG:4326...")
buildings = buildings.to_crs(epsg=4326)
boundary = boundary.to_crs(epsg=4326)

# Fix invalid geometries
print("🧹 Fixing invalid geometries (buildings)...")
buildings['geometry'] = buildings['geometry'].progress_apply(lambda g: g.buffer(0))

print("🧹 Fixing invalid geometries (boundary)...")
boundary['geometry'] = boundary['geometry'].progress_apply(lambda g: g.buffer(0))

# Spatial join
print("🔍 Performing spatial join (building ↔ boundary)...")
joined = gpd.sjoin(buildings, boundary[['boundary_id', 'geometry']], predicate="intersects", how="inner")

print(joined.head())

# Filter matched geometries
print("📌 Filtering matched boundary and buildings...")
buildings_filtered = buildings.loc[joined.index].copy()
boundary_filtered = boundary[boundary["boundary_id"].isin(joined["boundary_id"].unique())].copy()

# Overlay to split buildings by parcel boundaries
print("✂️ Splitting buildings by parcel boundaries...")
start_time = time.time()
buildings_split = gpd.overlay(buildings_filtered, boundary_filtered, how='intersection')
print(f"⏱️ Split complete in {round(time.time() - start_time, 2)} seconds")

# 🗑️ Remove duplicate geometries
print("🗑️ Removing duplicate split geometries...")
before = len(buildings_split)
buildings_split = buildings_split[~buildings_split.geometry.duplicated(keep='first')]
after = len(buildings_split)
print(f"✅ Removed {before - after} duplicates.")

# 🔍 Keep only valid area geometries
print("🔍 Filtering only Polygon and MultiPolygon geometries...")
buildings_split = buildings_split[
    buildings_split.geometry.type.isin(["Polygon", "MultiPolygon"])
].copy()

# Compute floor areas
print("📐 Computing floor areas...")
buildings_split['area'] = tqdm(buildings_split.geometry.area, desc="→ Calculating area")
buildings_split['floors'] = buildings_split['AVG_HEIGHT'] / floor_height
buildings_split['floor_area'] = buildings_split['area'] * buildings_split['floors']

# Aggregate by parcel
print("📊 Aggregating floor area by parcel...")
floor_area_by_parcel = buildings_split.groupby("boundary_id")["floor_area"].sum().reset_index()

floor_area_by_parcel.columns = ["boundary_id", "total_floor_area"]

print(floor_area_by_parcel.columns)
print(floor_area_by_parcel.head())

# Merge with original boundary
print("🔗 Merging results with original boundary...")
boundary = boundary.merge(floor_area_by_parcel, on="boundary_id", how="left")

# Calculate FAR
print("📏 Calculating FAR...")
boundary['parcel_area'] = tqdm(boundary.geometry.area, desc="→ Calculating parcel area")
boundary['far'] = boundary['total_floor_area'] / boundary['parcel_area']
boundary['far'] = boundary['far'].fillna(0).round(2)

# Categorize FAR values into buckets
print("📊 Categorizing FAR values into buckets...")
def categorize_far(far):
    if far <= 0.5:
        return "0-0.5"
    elif far <= 1:
        return "0.5-1"
    elif far <= 2:
        return "1-2"
    elif far <= 5:
        return "2-5"
    else:
        return "5+"

boundary['far_bucket'] = boundary['far'].apply(categorize_far)

# Dissolve features by FAR buckets
# print("🧩 Dissolving features by FAR buckets...")
# boundary_dissolved = boundary.dissolve(by='far_bucket', as_index=False)

# Join FAR and FAR bucket values to split buildings
print("🔗 Joining FAR and FAR bucket values to split buildings...")
buildings_split = buildings_split.merge(boundary[['boundary_id', 'far', 'far_bucket']], on='boundary_id', how='left')

# Keep only the desired fields in buildings_split
print("🧹 Keeping only selected fields: boundary_id, AVG_HEIGHT, far, far_bucket...")
buildings_split = buildings_split[['boundary_id', 'AVG_HEIGHT', 'far', 'far_bucket', 'geometry']]

# print(buildings_split.head())

# Save buildings_split as GeoJSON
output_buildings_geojson = "results/far/buildings_split.geojson"
print(f"💾 Saving split buildings to: {output_buildings_geojson}")
buildings_split.to_file(output_buildings_geojson, driver="GeoJSON")

# # Save output as Shapefile
# print("💾 Saving to: {output_shp}")
# boundary.to_file(output_shp, driver="ESRI Shapefile")

# # Drop all columns except for "OBJECTID", "far", and "far_bucket"
# print("🧹 Dropping unnecessary columns...")
# boundary = boundary[["OBJECTID", "far", "geometry"]]

# # # Save output as GeoJSON
# print("💾 Saving to: {output_geojson}")
# boundary.to_file(output_geojson, driver="GeoJSON")

# # Save output as GeoPackage
# print(f"💾 Saving to: {output_geopackage}")
# boundary.to_file(output_geopackage, driver="GPKG", layer="boundary")

# Convert OBJECTID to integer
boundary["OBJECTID"] = pd.to_numeric(boundary["OBJECTID"], errors="coerce").fillna(0).astype(int)

# Save OBJECTID and FAR to a CSV file
print(f"💾 Saving OBJECTID and FAR to: {output_csv}")
boundary[["OBJECTID", "far"]].to_csv(output_csv, index=False)

# Save output as geopackage

# Done
print("✅ Done! Sample output:")