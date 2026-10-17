"""
CRADLE Facility Pressure Analysis Module
Computes estimated population catchment and pressure load for healthcare facilities
using spatial gravity allocation, classifying facilities by strain level.
"""

from typing import Dict, Any, List
import numpy as np
import pandas as pd
import geopandas as gpd
from scipy.spatial.distance import cdist

import config


class FacilityPressureAnalyzer:
    """
    Allocates ward population demand to healthcare facilities using distance-decayed
    gravity allocation and computes Facility Pressure (Demand / Capacity).
    """

    def __init__(self, beta: float = 1.5, max_distance_km: float = 8.0):
        self.beta = beta
        self.max_distance_km = max_distance_km

    def calculate_facility_pressure(
        self,
        facilities_gdf: gpd.GeoDataFrame,
        wards_gdf: gpd.GeoDataFrame,
        crs_proj: str = None,
    ) -> gpd.GeoDataFrame:
        """
        Calculates Estimated_Population_Served and Pressure_Ratio for each facility.
        Pressure_Ratio = Allocated_Population / (Beds * WHO_Benchmark_Ratio)
        """
        fac = facilities_gdf.copy()
        wards = wards_gdf.copy()

        # Determine metric CRS
        if crs_proj is None:
            if "City_Key" in wards.columns and len(wards["City_Key"].dropna()) > 0:
                city_key = wards["City_Key"].dropna().iloc[0]
                crs_proj = config.get_city_crs(city_key)
            elif wards.crs and wards.crs.is_projected:
                crs_proj = wards.crs
            else:
                crs_proj = config.CRS_PROJ

        # Project to metric CRS for distance computation
        fac_utm = fac.to_crs(crs_proj)
        wards_utm = wards.to_crs(crs_proj)

        fac_coords = np.array([(g.x, g.y) for g in fac_utm.geometry])
        ward_coords = np.array([(g.centroid.x, g.centroid.y) for g in wards_utm.geometry])

        # Distance matrix in kilometers
        dist_matrix_km = cdist(ward_coords, fac_coords, metric="euclidean") / 1000.0

        # Facility capacity attractiveness (based on beds and facility level)
        # Avoid 0 capacity: min effective beds = 5
        fac_capacities = fac["Beds"].clip(lower=5).values

        # Gravity weights: W_ij = Capacity_j / (Distance_ij^beta)
        dist_clamped = np.maximum(dist_matrix_km, 0.5)  # min distance 500m to avoid division by zero
        attractiveness = (fac_capacities[np.newaxis, :] ** 0.8) / (dist_clamped ** self.beta)

        # Zero out attractiveness beyond max distance
        attractiveness[dist_matrix_km > self.max_distance_km] = 0.0

        # Normalize row-wise so each ward's population is distributed among accessible facilities
        row_sums = attractiveness.sum(axis=1, keepdims=True)
        # If a ward is too remote to reach any facility within max_dist, assign to nearest
        unreachable = (row_sums.squeeze() == 0)
        if np.any(unreachable):
            nearest_fac = np.argmin(dist_matrix_km[unreachable], axis=1)
            attractiveness[unreachable, nearest_fac] = 1.0
            row_sums = attractiveness.sum(axis=1, keepdims=True)

        prob_matrix = attractiveness / row_sums

        # Apportion ward populations
        ward_pops = wards["Population"].values[:, np.newaxis]
        allocated_pop = (prob_matrix * ward_pops).sum(axis=0)

        fac["Estimated_Pop_Served"] = np.round(allocated_pop).astype(int)

        # Facility capacity benchmark: In a standard system, 1 hospital bed serves ~333 citizens (WHO 3 beds/1000 pop)
        # For primary centres, 1 bed capacity benchmark is ~500 citizens
        benchmark_pop_per_bed = 333.3
        capacity_threshold = fac_capacities * benchmark_pop_per_bed

        pressure_ratio = fac["Estimated_Pop_Served"] / np.maximum(capacity_threshold, 1.0)
        fac["Pressure_Ratio"] = np.round(pressure_ratio, 2)

        # Categorize pressure
        fac["Pressure_Category"] = fac["Pressure_Ratio"].apply(self.classify_pressure)

        return fac

    @staticmethod
    def classify_pressure(ratio: float) -> str:
        """Categorizes facility pressure ratio into risk tiers."""
        if ratio >= 5.0:
            return "Critical"
        elif ratio >= 2.5:
            return "High"
        elif ratio >= 1.0:
            return "Moderate"
        else:
            return "Low"

    def summarize_pressure(self, facilities_gdf: gpd.GeoDataFrame) -> Dict[str, Any]:
        """Provides citywide summary of facility strains."""
        counts = facilities_gdf["Pressure_Category"].value_counts().to_dict()
        critical_facs = facilities_gdf[facilities_gdf["Pressure_Category"] == "Critical"]

        return {
            "total_facilities": len(facilities_gdf),
            "pressure_breakdown": counts,
            "critical_facilities_count": len(critical_facs),
            "critical_facilities_list": critical_facs[[
                "Facility_ID", "Facility_Name", "Facility_Type", "Beds", "Estimated_Pop_Served", "Pressure_Ratio"
            ]].head(10).to_dict(orient="records"),
            "mean_pressure_ratio": round(facilities_gdf["Pressure_Ratio"].mean(), 2),
        }
