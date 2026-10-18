"""
CRADLE Candidate Ranking Module
Scores and ranks potential facility locations using a multi-criteria candidate score,
assigning recommendation tiers and evaluating marginal coverage gains.
"""

from typing import Dict, Any, Optional, List
import numpy as np
import pandas as pd
import geopandas as gpd

import config
from src.spatial_analysis import SpatialAnalyzer


class CandidateRanker:
    """
    Ranks candidate locations using multi-factor criteria:
    Candidate Score = (0.40 * Gap_Severity + 0.30 * Pop_Coverage + 0.20 * Fac_Distance + 0.10 * Road_Proximity)
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or config.DEFAULT_CANDIDATE_WEIGHTS.copy()
        self.spatial = SpatialAnalyzer()

    def update_weights(self, new_weights: Dict[str, float]):
        """Updates scoring weights ensuring sum to 1.0."""
        total = sum(new_weights.values())
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"Candidate weights must sum to 1.0, got {total}")
        self.weights = new_weights.copy()

    def rank_candidates(
        self,
        candidates_gdf: gpd.GeoDataFrame,
        wards_gdf: gpd.GeoDataFrame,
        facilities_gdf: gpd.GeoDataFrame,
        coverage_radius_m: float = 3000.0,
    ) -> gpd.GeoDataFrame:
        """
        Computes coverage metrics, normalized component scores, composite Candidate Score,
        and assigns recommendation tiers.
        """
        if len(candidates_gdf) == 0:
            return candidates_gdf.copy()

        gdf = candidates_gdf.copy()

        # Compute buffer coverage (3km default) for each candidate if not already present
        if "Population_Covered" not in gdf.columns or "Wards_Reached" not in gdf.columns:
            # Determine metric CRS
            if "City_Key" in wards_gdf.columns and len(wards_gdf["City_Key"].dropna()) > 0:
                crs_proj = config.get_city_crs(wards_gdf["City_Key"].dropna().iloc[0])
            elif wards_gdf.crs and wards_gdf.crs.is_projected:
                crs_proj = wards_gdf.crs
            else:
                crs_proj = self.spatial.crs_proj

            wards_proj = wards_gdf.to_crs(crs_proj)
            cands_proj = gdf.to_crs(crs_proj)

            buf_geoms = cands_proj.geometry.buffer(coverage_radius_m)
            buf_gdf = gpd.GeoDataFrame({"cand_idx": range(len(gdf))}, geometry=buf_geoms, crs=crs_proj)

            sj = gpd.sjoin(
                buf_gdf,
                wards_proj[["Ward_ID", "Population", "Gap_Score", "geometry"]],
                predicate="intersects"
            )

            if len(sj) > 0:
                high_gap_mask = sj["Gap_Score"] >= 50.0
                sj["is_high_gap"] = high_gap_mask.astype(int)

                agg_stats = sj.groupby("cand_idx").agg(
                    pop_covered=("Population", "sum"),
                    wards_reached=("Ward_ID", "nunique"),
                    high_gap_count=("is_high_gap", "sum"),
                )

                gdf["Population_Covered"] = [
                    int(round(agg_stats.loc[i, "pop_covered"] * 0.65)) if i in agg_stats.index else 0
                    for i in range(len(gdf))
                ]
                gdf["Wards_Reached"] = [
                    int(agg_stats.loc[i, "wards_reached"]) if i in agg_stats.index else 0
                    for i in range(len(gdf))
                ]
                gdf["High_Gap_Wards_Covered"] = [
                    int(agg_stats.loc[i, "high_gap_count"]) if i in agg_stats.index else 0
                    for i in range(len(gdf))
                ]
            else:
                gdf["Population_Covered"] = 0
                gdf["Wards_Reached"] = 0
                gdf["High_Gap_Wards_Covered"] = 0

        # Distance to existing facilities (meters / km) if not already present
        if "Facility_Distance_km" not in gdf.columns:
            dist_matrix = self.spatial.compute_distance_matrix(gdf, facilities_gdf)
            if dist_matrix.shape[1] > 0:
                min_fac_dist_km = dist_matrix.min(axis=1) / 1000.0
            else:
                min_fac_dist_km = np.full(len(gdf), 5.0)

            gdf["Facility_Distance_km"] = np.round(min_fac_dist_km, 2)

        # 1. Gap Severity component (0 to 100)
        gap_severity = gdf["Gap_Score"].clip(0.0, 100.0)

        # 2. Population Coverage component (0 to 100)
        max_cov = gdf["Population_Covered"].quantile(0.95) or 1.0
        pop_coverage_score = (gdf["Population_Covered"] / max(max_cov, 1.0)).clip(0.0, 1.0) * 100.0

        # 3. Existing Facility Distance component (0 to 100)
        # Candidates further from existing facilities score higher (filling spatial voids)
        target_dist_km = config.BENCHMARKS["hospital_distance_km"]
        fac_dist_score = (gdf["Facility_Distance_km"] / target_dist_km).clip(0.0, 1.0) * 100.0

        # 4. Road Proximity component (0 to 100)
        # Proxied by ward density & accessibility index
        density_norm = (wards_gdf.set_index("Ward_ID").loc[gdf["Ward_ID"]]["Population_Density"].values / 25000.0).clip(0.0, 1.0)
        road_prox_score = density_norm * 100.0

        # Store sub-scores
        gdf["Score_Gap_Severity"] = gap_severity.round(1)
        gdf["Score_Pop_Coverage"] = pop_coverage_score.round(1)
        gdf["Score_Fac_Distance"] = fac_dist_score.round(1)
        gdf["Score_Road_Proximity"] = np.round(road_prox_score, 1)

        # Composite Candidate Score (0 to 100)
        composite = (
            self.weights["gap_severity"] * gap_severity
            + self.weights["population_coverage"] * pop_coverage_score
            + self.weights["facility_distance"] * fac_dist_score
            + self.weights["road_proximity"] * road_prox_score
        )

        gdf["Candidate_Score"] = composite.round(1).clip(0.0, 100.0)

        # Coverage Gain estimate (percentage of ward population newly directly accessible within 2km)
        gdf["Coverage_Gain"] = (gdf["Population_Covered"] * 0.45).round().astype(int)

        # Recommendation Category
        gdf["Recommendation"] = gdf["Candidate_Score"].apply(self.classify_recommendation)

        # Rank candidates descending
        gdf["Rank"] = gdf["Candidate_Score"].rank(ascending=False, method="min").astype(int)
        gdf = gdf.sort_values("Rank").reset_index(drop=True)

        return gdf

    @staticmethod
    def classify_recommendation(score: float) -> str:
        """Maps candidate score to policy recommendation tiers."""
        if score >= 75.0:
            return "Highly Recommended"
        elif score >= 60.0:
            return "Recommended"
        elif score >= 45.0:
            return "Moderate"
        else:
            return "Low Priority"
