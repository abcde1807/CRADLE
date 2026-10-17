"""
CRADLE Healthcare Gap Analyzer Module
Calculates the 4-indicator Healthcare Gap Score (0-100), assigns priority categories,
and generates transparent natural-language explainability summaries for every ward.
"""

from typing import Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
import geopandas as gpd

import config


class HealthcareGapAnalyzer:
    """
    Computes ward-level healthcare resource gaps using a multi-criteria gap-first approach:
    Gap Score = (0.30 * Pop_Pressure + 0.30 * Capacity_Deficit + 0.25 * Distance_Gap + 0.15 * Facility_Scarcity) * 100
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or config.DEFAULT_GAP_WEIGHTS.copy()
        self._validate_weights(self.weights)

    def _validate_weights(self, weights: Dict[str, float]):
        """Ensures weights sum to 1.0 (with slight floating tolerance)."""
        total = sum(weights.values())
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"Gap weights must sum to 1.0, got {total}")

    def update_weights(self, new_weights: Dict[str, float]):
        """Dynamically updates component weights."""
        self._validate_weights(new_weights)
        self.weights = new_weights.copy()

    def calculate_gap_scores(self, wards_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Calculates normalized components (0 to 1) and composite Gap Score (0 to 100).
        Also generates natural-language explainability diagnosis for each ward.
        """
        gdf = wards_gdf.copy()

        # Handle edge cases: missing columns or zero values
        for col in ["Population", "Population_Density", "Hospital_Beds", "Beds_per_1000", "Healthcare_Facilities"]:
            if col not in gdf.columns:
                gdf[col] = 0

        # 1. Population Pressure (0 to 1)
        # Combines population density percentile and vulnerable population ratio
        density_p95 = gdf["Population_Density"].quantile(0.95) or 1.0
        norm_density = (gdf["Population_Density"] / max(density_p95, 1.0)).clip(0.0, 1.0)

        # Vulnerable population ratio (Elderly + Children) / Population
        if "Elderly" in gdf.columns and "Children" in gdf.columns:
            vuln_ratio = ((gdf["Elderly"] + gdf["Children"]) / gdf["Population"].replace(0, 1)).clip(0.0, 1.0)
            pop_pressure = (0.7 * norm_density + 0.3 * vuln_ratio).clip(0.0, 1.0)
        else:
            pop_pressure = norm_density

        # 2. Capacity Deficit (0 to 1)
        # Inverse of beds per 1,000 compared to WHO target (3.0 beds per 1,000)
        who_target = config.BENCHMARKS["beds_per_1000_who"]
        capacity_deficit = (1.0 - (gdf["Beds_per_1000"] / who_target)).clip(0.0, 1.0)

        # 3. Distance Gap (0 to 1)
        # Distance to nearest facility (weight 0.4) and nearest hospital (weight 0.6)
        if "Nearest_Facility_Distance" in gdf.columns and "Nearest_Hospital_Distance" in gdf.columns:
            norm_fac_dist = (gdf["Nearest_Facility_Distance"] / config.BENCHMARKS["target_facility_distance_km"]).clip(0.0, 1.0)
            norm_hosp_dist = (gdf["Nearest_Hospital_Distance"] / config.BENCHMARKS["hospital_distance_km"]).clip(0.0, 1.0)
            distance_gap = (0.4 * norm_fac_dist + 0.6 * norm_hosp_dist).clip(0.0, 1.0)
        elif "Nearest_Facility_Distance" in gdf.columns:
            distance_gap = (gdf["Nearest_Facility_Distance"] / config.BENCHMARKS["target_facility_distance_km"]).clip(0.0, 1.0)
        else:
            distance_gap = pd.Series(0.5, index=gdf.index)

        # 4. Facility Scarcity (0 to 1)
        # Inverse of facilities per 10,000 population, benchmark: 1 facility per 10,000
        fac_per_10k = (gdf["Healthcare_Facilities"] / gdf["Population"].replace(0, 1)) * 10000
        facility_scarcity = (1.0 - (fac_per_10k / 1.5)).clip(0.0, 1.0)

        # Store normalized indicators (scale 0-100 for display and explainability)
        gdf["Pop_Pressure_Norm"] = (pop_pressure * 100).round(1)
        gdf["Capacity_Deficit_Norm"] = (capacity_deficit * 100).round(1)
        gdf["Distance_Gap_Norm"] = (distance_gap * 100).round(1)
        gdf["Facility_Scarcity_Norm"] = (facility_scarcity * 100).round(1)

        # Composite Gap Score (0-100)
        composite_score = (
            self.weights["population_pressure"] * pop_pressure
            + self.weights["capacity_deficit"] * capacity_deficit
            + self.weights["distance_gap"] * distance_gap
            + self.weights["facility_scarcity"] * facility_scarcity
        ) * 100.0

        gdf["Gap_Score"] = composite_score.round(1).clip(0.0, 100.0)

        # Assign Priority Categories
        gdf["Priority_Category"] = gdf["Gap_Score"].apply(self.classify_priority)

        # Generate Explainability diagnosis
        gdf["Primary_Issue"] = [
            self._diagnose_primary_issue(row) for _, row in gdf.iterrows()
        ]
        gdf["Explainability_Text"] = [
            self._generate_explanation(row) for _, row in gdf.iterrows()
        ]

        # Rank wards by Gap Score descending
        gdf["Gap_Rank"] = gdf["Gap_Score"].rank(ascending=False, method="min").astype(int)

        return gdf

    @staticmethod
    def classify_priority(score: float) -> str:
        """Classifies Gap Score into standard planning priority categories."""
        if score >= 70.0:
            return "Critical"
        elif score >= 50.0:
            return "High"
        elif score >= 25.0:
            return "Moderate"
        else:
            return "Low"

    @staticmethod
    def _diagnose_primary_issue(row: pd.Series) -> str:
        """Identifies the dominant contributing factor to the gap score."""
        components = {
            "Population Pressure": row.get("Pop_Pressure_Norm", 0),
            "Capacity Deficit": row.get("Capacity_Deficit_Norm", 0),
            "Distance Gap": row.get("Distance_Gap_Norm", 0),
            "Facility Scarcity": row.get("Facility_Scarcity_Norm", 0),
        }
        primary = max(components, key=components.get)
        max_val = components[primary]

        if max_val < 30.0:
            return "Well-served: Adequate healthcare infrastructure and accessible services."

        if primary == "Capacity Deficit":
            return "Severe shortage of hospital beds and secondary clinical capacity relative to population."
        elif primary == "Population Pressure":
            return "Extreme population density and demographic demand overburdening local facilities."
        elif primary == "Distance Gap":
            return "Spatial isolation with excessive travel distance to nearest hospital/emergency care."
        elif primary == "Facility Scarcity":
            return "Acute lack of primary and urban community healthcare centres."
        return "Complex multi-factor healthcare gap."

    @staticmethod
    def _generate_explanation(row: pd.Series) -> str:
        """Generates comprehensive natural-language explanation for dashboard explainability panel."""
        ward_id = row.get("Ward_ID", "N/A")
        ward_name = row.get("Ward_Name", f"Ward {ward_id}")
        zone = row.get("Zone", "N/A")
        gap_score = row.get("Gap_Score", 0)
        priority = row.get("Priority_Category", "Low")
        pop = row.get("Population", 0)
        beds = row.get("Hospital_Beds", 0)
        beds_k = row.get("Beds_per_1000", 0)
        dist_fac = row.get("Nearest_Facility_Distance", 0)
        dist_hosp = row.get("Nearest_Hospital_Distance", 0)

        pp = row.get("Pop_Pressure_Norm", 0)
        cd = row.get("Capacity_Deficit_Norm", 0)
        dg = row.get("Distance_Gap_Norm", 0)
        fs = row.get("Facility_Scarcity_Norm", 0)

        lines = [
            f"**{ward_name} ({zone})** has a Healthcare Gap Score of **{gap_score:.1f}/100** ({priority} Priority).",
            f"- **Demographics**: Population of {pop:,} with density {row.get('Population_Density', 0):,.0f} persons/km².",
            f"- **Infrastructure**: {row.get('Healthcare_Facilities', 0)} total facilities, {beds:,} total beds ({beds_k:.2f} beds per 1,000 vs WHO target 3.0).",
            f"- **Accessibility**: Nearest facility is {dist_fac:.1f} km away; nearest secondary/tertiary hospital is {dist_hosp:.1f} km away.",
            "",
            "**Key Indicator Breakdown (0-100 scale):**",
            f"- Population Pressure: {pp:.0f}/100",
            f"- Capacity Deficit: {cd:.0f}/100",
            f"- Distance Gap: {dg:.0f}/100",
            f"- Facility Scarcity: {fs:.0f}/100",
            "",
            f"**Primary Diagnostic:** {row.get('Primary_Issue', '')}",
        ]
        return "\n".join(lines)
