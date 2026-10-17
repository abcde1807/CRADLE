"""
CRADLE Adaptive Infrastructure Planning Score (AIPS) Module
Quantifies recommendation robustness by evaluating cross-scenario rank stability
and assigning composite AIPS scores and robustness classifications.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import geopandas as gpd

import config
from src.sensitivity import SensitivityAnalyzer
from src.ahp import AHPSuitabilityModel


class AIPSScorer:
    """
    Computes the Adaptive Infrastructure Planning Score (AIPS):
    Rewards candidates that maintain superior performance across multiple planning priorities,
    penalizing sensitivity to weighting volatility.
    """

    def __init__(self):
        self.sensitivity = SensitivityAnalyzer()
        self.ahp_model = AHPSuitabilityModel()

    def compute_aips(
        self,
        candidates_gdf: gpd.GeoDataFrame,
        wards_gdf: gpd.GeoDataFrame,
        facilities_gdf: gpd.GeoDataFrame,
    ) -> pd.DataFrame:
        """
        Calculates AIPS Score (0-100) and Robustness Category for all candidate sites.
        """
        if len(candidates_gdf) == 0:
            return pd.DataFrame()

        # 1. Run Sensitivity Analysis across 4 core weighting profiles
        sens_results = self.sensitivity.run_sensitivity_analysis(candidates_gdf, wards_gdf, facilities_gdf)
        rankings_df = sens_results["rankings_df"].copy()

        # 2. Add AHP Suitability Rank
        ahp_cands = self.ahp_model.evaluate_candidates(candidates_gdf, wards_gdf)
        ahp_rank_map = ahp_cands.set_index("Candidate_ID")["AHP_Suitability_Score"].rank(ascending=False, method="min").astype(int)
        rankings_df["AHP Scenario Rank"] = ahp_rank_map

        # Scenario ranks
        base_rank_col = "Balanced (Baseline) Rank"
        pop_rank_col = "Population-Focused Rank"
        cap_rank_col = "Capacity & Gap-Focused Rank"
        acc_rank_col = "Spatial Accessibility-Focused Rank"
        ahp_rank_col = "AHP Scenario Rank"

        scenario_cols = [base_rank_col, pop_rank_col, cap_rank_col, acc_rank_col, ahp_rank_col]
        valid_scenario_cols = [c for c in scenario_cols if c in rankings_df.columns]

        # Mean Rank & Rank StdDev across all 5 scenarios
        rankings_df["Cross_Scenario_Mean_Rank"] = rankings_df[valid_scenario_cols].mean(axis=1).round(2)
        rankings_df["Cross_Scenario_StdDev"] = rankings_df[valid_scenario_cols].std(axis=1).round(2)

        # Baseline Score (0-100)
        base_score_col = "Balanced (Baseline) Score"
        if base_score_col in rankings_df.columns:
            base_score = rankings_df[base_score_col]
        else:
            base_score = 100.0 - rankings_df[base_rank_col]

        # Robustness penalty: higher std_dev lowers AIPS
        # Penalty factor: exponential decay or normalized ratio
        cv = rankings_df["Cross_Scenario_StdDev"] / np.maximum(rankings_df["Cross_Scenario_Mean_Rank"], 1.0)
        stability_multiplier = np.exp(-0.8 * cv).clip(0.4, 1.0)

        raw_aips = base_score * stability_multiplier
        rankings_df["AIPS"] = raw_aips.round(1).clip(0.0, 100.0)

        # Assign Robustness Categories
        rankings_df["Robustness_Category"] = [
            self._classify_robustness(row["AIPS"], row["Cross_Scenario_StdDev"])
            for _, row in rankings_df.iterrows()
        ]

        # Clean display table
        display_df = rankings_df.reset_index().rename(columns={"index": "Candidate_ID"})
        display_df = display_df.sort_values("AIPS", ascending=False).reset_index(drop=True)
        display_df["AIPS_Rank"] = range(1, len(display_df) + 1)

        return display_df

    @staticmethod
    def _classify_robustness(aips: float, std_dev: float) -> str:
        """Classifies candidate into robustness categories based on score and rank volatility."""
        if aips >= 70.0 and std_dev <= 3.5:
            return "Very Robust"
        elif aips >= 55.0 and std_dev <= 7.0:
            return "Robust"
        elif aips >= 40.0 and std_dev <= 14.0:
            return "Moderately Robust"
        else:
            return "Sensitive"
