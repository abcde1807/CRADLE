"""
CRADLE Preprocessing Execution Script
Runs the data loading, spatial integration, gap scoring, desert detection,
and facility pressure analysis pipeline for all supported cities,
producing analysis-ready datasets and backward-compatible default files.
"""

import sys
import argparse
from pathlib import Path
import geopandas as gpd
import pandas as pd

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from src.preprocessing import PreprocessingPipeline
from src.gap_analyzer import HealthcareGapAnalyzer
from src.healthcare_desert import HealthcareDesertDetector
from src.facility_pressure import FacilityPressureAnalyzer


def preprocess_single_city(city_key: str):
    """Executes the full preprocessing pipeline for a single city."""
    city_cfg = config.get_city_config(city_key)
    city_name = city_cfg["city_name"]
    crs_proj = config.get_city_crs(city_key)
    paths = config.get_city_data_paths(city_key)

    print(f"\n--- Processing City: {city_name} ({city_key.upper()}) [CRS: {crs_proj}] ---")

    # 1. Preprocessing and spatial joins
    pipeline = PreprocessingPipeline()
    wards_gdf, facilities_gdf, meta = pipeline.run(city_key=city_key)
    print(f"  [OK] Ingested {len(wards_gdf)} wards and {len(facilities_gdf)} facilities.")
    print(f"       Total population: {meta['total_population']:,}")
    print(f"       Total hospital beds: {meta['total_beds']:,} ({meta['city_beds_per_1000']} beds/1000 pop)")

    # 2. Healthcare Gap Analysis
    gap_analyzer = HealthcareGapAnalyzer()
    wards_gdf = gap_analyzer.calculate_gap_scores(wards_gdf)
    print(f"  [OK] Computed Healthcare Gap Scores (Mean Gap: {wards_gdf['Gap_Score'].mean():.1f}/100)")

    # 3. Healthcare Desert Detection
    desert_detector = HealthcareDesertDetector()
    wards_gdf = desert_detector.detect_deserts(wards_gdf)
    desert_stats = desert_detector.summarize_deserts(wards_gdf)
    print(f"  [OK] Healthcare Deserts: {desert_stats['total_desert_wards']} wards ({desert_stats['percentage_desert_wards']}%)")

    # 4. Facility Pressure Analysis
    pressure_analyzer = FacilityPressureAnalyzer()
    facilities_gdf = pressure_analyzer.calculate_facility_pressure(facilities_gdf, wards_gdf, crs_proj=crs_proj)
    pressure_stats = pressure_analyzer.summarize_pressure(facilities_gdf)
    print(f"  [OK] Facility Pressure Analyzed. High/Critical Strain Facilities: {pressure_stats['critical_facilities_count']}")

    # 5. Save city-specific processed datasets
    out_wards = paths["processed_wards_geojson"]
    out_fac = paths["processed_fac_geojson"]
    wards_gdf.to_file(out_wards, driver="GeoJSON")
    facilities_gdf.to_file(out_fac, driver="GeoJSON")
    print(f"  [SAVED] {out_wards.name} & {out_fac.name}")

    # If Chennai (default city), also save to legacy paths for backwards compatibility
    if city_key == "chennai":
        legacy_wards = config.PROCESSED_DATA_DIR / "processed_wards.geojson"
        legacy_fac = config.PROCESSED_DATA_DIR / "processed_facilities.geojson"
        wards_gdf.to_file(legacy_wards, driver="GeoJSON")
        facilities_gdf.to_file(legacy_fac, driver="GeoJSON")
        print(f"  [SAVED] Backwards-compatible legacy files: {legacy_wards.name} & {legacy_fac.name}")

    return wards_gdf, facilities_gdf


def run_all_cities():
    """Runs preprocessing for all active supported cities and creates combined datasets."""
    print("=" * 65)
    print("CRADLE: MULTI-CITY PREPROCESSING & SPATIAL INTEGRATION PIPELINE")
    print("=" * 65)

    all_wards = []
    all_facilities = []

    active_cities = [k for k, v in config.SUPPORTED_CITIES.items() if v.get("is_active") is True]

    for city_key in active_cities:
        w_gdf, f_gdf = preprocess_single_city(city_key)
        all_wards.append(w_gdf)
        all_facilities.append(f_gdf)

    # Combine into all_cities GeoJSONs (in EPSG:4326 for cross-city GIS mapping/ML)
    combined_wards = gpd.GeoDataFrame(pd.concat(all_wards, ignore_index=True), crs=config.CRS_GEO)
    combined_fac = gpd.GeoDataFrame(pd.concat(all_facilities, ignore_index=True), crs=config.CRS_GEO)

    all_wards_path = config.PROCESSED_DATA_DIR / "all_cities_wards.geojson"
    all_fac_path = config.PROCESSED_DATA_DIR / "all_cities_facilities.geojson"
    combined_wards.to_file(all_wards_path, driver="GeoJSON")
    combined_fac.to_file(all_fac_path, driver="GeoJSON")

    print("\n" + "=" * 65)
    print("MULTI-CITY PREPROCESSING COMPLETE")
    print(f"Total Wards Processed across {len(active_cities)} cities: {len(combined_wards)}")
    print(f"Total Facilities Processed across {len(active_cities)} cities: {len(combined_fac)}")
    print(f"Combined datasets saved:")
    print(f"  -> {all_wards_path}")
    print(f"  -> {all_fac_path}")
    print("=" * 65)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Preprocess CRADLE data for one or all cities")
    parser.add_argument("--city", type=str, default=None, help="City key (e.g. chennai, coimbatore, bengaluru, hyderabad)")
    args = parser.parse_args()

    if args.city:
        preprocess_single_city(args.city.lower())
    else:
        run_all_cities()
