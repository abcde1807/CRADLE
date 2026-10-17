"""
CRADLE Multi-City Architecture Test Suite
Verifies multi-city configuration registry, UTM metric CRS mappings,
per-city processed datasets, and composite ID uniqueness.
"""

import pytest
import geopandas as gpd
import pandas as pd

import config
from src.data_loader import DataLoader
from src.gap_analyzer import HealthcareGapAnalyzer
from src.healthcare_desert import HealthcareDesertDetector


def test_supported_cities_config():
    """Validates configuration entries for all active cities."""
    active_cities = [k for k, v in config.SUPPORTED_CITIES.items() if v.get("is_active") is True]
    assert len(active_cities) == 5
    assert set(active_cities) == {"chennai", "coimbatore", "bengaluru", "hyderabad", "delhi"}

    for city in active_cities:
        cfg = config.get_city_config(city)
        assert "city_name" in cfg
        assert "state_code" in cfg
        assert "crs_proj" in cfg
        assert "center" in cfg
        assert len(cfg["center"]) == 2
        assert "bbox" in cfg
        assert cfg["admin_count"] > 0


def test_metric_crs_mappings():
    """Verifies that cities in different UTM zones receive distinct metric projections."""
    assert config.get_city_crs("chennai") == "EPSG:32644"      # UTM 44N
    assert config.get_city_crs("hyderabad") == "EPSG:32644"    # UTM 44N
    assert config.get_city_crs("coimbatore") == "EPSG:32643"   # UTM 43N
    assert config.get_city_crs("bengaluru") == "EPSG:32643"    # UTM 43N
    assert config.get_city_crs("delhi") == "EPSG:32643"        # UTM 43N


def test_per_city_processed_datasets():
    """Verifies that each active city produces valid processed GeoJSON files."""
    active_cities = [k for k, v in config.SUPPORTED_CITIES.items() if v.get("is_active") is True]

    for city in active_cities:
        paths = config.get_city_data_paths(city)
        wards_file = paths["processed_wards_geojson"]
        fac_file = paths["processed_fac_geojson"]

        assert wards_file.exists(), f"Processed wards file missing for {city}: {wards_file}"
        assert fac_file.exists(), f"Processed facilities file missing for {city}: {fac_file}"

        w_gdf = gpd.read_file(wards_file)
        f_gdf = gpd.read_file(fac_file)

        assert len(w_gdf) > 0
        assert len(f_gdf) > 0
        assert "Gap_Score" in w_gdf.columns
        assert "Priority_Category" in w_gdf.columns
        assert "Healthcare_Desert" in w_gdf.columns
        assert "Estimated_Pop_Served" in f_gdf.columns
        assert "Pressure_Category" in f_gdf.columns


def test_composite_id_schema_and_uniqueness():
    """Verifies composite ID schema and ensures zero ID collisions across all cities."""
    all_wards_path = config.PROCESSED_DATA_DIR / "all_cities_wards.geojson"
    assert all_wards_path.exists()

    all_gdf = gpd.read_file(all_wards_path)
    assert len(all_gdf) == 898

    assert "Composite_ID" in all_gdf.columns
    # Check no duplicates
    assert all_gdf["Composite_ID"].nunique() == len(all_gdf)

    # Check prefix formatting IND_{STATE}_{CITY}_
    for comp_id in all_gdf["Composite_ID"].head(50):
        parts = comp_id.split("_")
        assert len(parts) == 4
        assert parts[0] == "IND"
        assert parts[1] in ["TN", "KA", "TS", "DL"]
