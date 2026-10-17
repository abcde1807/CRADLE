"""
CRADLE Two-Step Floating Catchment Area (2SFCA) Accessibility Module
Implements the 2SFCA spatial accessibility method with distance-decay kernels (gravity, Gaussian, binary),
computing ward-level healthcare supply-to-demand accessibility indices.
"""

from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
import geopandas as gpd
from scipy.spatial.distance import cdist

import config


class TwoSFCAAnalyzer:
    """
    Computes spatial accessibility using Two-Step Floating Catchment Area (2SFCA):
    Step 1: Compute facility provider-to-population ratio R_j
    Step 2: Sum provider ratios R_j for each ward to obtain accessibility index A_i
    """

    def __init__(
        self,
        catchment_radius_km: float = config.TWO_SFCA_CONFIG["catchment_radius_km"],
        decay_type: str = config.TWO_SFCA_CONFIG["decay_type"],
        gravity_beta: float = config.TWO_SFCA_CONFIG["gravity_beta"],
    ):
        self.d0_km = catchment_radius_km
        self.decay_type = decay_type
        self.beta = gravity_beta

    def _decay_kernel(self, dist_km: np.ndarray) -> np.ndarray:
        """Evaluates distance decay function f(d_ij) within catchment threshold d0."""
        in_catchment = dist_km <= self.d0_km
        weights = np.zeros_like(dist_km, dtype=float)

        if self.decay_type == "binary":
            weights[in_catchment] = 1.0
        elif self.decay_type == "gravity":
            d_safe = np.maximum(dist_km, 0.5)
            weights[in_catchment] = (d_safe[in_catchment] / self.d0_km) ** (-self.beta)
        elif self.decay_type == "gaussian":
            weights[in_catchment] = (
                (np.exp(-0.5 * (dist_km[in_catchment] / self.d0_km) ** 2) - np.exp(-0.5))
                / (1.0 - np.exp(-0.5))
            )
        else:
            weights[in_catchment] = 1.0

        return weights

    def calculate_accessibility(
        self,
        wards_gdf: gpd.GeoDataFrame,
        facilities_gdf: gpd.GeoDataFrame,
    ) -> gpd.GeoDataFrame:
        """
        Executes 2SFCA analysis:
        Returns wards GeoDataFrame with columns:
        - `Two_SFCA_Score`: raw accessibility index (beds per person accessible)
        - `Two_SFCA_Norm`: normalized score 0–100
        - `Accessibility_Tier`: Very High, High, Moderate, Low, Severely Deficient
        """
        wards = wards_gdf.copy()
        fac = facilities_gdf.copy()

        # Determine metric CRS
        if "City_Key" in wards.columns and len(wards["City_Key"].dropna()) > 0:
            crs_proj = config.get_city_crs(wards["City_Key"].dropna().iloc[0])
        elif wards.crs and wards.crs.is_projected:
            crs_proj = wards.crs
        else:
            crs_proj = config.CRS_PROJ

        # Extract coordinates in metric CRS
        wards_utm = wards.to_crs(crs_proj)
        fac_utm = fac.to_crs(crs_proj)

        ward_coords = np.array([(g.centroid.x, g.centroid.y) for g in wards_utm.geometry])
        fac_coords = np.array([(g.x, g.y) for g in fac_utm.geometry])

        # Distance matrix in km
        dist_matrix_km = cdist(ward_coords, fac_coords, metric="euclidean") / 1000.0

        # Weights matrix W_ij
        weights_matrix = self._decay_kernel(dist_matrix_km)  # shape (num_wards, num_fac)

        # Facility capacity (Beds, min 5 to avoid zero supply)
        supply_s = fac["Beds"].clip(lower=5).values  # shape (num_fac,)
        pop_p = wards["Population"].values  # shape (num_wards,)

        # Step 1: For each facility j, compute denominator D_j = sum_{k} P_k * W_kj
        denominator_j = (pop_p[:, np.newaxis] * weights_matrix).sum(axis=0)  # shape (num_fac,)
        denominator_j = np.maximum(denominator_j, 1.0)

        # Provider-to-population ratio R_j (beds per 1000 people)
        r_j = (supply_s / denominator_j) * 1000.0  # shape (num_fac,)

        # Step 2: For each ward i, sum R_j * W_ij
        accessibility_a_i = (weights_matrix * r_j[np.newaxis, :]).sum(axis=1)

        wards["Two_SFCA_Score"] = np.round(accessibility_a_i, 3)

        # Normalize to 0–100 scale
        max_acc = np.percentile(accessibility_a_i, 95) or 1.0
        wards["Two_SFCA_Norm"] = np.round((accessibility_a_i / max(max_acc, 0.01)).clip(0.0, 1.0) * 100.0, 1)

        # Assign accessibility tiers
        wards["Accessibility_Tier"] = wards["Two_SFCA_Norm"].apply(self.classify_tier)

        return wards

    @staticmethod
    def classify_tier(norm_score: float) -> str:
        """Classifies 2SFCA accessibility into descriptive planning tiers."""
        if norm_score >= 80.0:
            return "Very High Access"
        elif norm_score >= 60.0:
            return "High Access"
        elif norm_score >= 40.0:
            return "Moderate Access"
        elif norm_score >= 20.0:
            return "Low Access"
        else:
            return "Severely Deficient Access"
