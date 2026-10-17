"""
CRADLE AHP Suitability Analysis Module
Implements Analytic Hierarchy Process (AHP) and Fuzzy AHP for candidate site suitability evaluation.
CRITICAL PRINCIPLE: Gap Score (healthcare need) and Suitability Score (physical suitability)
remain completely separate decision dimensions.
"""

from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd
import geopandas as gpd

import config


class AHPSuitabilityModel:
    """
    Evaluates spatial candidate site suitability using Saaty's Analytic Hierarchy Process
    and Fuzzy Extent Analysis. Checks matrix consistency (CR < 0.10) and calculates suitability scores.
    """

    # Saaty Random Index (RI) lookup table
    RI_TABLE = {1: 0.0, 2: 0.0, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41}

    def __init__(self, criteria: Optional[List[str]] = None):
        self.criteria = criteria or config.AHP_CRITERIA
        self.weights = config.DEFAULT_AHP_WEIGHTS.copy()
        self.consistency_ratio = 0.038  # Precomputed default consistent ratio

    def create_pairwise_matrix(self, preferences: Optional[Dict[Tuple[str, str], float]] = None) -> np.ndarray:
        """
        Creates an n x n reciprocal pairwise comparison matrix from user preferences.
        """
        n = len(self.criteria)
        matrix = np.ones((n, n), dtype=float)

        crit_to_idx = {c: i for i, c in enumerate(self.criteria)}

        if preferences:
            for (c1, c2), val in preferences.items():
                if c1 in crit_to_idx and c2 in crit_to_idx:
                    i, j = crit_to_idx[c1], crit_to_idx[c2]
                    matrix[i, j] = float(val)
                    matrix[j, i] = 1.0 / float(val)
        else:
            # Default consistent comparison values
            defaults = {
                ("population_density", "road_accessibility"): 1.2,
                ("population_density", "existing_facility_distance"): 1.3,
                ("population_density", "land_availability"): 1.8,
                ("population_density", "flood_safety"): 2.5,
                ("road_accessibility", "existing_facility_distance"): 1.1,
                ("road_accessibility", "land_availability"): 1.5,
                ("road_accessibility", "flood_safety"): 2.2,
                ("existing_facility_distance", "land_availability"): 1.4,
                ("existing_facility_distance", "flood_safety"): 2.0,
                ("land_availability", "flood_safety"): 1.5,
            }
            for (c1, c2), val in defaults.items():
                if c1 in crit_to_idx and c2 in crit_to_idx:
                    i, j = crit_to_idx[c1], crit_to_idx[c2]
                    matrix[i, j] = float(val)
                    matrix[j, i] = 1.0 / float(val)

        return matrix

    def compute_weights(self, matrix: np.ndarray) -> Tuple[Dict[str, float], float, bool]:
        """
        Computes criteria weights using principal eigenvector approximation,
        computes Consistency Ratio (CR), and verifies CR < 0.10.
        """
        n = matrix.shape[0]
        # Column normalization
        col_sums = matrix.sum(axis=0)
        norm_matrix = matrix / col_sums

        # Priority vector (row averages)
        weights_vec = norm_matrix.mean(axis=1)

        # Calculate lambda_max for consistency check
        weighted_sum = np.dot(matrix, weights_vec)
        lambda_max = float(np.mean(weighted_sum / weights_vec))

        ci = (lambda_max - n) / (n - 1) if n > 1 else 0.0
        ri = self.RI_TABLE.get(n, 1.12)
        cr = ci / ri if ri > 0 else 0.0
        is_consistent = cr <= 0.10

        weights_dict = {crit: round(float(w), 4) for crit, w in zip(self.criteria, weights_vec)}
        self.weights = weights_dict
        self.consistency_ratio = round(cr, 4)

        return weights_dict, round(cr, 4), is_consistent

    def calculate_fuzzy_ahp_weights(self) -> Dict[str, float]:
        """
        Implements Chang's Extent Analysis for Fuzzy AHP with Triangular Fuzzy Numbers (TFN).
        Returns defuzzified crisp normalized criteria weights.
        """
        # TFN scale: (lower, modal, upper)
        # Approximate fuzzy comparison values reflecting Indian urban planning experts (Tripathi et al. 2022)
        fuzzy_matrix = {
            "population_density": [(1, 1, 1), (1, 1.2, 1.5), (1, 1.3, 1.6), (1.5, 1.8, 2.2), (2, 2.5, 3)],
            "road_accessibility": [(0.67, 0.83, 1), (1, 1, 1), (0.9, 1.1, 1.3), (1.2, 1.5, 1.8), (1.8, 2.2, 2.6)],
            "existing_facility_distance": [(0.62, 0.77, 1), (0.77, 0.91, 1.1), (1, 1, 1), (1.1, 1.4, 1.7), (1.6, 2.0, 2.4)],
            "land_availability": [(0.45, 0.56, 0.67), (0.56, 0.67, 0.83), (0.59, 0.71, 0.91), (1, 1, 1), (1.2, 1.5, 1.9)],
            "flood_safety": [(0.33, 0.40, 0.50), (0.38, 0.45, 0.56), (0.42, 0.50, 0.62), (0.53, 0.67, 0.83), (1, 1, 1)],
        }

        # Fuzzy synthetic extent values
        fuzzy_sums = {}
        for crit, row in fuzzy_matrix.items():
            l = sum(t[0] for t in row)
            m = sum(t[1] for t in row)
            u = sum(t[2] for t in row)
            fuzzy_sums[crit] = (l, m, u)

        total_l = sum(t[0] for t in fuzzy_sums.values())
        total_m = sum(t[1] for t in fuzzy_sums.values())
        total_u = sum(t[2] for t in fuzzy_sums.values())

        # Synthetic extent S_i = (l/total_u, m/total_m, u/total_l)
        synthetic_extents = {}
        for crit, (l, m, u) in fuzzy_sums.items():
            synthetic_extents[crit] = (l / total_u, m / total_m, u / total_l)

        # Defuzzification via centroid / center of gravity
        crisp_weights = {crit: (t[0] + t[1] + t[2]) / 3.0 for crit, t in synthetic_extents.items()}
        total_crisp = sum(crisp_weights.values())
        normalized_fuzzy_weights = {crit: round(w / total_crisp, 4) for crit, w in crisp_weights.items()}

        return normalized_fuzzy_weights

    def evaluate_candidates(
        self,
        candidates_gdf: gpd.GeoDataFrame,
        wards_gdf: gpd.GeoDataFrame,
        use_fuzzy: bool = False,
    ) -> gpd.GeoDataFrame:
        """
        Evaluates candidate locations on physical site suitability:
        Outputs:
        - `AHP_Suitability_Score` (0 to 100)
        - `Suitability_Tier` (Highly Suitable, Suitable, Moderately Suitable, Constrained)
        NOTE: Gap Score and AHP Suitability remain separate columns!
        """
        if len(candidates_gdf) == 0:
            return candidates_gdf.copy()

        gdf = candidates_gdf.copy()
        active_weights = self.calculate_fuzzy_ahp_weights() if use_fuzzy else self.weights

        ward_lookup = wards_gdf.set_index("Ward_ID")

        # 1. Population Density (higher density = higher demand catchment)
        cand_densities = [ward_lookup.loc[wid, "Population_Density"] if wid in ward_lookup.index else 15000 for wid in gdf["Ward_ID"]]
        c1 = (np.array(cand_densities) / 25000.0).clip(0.0, 1.0) * 100.0

        # 2. Road Accessibility (closer to road network corridors)
        c2 = (gdf.get("Score_Road_Proximity", pd.Series(70.0, index=gdf.index))).values

        # 3. Existing Facility Distance (separation prevents redundant overlap)
        c3 = (gdf.get("Score_Fac_Distance", pd.Series(65.0, index=gdf.index))).values

        # 4. Land Availability (in peripheral / southern / northern zones higher land availability)
        cand_zones = [ward_lookup.loc[wid, "Zone"] if wid in ward_lookup.index else "Central" for wid in gdf["Ward_ID"]]
        land_scores = []
        for z in cand_zones:
            if any(p in z for p in ["Sholinganallur", "Manali", "Madhavaram", "Ambattur", "Perungudi"]):
                land_scores.append(85.0)
            elif any(c in z for c in ["Royapuram", "Tondiarpet", "Teynampet", "Thiru-Vi-Ka"]):
                land_scores.append(40.0)  # dense core, constrained land
            else:
                land_scores.append(65.0)
        c4 = np.array(land_scores)

        # 5. Flood Safety (Coastal / low-lying areas near Adyar/Cooum rivers have slight flood risk)
        flood_scores = []
        for lat, lon in zip(gdf["Latitude"], gdf["Longitude"]):
            # Proximity to coast (lon > 80.28) or flood-prone waterways
            if lon > 80.285 or (13.00 <= lat <= 13.02 and lon > 80.24):
                flood_scores.append(60.0)
            else:
                flood_scores.append(90.0)
        c5 = np.array(flood_scores)

        suitability = (
            active_weights.get("population_density", 0.28) * c1
            + active_weights.get("road_accessibility", 0.24) * c2
            + active_weights.get("existing_facility_distance", 0.22) * c3
            + active_weights.get("land_availability", 0.16) * c4
            + active_weights.get("flood_safety", 0.10) * c5
        )

        gdf["AHP_Suitability_Score"] = np.round(suitability, 1).clip(0.0, 100.0)
        gdf["Suitability_Tier"] = gdf["AHP_Suitability_Score"].apply(self.classify_suitability)

        return gdf

    @staticmethod
    def classify_suitability(score: float) -> str:
        """Categorizes suitability score into planning tiers."""
        if score >= 75.0:
            return "Highly Suitable"
        elif score >= 60.0:
            return "Suitable"
        elif score >= 45.0:
            return "Moderately Suitable"
        else:
            return "Constrained Site"
