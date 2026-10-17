"""
Unit tests for CRADLE Population Coverage and Before/After Scenario Simulation
"""

import pytest
import geopandas as gpd
from shapely.geometry import Polygon, Point

import config
from src.coverage import PopulationCoverageAnalyzer
from src.scenario import ScenarioSimulator


@pytest.fixture
def mock_simulation_data():
    """Builds two adjacent wards and one baseline facility."""
    w1_geom = Polygon([(80.20, 13.00), (80.22, 13.00), (80.22, 13.02), (80.20, 13.02)])
    w2_geom = Polygon([(80.22, 13.00), (80.24, 13.00), (80.24, 13.02), (80.22, 13.02)])

    wards_gdf = gpd.GeoDataFrame({
        "Ward_ID": [1, 2],
        "Ward_Name": ["Ward 01", "Ward 02"],
        "Zone": ["Zone A", "Zone A"],
        "Population": [40000, 50000],
        "Area_km2": [2.0, 2.0],
        "Population_Density": [20000.0, 25000.0],
        "Healthcare_Facilities": [1, 0],
        "Hospital_Beds": [50, 0],
        "Total_Doctors": [6, 0],
        "Beds_per_1000": [1.25, 0.0],
        "Facilities_per_10k": [0.25, 0.0],
        "Nearest_Facility_Distance": [0.5, 3.5],
        "Nearest_Hospital_Distance": [0.5, 4.5],
        "Gap_Score": [45.0, 85.0],
        "Priority_Category": ["Moderate", "Critical"],
        "Healthcare_Desert": [False, True],
        "Desert_Affected_Population": [0, 50000],
    }, geometry=[w1_geom, w2_geom], crs=config.CRS_GEO)

    fac_gdf = gpd.GeoDataFrame({
        "Facility_ID": ["F1"],
        "Facility_Name": ["Old Clinic"],
        "Latitude": [13.01],
        "Longitude": [80.21],
        "Facility_Type": ["CHC"],
        "Beds": [50],
        "Doctors": [6],
        "Ownership": ["Public"],
    }, geometry=[Point(80.21, 13.01)], crs=config.CRS_GEO)

    return wards_gdf, fac_gdf


def test_multi_radius_coverage(mock_simulation_data):
    """Verifies coverage across 2km, 3km, 5km concentric buffers."""
    wards_gdf, _ = mock_simulation_data
    cov_analyzer = PopulationCoverageAnalyzer(radii_km=[2.0, 3.0, 5.0])

    target_pt = Point(80.23, 13.01)  # Center of Ward 2
    res = cov_analyzer.evaluate_multi_radius_coverage(target_pt, wards_gdf)

    assert "2km" in res
    assert "3km" in res
    assert "5km" in res

    # Monotonic property: larger buffer covers greater or equal population
    assert res["5km"]["population_covered"] >= res["3km"]["population_covered"]
    assert res["3km"]["population_covered"] >= res["2km"]["population_covered"]
    assert res["2km"]["population_covered"] > 0


def test_before_vs_after_simulation(mock_simulation_data):
    """Verifies that adding a facility reduces Gap Score and alleviates desert status."""
    wards_gdf, fac_gdf = mock_simulation_data
    simulator = ScenarioSimulator()

    cand_pt = Point(80.23, 13.01)  # Add hospital in Ward 2 (Critical ward)
    after_wards, after_facs, metrics = simulator.simulate_facility_addition(
        wards_gdf=wards_gdf,
        facilities_gdf=fac_gdf,
        candidate_location=cand_pt,
        facility_type="Government Hospital",
        beds=150,
        coverage_radius_km=3.0,
    )

    # Facilities increased by 1
    assert len(after_facs) == len(fac_gdf) + 1

    # Citywide average gap score must decrease
    assert metrics["citywide_gap_reduction"] > 0
    assert metrics["after_avg_gap"] < metrics["before_avg_gap"]

    # Ward 2 gap score specifically must decrease significantly
    w2_before = wards_gdf[wards_gdf["Ward_ID"] == 2].iloc[0]["Gap_Score"]
    w2_after = after_wards[after_wards["Ward_ID"] == 2].iloc[0]["Gap_Score"]
    assert w2_after < w2_before

    # Critical wards reduced
    assert metrics["after_critical_wards"] <= metrics["before_critical_wards"]
