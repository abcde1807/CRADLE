"""
CRADLE Healthcare Desert Detection Module
Identifies urban healthcare deserts where high population demand coincides with severe
capacity deficits, sparse facilities, and elevated spatial distance to secondary/emergency care.
"""

from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd
import geopandas as gpd

import config


class HealthcareDesertDetector:
    """
    Detects healthcare deserts and calculates desert severity index based on
    multi-criteria spatial and capacity thresholds.
    """

    def __init__(self, criteria: Dict[str, float] = None):
        self.criteria = criteria or config.DESERT_CRITERIA.copy()

    def detect_deserts(self, wards_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Evaluates each ward against desert criteria and computes Healthcare_Desert (bool),
        Healthcare_Desert_Severity (0-100), and Affected_Population.
        """
        gdf = wards_gdf.copy()

        # Criteria thresholds
        min_gap = self.criteria.get("min_gap_score", 60.0)
        min_hosp_dist = self.criteria.get("min_distance_to_hospital_km", 3.5)
        max_beds = self.criteria.get("max_beds_per_1000", 1.0)

        # Condition 1: Elevated Gap Score
        cond_gap = gdf["Gap_Score"] >= min_gap

        # Condition 2: Poor access to hospital/emergency care
        cond_dist = gdf["Nearest_Hospital_Distance"] >= min_hosp_dist

        # Condition 3: Extreme bed deficit
        cond_beds = gdf["Beds_per_1000"] <= max_beds

        # Condition 4: Limited or zero primary facilities
        cond_fac = gdf["Healthcare_Facilities"] <= 1

        # A ward is classified as a Healthcare Desert if:
        # High Gap AND (Far from hospital OR (low beds AND sparse facilities))
        is_desert = cond_gap & (cond_dist | (cond_beds & cond_fac))
        gdf["Healthcare_Desert"] = is_desert

        # Compute Desert Severity (0 to 100)
        # Severity considers gap score, extra distance beyond threshold, and population size
        dist_factor = (gdf["Nearest_Hospital_Distance"] / max(min_hosp_dist, 1.0)).clip(1.0, 3.0) / 3.0
        bed_factor = (1.0 - (gdf["Beds_per_1000"] / max(config.BENCHMARKS["beds_per_1000_who"], 1.0))).clip(0.0, 1.0)
        gap_factor = (gdf["Gap_Score"] / 100.0).clip(0.0, 1.0)

        raw_severity = (0.45 * gap_factor + 0.35 * dist_factor + 0.20 * bed_factor) * 100.0
        gdf["Healthcare_Desert_Severity"] = np.where(is_desert, raw_severity.round(1), 0.0)

        # Affected population in desert wards
        gdf["Desert_Affected_Population"] = np.where(is_desert, gdf["Population"], 0)

        return gdf

    def summarize_deserts(self, gdf: gpd.GeoDataFrame) -> Dict[str, Any]:
        """Returns aggregate statistics on healthcare deserts across the city."""
        desert_wards = gdf[gdf["Healthcare_Desert"]]
        total_deserts = len(desert_wards)
        total_pop = gdf["Population"].sum()
        affected_pop = desert_wards["Population"].sum()
        pct_pop_affected = (affected_pop / max(total_pop, 1)) * 100.0

        top_deserts = desert_wards.sort_values("Healthcare_Desert_Severity", ascending=False)[
            ["Ward_ID", "Ward_Name", "Zone", "Gap_Score", "Healthcare_Desert_Severity", "Population"]
        ].head(10).to_dict(orient="records")

        return {
            "total_desert_wards": total_deserts,
            "percentage_desert_wards": round((total_deserts / max(len(gdf), 1)) * 100.0, 1),
            "total_affected_population": int(affected_pop),
            "percentage_population_affected": round(pct_pop_affected, 1),
            "mean_severity": round(desert_wards["Healthcare_Desert_Severity"].mean(), 1) if total_deserts > 0 else 0.0,
            "top_desert_wards": top_deserts,
        }
