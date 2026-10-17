"""
Unit tests for CRADLE Candidate Location Generator and Ranking
"""

import pytest
import geopandas as gpd
from shapely.geometry import Polygon, Point

import config
from src.candidate_generator import CandidateLocationGenerator
from src.candidate_ranking import CandidateRanker
from src.gap_analyzer import HealthcareGapAnalyzer


@pytest.fixture
def sample_system():
    """Generates small mock system for candidate testing."""
    ward_geom = Polygon([(80.20, 13.00), (80.24, 13.00), (80.24, 13.04), (80.20, 13.04)])
    wards_gdf = gpd.GeoDataFrame({
        "Ward_ID": [101],
        "Ward_Name": ["Critical Ward"],
        "Zone": ["Test Zone"],
        "Population": [45000],
        "Area_km2": [4.0],
        "Population_Density": [11250.0],
        "Healthcare_Facilities": [0],
        "Hospital_Beds": [0],
        "Beds_per_1000": [0.0],
        "Nearest_Facility_Distance": [3.5],
        "Nearest_Hospital_Distance": [5.0],
        "Gap_Score": [82.5],
        "Priority_Category": ["Critical"],
        "Healthcare_Desert": [True],
    }, geometry=[ward_geom], crs=config.CRS_GEO)

    fac_gdf = gpd.GeoDataFrame({
        "Facility_ID": ["FAC_001"],
        "Facility_Name": ["Existing Clinic"],
        "Latitude": [13.01],
        "Longitude": [80.21],
        "Facility_Type": ["PHC"],
        "Beds": [10],
        "Doctors": [2],
        "Ownership": ["Public"],
    }, geometry=[Point(80.21, 13.01)], crs=config.CRS_GEO)

    return wards_gdf, fac_gdf


def test_candidate_generation_and_buffering(sample_system):
    """Verifies that candidates are generated inside wards and outside facility buffers."""
    wards_gdf, fac_gdf = sample_system
    gen = CandidateLocationGenerator(grid_size_meters=800, buffer_meters=500)
    cands = gen.generate_candidates(wards_gdf, fac_gdf)

    assert len(cands) > 0
    assert "Candidate_ID" in cands.columns
    assert "Latitude" in cands.columns
    assert "Longitude" in cands.columns

    # Verify every candidate is inside the ward polygon
    ward_poly = wards_gdf.geometry.iloc[0]
    for pt in cands.geometry:
        assert ward_poly.buffer(0.001).contains(pt)

    # Verify no candidate is within 500m of the existing facility
    fac_utm = fac_gdf.to_crs(config.CRS_PROJ).geometry.iloc[0]
    cands_utm = cands.to_crs(config.CRS_PROJ)
    distances = cands_utm.geometry.distance(fac_utm)
    assert (distances >= 490).all()


def test_candidate_ranking_and_scores(sample_system):
    """Verifies candidate scoring in [0, 100], recommendations, and rank ordering."""
    wards_gdf, fac_gdf = sample_system
    gen = CandidateLocationGenerator(grid_size_meters=1000)
    cands = gen.generate_candidates(wards_gdf, fac_gdf)

    ranker = CandidateRanker()
    ranked = ranker.rank_candidates(cands, wards_gdf, fac_gdf, coverage_radius_m=2500)

    assert "Candidate_Score" in ranked.columns
    assert "Rank" in ranked.columns
    assert "Recommendation" in ranked.columns

    assert (ranked["Candidate_Score"] >= 0.0).all()
    assert (ranked["Candidate_Score"] <= 100.0).all()

    # Ranks should be 1 to N ordered
    assert list(ranked["Rank"]) == sorted(list(ranked["Rank"]))
    assert ranked.iloc[0]["Candidate_Score"] >= ranked.iloc[-1]["Candidate_Score"]


def test_empty_candidates_handling(sample_system):
    """Verifies ranker handles empty candidates without throwing uncaught exceptions."""
    wards_gdf, fac_gdf = sample_system
    empty_cands = gpd.GeoDataFrame(columns=["Candidate_ID", "geometry"], crs=config.CRS_GEO)
    ranker = CandidateRanker()
    res = ranker.rank_candidates(empty_cands, wards_gdf, fac_gdf)
    assert len(res) == 0
