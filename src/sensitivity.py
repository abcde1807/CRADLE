"""
CRADLE Sensitivity Analysis Module
Evaluates candidate ranking stability and rank shifts across varying multi-criteria weighting profiles
(Balanced, Population-Focused, Capacity-Focused, Accessibility-Focused).
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import geopandas as gpd
from scipy.stats import spearmanr

import config
from src.candidate_ranking import CandidateRanker


class SensitivityAnalyzer:
    """
    Simulates alternative weight regimes and analyzes candidate ranking stability
    to identify robust vs sensitive site recommendations.
    """

    def __init__(self, profiles: Optional[Dict[str, Dict[str, float]]] = None):
        self.profiles = profiles or config.SENSITIVITY_PROFILES.copy()
        self.ranker = CandidateRanker()

    def run_sensitivity_analysis(
        self,
        candidates_gdf: gpd.GeoDataFrame,
        wards_gdf: gpd.GeoDataFrame,
        facilities_gdf: gpd.GeoDataFrame,
    ) -> Dict[str, Any]:
        """
        Executes candidate ranking across all sensitivity profiles.
        Returns:
            Dict containing:
                - `rankings_df`: DataFrame of candidate ranks across scenarios
                - `correlation_matrix`: Spearman correlation between profiles
                - `mean_rank_shifts`: Average rank movement per scenario
                - `top_10_stability`: Stability of top 10 candidates
        """
        if len(candidates_gdf) == 0:
            return {}

        results = {}
        top_candidates_per_profile = {}

        for profile_name, weights in self.profiles.items():
            self.ranker.update_weights(weights)
            ranked_gdf = self.ranker.rank_candidates(
                candidates_gdf, wards_gdf, facilities_gdf
            )
            # Store ranks indexed by Candidate_ID
            rank_map = ranked_gdf.set_index("Candidate_ID")["Rank"]
            score_map = ranked_gdf.set_index("Candidate_ID")["Candidate_Score"]
            results[f"{profile_name} Rank"] = rank_map
            results[f"{profile_name} Score"] = score_map
            top_candidates_per_profile[profile_name] = ranked_gdf["Candidate_ID"].head(10).tolist()

        rankings_df = pd.DataFrame(results)
        rankings_df["Ward_ID"] = candidates_gdf.set_index("Candidate_ID")["Ward_ID"]
        rankings_df["Ward_Name"] = candidates_gdf.set_index("Candidate_ID")["Ward_Name"]
        rankings_df["Zone"] = candidates_gdf.set_index("Candidate_ID")["Zone"]

        # Calculate rank variance and standard deviation across profiles
        rank_cols = [c for c in rankings_df.columns if "Rank" in c]
        rankings_df["Rank_StdDev"] = rankings_df[rank_cols].std(axis=1).round(2)
        rankings_df["Rank_Range"] = (rankings_df[rank_cols].max(axis=1) - rankings_df[rank_cols].min(axis=1)).astype(int)

        # Baseline comparison
        baseline_col = "Balanced (Baseline) Rank"
        if baseline_col in rankings_df.columns:
            rankings_df["Baseline_Rank"] = rankings_df[baseline_col]

        # Spearman rank correlations with baseline
        correlations = {}
        for col in rank_cols:
            if col != baseline_col:
                corr, _ = spearmanr(rankings_df[baseline_col], rankings_df[col])
                correlations[col.replace(" Rank", "")] = round(float(corr), 3)

        return {
            "rankings_df": rankings_df.sort_values("Baseline_Rank" if baseline_col in rankings_df.columns else rank_cols[0]),
            "correlations": correlations,
            "top_candidates_per_profile": top_candidates_per_profile,
            "mean_std_dev": round(float(rankings_df["Rank_StdDev"].mean()), 2),
        }
