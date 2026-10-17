"""
CRADLE Machine Learning Test Suite
Tests predictor initialization, single-ward inference, batch GeoDataFrame enrichment,
and Leave-One-City-Out Spatial Cross Validation output fidelity.
"""

import pytest
import numpy as np
import pandas as pd
import geopandas as gpd

import config
from src.model_inference import CradlePredictor
from src.model_training import FEATURE_COLUMNS, PRIORITY_CLASSES


@pytest.fixture
def predictor():
    """Initializes and returns the singleton predictor instance."""
    return CradlePredictor()


def test_predictor_initialization_and_metadata(predictor):
    """Verifies model loads properly and contains valid metadata."""
    info = predictor.get_model_info()
    assert "version" in info
    assert info["training_samples"] >= 800
    assert set(info["cities"]) == {"chennai", "coimbatore", "bengaluru", "hyderabad", "delhi"}
    assert all(f in info["feature_names"] for f in FEATURE_COLUMNS)
    assert info["loco_classifier_accuracy"] >= 0.75
    assert info["loco_regressor_rmse"] < 10.0


def test_single_ward_prediction(predictor):
    """Tests single-ward dictionary inference and probability distributions."""
    sample_ward = {
        "Population": 45000,
        "Population_Density": 18000.0,
        "Elderly": 5000,
        "Children": 7500,
        "Households": 11000,
        "Vuln_Ratio": 0.278,
        "Nearest_Facility_Distance": 3.8,
        "Nearest_Hospital_Distance": 6.2,
        "Healthcare_Facilities": 0,
        "Beds_per_1000": 0.2,
    }

    result = predictor.predict_ward(sample_ward)

    assert "predicted_priority" in result
    assert result["predicted_priority"] in PRIORITY_CLASSES
    assert 0.0 <= result["predicted_gap_score"] <= 100.0
    assert 0.0 <= result["confidence"] <= 1.0

    # Probabilities must sum to ~1.0
    probs = result["priority_probabilities"]
    assert len(probs) == len(PRIORITY_CLASSES)
    assert abs(sum(probs.values()) - 1.0) < 0.01

    # Check top drivers explainability
    assert len(result["top_drivers"]) > 0


def test_batch_prediction_on_processed_data(predictor):
    """Tests batch prediction on actual multi-city processed GeoDataFrame."""
    wards_path = config.PROCESSED_DATA_DIR / "all_cities_wards.geojson"
    assert wards_path.exists(), "Processed all_cities_wards.geojson must exist"

    gdf = gpd.read_file(wards_path)
    sample_gdf = gdf.head(25).copy()

    enriched = predictor.predict_batch(sample_gdf)

    assert "ML_Predicted_Priority" in enriched.columns
    assert "ML_Confidence" in enriched.columns
    assert "ML_Predicted_Gap_Score" in enriched.columns
    assert enriched["ML_Predicted_Priority"].isin(PRIORITY_CLASSES).all()
    assert (enriched["ML_Predicted_Gap_Score"] >= 0.0).all()
    assert (enriched["ML_Predicted_Gap_Score"] <= 100.0).all()
