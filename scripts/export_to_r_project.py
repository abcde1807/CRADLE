"""
CRADLE R Project Data Exporter
Copies multi-city and per-city GeoJSON/CSV datasets into r_project/data/
for independent execution and replication in RStudio.
"""

import sys
import shutil
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config

def export_r_data():
    r_data_dir = config.R_PROJECT_DIR / "data"
    r_scripts_dir = config.R_PROJECT_DIR / "scripts"
    r_outputs_dir = config.R_PROJECT_DIR / "outputs"

    for d in [r_data_dir, r_scripts_dir, r_outputs_dir]:
        d.mkdir(parents=True, exist_ok=True)

    print(f"Exporting datasets to RStudio project: {r_data_dir}")

    # Copy raw/sample data for all cities
    for city_key in config.SUPPORTED_CITIES.keys():
        if not config.SUPPORTED_CITIES[city_key].get("is_active"):
            continue
        paths = config.get_city_data_paths(city_key)

        for key in ["sample_wards_geojson", "sample_pop_csv", "sample_fac_csv", "processed_wards_geojson", "processed_fac_geojson"]:
            src = paths.get(key)
            if src and src.exists():
                dst = r_data_dir / src.name
                shutil.copy2(src, dst)
                print(f"  -> Copied {src.name}")

    # Copy combined datasets
    for fn in ["all_cities_wards.geojson", "all_cities_facilities.geojson", "processed_wards.geojson", "processed_facilities.geojson"]:
        src = config.PROCESSED_DATA_DIR / fn
        if src.exists():
            dst = r_data_dir / fn
            shutil.copy2(src, dst)
            print(f"  -> Copied {fn}")

    print("[OK] All data files exported to r_project/data/")

if __name__ == "__main__":
    export_r_data()
