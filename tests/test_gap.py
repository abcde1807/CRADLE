"""
Unit tests for CRADLE Healthcare Gap Analyzer and Desert Detection
"""

import pytest
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon, Point

import config
from src.gap_analyzer import HealthcareGapAnalyzer
from src.healthcare_desert import HealthcareDesertDetector


@pytest.fixture
def mock_wards_gdf():
    """Creates a synthetic GeoDataFrame representing 5 test wards with varying conditions."""
    geoms = [
        Polygon([(80.20, 13.00), (80.22, 13.00), (80.22, 13.02), (80.20, 13.02)]),
        Polygon([(80.22, 13.00), (80.24, 13.00), (80.24, 13.02), (80.22, 13.02)]),
        Polygon([(80.24, 13.00), (80.26, 13.00), (80.26, 13.02), (80.24, 13.02)]),
        Polygon([(80.20, 13.02), (80.22, 13.02), (80.22, 13.04), (80.20, 13.04)]),
        Polygon([(80.22, 13.02), (80.24, 13.02), (80.24, 13.04), (80.22, 13.04)]),
    ]
    data = {
        "Ward_ID": [1, 2, 3, 4, 5],
        "Ward_Name": ["Ward 001", "Ward 002", "Ward 003", "Ward 004", "Ward 005"],
        "Zone": ["Zone North", "Zone North", "Zone Central", "Zone Central", "Zone South"],
        "Population": [40000, 35000, 50000, 20000, 60000],
        "Area_km2": [2.0, 2.0, 2.5, 3.0, 1.5],
        "Population_Density": [20000.0, 17500.0, 20000.0, 6666.7, 40000.0],
        "Healthcare_Facilities": [3, 0, 1, 4, 0],
        "Hospital_Beds": [120, 0, 15, 250, 0],
        "Total_Doctors": [20, 0, 3, 45, 0],
        "Beds_per_1000": [3.0, 0.0, 0.3, 12.5, 0.0],
        "Facilities_per_10k": [0.75, 0.0, 0.2, 2.0, 0.0],
        "Nearest_Facility_Distance": [0.3, 3.2, 1.5, 0.2, 4.5],
        "Nearest_Hospital_Distance": [1.2, 5.8, 3.8, 0.8, 6.2],
        "Elderly": [4000, 3500, 5000, 2000, 6000],
        "Children": [7000, 6000, 9000, 3600, 11000],
    }
    return gpd.GeoDataFrame(data, geometry=geoms, crs=config.CRS_GEO)


def test_gap_score_bounds_and_ranking(mock_wards_gdf):
    """Verifies that Gap Scores are bounded in [0, 100] and properly ranked."""
    analyzer = HealthcareGapAnalyzer()
    res = analyzer.calculate_gap_scores(mock_wards_gdf)

    assert "Gap_Score" in res.columns
    assert (res["Gap_Score"] >= 0.0).all()
    assert (res["Gap_Score"] <= 100.0).all()

    # Ward 5 has zero beds, zero facilities, high pop density, far from hospital -> should be Critical
    w5 = res[res["Ward_ID"] == 5].iloc[0]
    assert w5["Priority_Category"] in ["Critical", "High"]
    assert w5["Gap_Score"] > 70.0

    # Ward 4 has 12.5 beds/1000 and 4 facilities -> should be Low or Moderate
    w4 = res[res["Ward_ID"] == 4].iloc[0]
    assert w4["Gap_Score"] < w5["Gap_Score"]
    assert w4["Priority_Category"] in ["Low", "Moderate"]


def test_custom_weights(mock_wards_gdf):
    """Verifies dynamic weight updating and validation."""
    analyzer = HealthcareGapAnalyzer()

    # Valid custom weights
    custom = {
        "population_pressure": 0.50,
        "capacity_deficit": 0.30,
        "distance_gap": 0.10,
        "facility_scarcity": 0.10,
    }
    analyzer.update_weights(custom)
    res = analyzer.calculate_gap_scores(mock_wards_gdf)
    assert len(res) == len(mock_wards_gdf)

    # Invalid weights not summing to 1.0
    with pytest.raises(ValueError):
        analyzer.update_weights({"population_pressure": 0.8, "capacity_deficit": 0.8, "distance_gap": 0.1, "facility_scarcity": 0.1})


def test_explainability_generation(mock_wards_gdf):
    """Verifies explainability text and primary issue diagnostic."""
    analyzer = HealthcareGapAnalyzer()
    res = analyzer.calculate_gap_scores(mock_wards_gdf)

    assert "Primary_Issue" in res.columns
    assert "Explainability_Text" in res.columns

    for _, row in res.iterrows():
        assert len(row["Primary_Issue"]) > 10
        assert str(row["Ward_ID"]) in row["Explainability_Text"]
        assert "Gap Score" in row["Explainability_Text"]


def test_healthcare_desert_detection(mock_wards_gdf):
    """Verifies desert identification logic and affected population."""
    analyzer = HealthcareGapAnalyzer()
    res = analyzer.calculate_gap_scores(mock_wards_gdf)

    detector = HealthcareDesertDetector()
    desert_gdf = detector.detect_deserts(res)

    assert "Healthcare_Desert" in desert_gdf.columns
    assert "Healthcare_Desert_Severity" in desert_gdf.columns
    assert "Desert_Affected_Population" in desert_gdf.columns

    # Ward 5 has high gap, dist to hospital > 3.5km, beds < 1.0 -> Healthcare Desert
    w5 = desert_gdf[desert_gdf["Ward_ID"] == 5].iloc[0]
    assert w5["Healthcare_Desert"] is True or w5["Healthcare_Desert"] == 1
    assert w5["Healthcare_Desert_Severity"] > 50.0
    assert w5["Desert_Affected_Population"] == 60000

    # Ward 4 is well served -> NOT a desert
    w4 = desert_gdf[desert_gdf["Ward_ID"] == 4].iloc[0]
    assert not w4["Healthcare_Desert"]
    assert w4["Healthcare_Desert_Severity"] == 0.0


def test_edge_cases_zero_population_and_missing_data():
    """Verifies robust handling of zero population, missing beds, or zero facilities."""
    geoms = [Polygon([(80.20, 13.00), (80.22, 13.00), (80.22, 13.02), (80.20, 13.02)])]
    edge_df = gpd.GeoDataFrame({
        "Ward_ID": [999],
        "Ward_Name": ["Empty Ward"],
        "Zone": ["Test"],
        "Population": [0],
        "Area_km2": [1.0],
        "Population_Density": [0.0],
        "Healthcare_Facilities": [0],
        "Hospital_Beds": [0],
        "Beds_per_1000": [0.0],
    }, geometry=geoms, crs=config.CRS_GEO)

    analyzer = HealthcareGapAnalyzer()
    res = analyzer.calculate_gap_scores(edge_df)
    assert len(res) == 1
    assert 0.0 <= res.iloc[0]["Gap_Score"] <= 100.0
