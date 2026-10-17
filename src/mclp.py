"""
CRADLE Maximal Covering Location Problem (MCLP) Module
Solves binary integer linear programming optimization for multi-facility healthcare siting
under facility count, budget, and coverage radius constraints using PuLP.
"""

from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from scipy.spatial.distance import cdist
import pulp

import config


class MCLPOptimizer:
    """
    Maximal Covering Location Problem (MCLP) Optimizer with Gap-Weighted Demand:
    Selects p candidate locations to maximize gap-weighted population coverage
    within service radius R subject to budget and facility count constraints.
    """

    def __init__(self):
        pass

    def solve_mclp(
        self,
        candidates_gdf: gpd.GeoDataFrame,
        wards_gdf: gpd.GeoDataFrame,
        num_facilities: int = 5,
        coverage_radius_km: float = 3.0,
        budget_crores: Optional[float] = None,
        cost_per_facility_cr: float = 8.0,
        use_gap_weighting: bool = True,
    ) -> Dict[str, Any]:
        """
        Solves the MCLP integer program using PuLP.
        """
        if len(candidates_gdf) == 0:
            return {"status": "Error", "message": "No candidate locations provided."}

        num_facilities = min(num_facilities, len(candidates_gdf))

        # Project coordinates to metric UTM
        cand_utm = candidates_gdf.to_crs(config.CRS_PROJ)
        wards_utm = wards_gdf.to_crs(config.CRS_PROJ)

        cand_coords = np.array([(g.x, g.y) for g in cand_utm.geometry])
        ward_coords = np.array([(g.centroid.x, g.centroid.y) for g in wards_utm.geometry])

        # Distance matrix in km
        dist_matrix_km = cdist(ward_coords, cand_coords, metric="euclidean") / 1000.0

        num_wards = len(wards_gdf)
        num_cands = len(candidates_gdf)

        # Coverage adjacency matrix: A_ij = 1 if cand j covers ward i
        coverage_matrix = (dist_matrix_km <= coverage_radius_km).astype(int)

        # Demand weights: Gap-First weighting
        # w_i = Population * (Gap_Score / 100) if use_gap_weighting else Population
        pop_arr = wards_gdf["Population"].values.astype(float)
        gap_arr = wards_gdf["Gap_Score"].values.astype(float) / 100.0

        if use_gap_weighting:
            demand_weights = pop_arr * np.maximum(gap_arr, 0.1)
        else:
            demand_weights = pop_arr

        # Formulate PuLP Integer Linear Program
        prob = pulp.LpProblem("CRADLE_MCLP_Optimization", pulp.LpMaximize)

        # Decision variables
        # x_j: 1 if candidate j is selected
        x = [pulp.LpVariable(f"x_{j}", cat=pulp.LpBinary) for j in range(num_cands)]

        # y_i: 1 if ward i is covered
        y = [pulp.LpVariable(f"y_{i}", cat=pulp.LpBinary) for i in range(num_wards)]

        # Objective: Maximize total covered gap-weighted demand
        prob += pulp.lpSum([demand_weights[i] * y[i] for i in range(num_wards)])

        # Constraint 1: Ward coverage coupling: sum_{j} A_ij * x_j >= y_i
        for i in range(num_wards):
            covering_cands = [x[j] for j in range(num_cands) if coverage_matrix[i, j] == 1]
            if len(covering_cands) > 0:
                prob += pulp.lpSum(covering_cands) >= y[i]
            else:
                prob += y[i] == 0

        # Constraint 2: Number of facilities: sum_j x_j <= num_facilities
        prob += pulp.lpSum(x) == num_facilities

        # Constraint 3: Optional Budget constraint
        if budget_crores is not None and budget_crores > 0:
            max_fac_by_budget = int(budget_crores // cost_per_facility_cr)
            if max_fac_by_budget < num_facilities:
                prob += pulp.lpSum([cost_per_facility_cr * x[j] for j in range(num_cands)]) <= budget_crores

        # Solve ILP quietly
        solver = pulp.PULP_CBC_CMD(msg=False)
        solver_status = prob.solve(solver)

        if pulp.LpStatus[solver_status] != "Optimal":
            # Fallback heuristic: greedy selection by marginal demand coverage
            return self._solve_greedy_fallback(
                candidates_gdf, wards_gdf, num_facilities, coverage_radius_km, demand_weights, coverage_matrix
            )

        # Extract selected candidates
        selected_cand_indices = [j for j in range(num_cands) if pulp.value(x[j]) > 0.5]
        covered_ward_indices = [i for i in range(num_wards) if pulp.value(y[i]) > 0.5]

        selected_candidates_gdf = candidates_gdf.iloc[selected_cand_indices].copy()
        selected_candidates_gdf["MCLP_Rank"] = range(1, len(selected_candidates_gdf) + 1)

        total_city_pop = int(wards_gdf["Population"].sum())
        total_pop_covered = int(wards_gdf.iloc[covered_ward_indices]["Population"].sum())
        pct_covered = round((total_pop_covered / max(total_city_pop, 1)) * 100.0, 2)
        total_cost = len(selected_candidates_gdf) * cost_per_facility_cr

        high_gap_wards_covered = int((wards_gdf.iloc[covered_ward_indices]["Gap_Score"] >= 50.0).sum())

        return {
            "status": "Optimal",
            "num_facilities_selected": len(selected_candidates_gdf),
            "selected_candidate_ids": selected_candidates_gdf["Candidate_ID"].tolist(),
            "selected_candidates_gdf": selected_candidates_gdf,
            "total_population_covered": total_pop_covered,
            "percentage_population_covered": pct_covered,
            "remaining_underserved_population": total_city_pop - total_pop_covered,
            "covered_wards_count": len(covered_ward_indices),
            "high_gap_wards_covered": high_gap_wards_covered,
            "total_capital_cost_crores": total_cost,
            "coverage_radius_km": coverage_radius_km,
        }

    def _solve_greedy_fallback(
        self,
        candidates_gdf: gpd.GeoDataFrame,
        wards_gdf: gpd.GeoDataFrame,
        num_facilities: int,
        coverage_radius_km: float,
        demand_weights: np.ndarray,
        coverage_matrix: np.ndarray,
    ) -> Dict[str, Any]:
        """Greedy heuristic fallback if CBC solver encounters an issue."""
        num_cands = len(candidates_gdf)
        num_wards = len(wards_gdf)

        selected = []
        covered_wards = set()

        for _ in range(num_facilities):
            best_cand = None
            best_gain = -1.0
            best_new_covered = set()

            for j in range(num_cands):
                if j in selected:
                    continue
                new_wards = {i for i in range(num_wards) if coverage_matrix[i, j] == 1 and i not in covered_wards}
                gain = sum(demand_weights[i] for i in new_wards)

                if gain > best_gain:
                    best_gain = gain
                    best_cand = j
                    best_new_covered = new_wards

            if best_cand is not None and best_gain > 0:
                selected.append(best_cand)
                covered_wards.update(best_new_covered)
            else:
                # Fill remaining with top ranked candidates
                for j in range(num_cands):
                    if j not in selected:
                        selected.append(j)
                        break

        selected_gdf = candidates_gdf.iloc[selected].copy()
        selected_gdf["MCLP_Rank"] = range(1, len(selected_gdf) + 1)

        total_city_pop = int(wards_gdf["Population"].sum())
        total_pop_covered = int(wards_gdf.iloc[list(covered_wards)]["Population"].sum()) if covered_wards else 0

        return {
            "status": "Greedy_Heuristic",
            "num_facilities_selected": len(selected_gdf),
            "selected_candidate_ids": selected_gdf["Candidate_ID"].tolist(),
            "selected_candidates_gdf": selected_gdf,
            "total_population_covered": total_pop_covered,
            "percentage_population_covered": round((total_pop_covered / max(total_city_pop, 1)) * 100.0, 2),
            "remaining_underserved_population": total_city_pop - total_pop_covered,
            "covered_wards_count": len(covered_wards),
            "high_gap_wards_covered": int((wards_gdf.iloc[list(covered_wards)]["Gap_Score"] >= 50.0).sum()) if covered_wards else 0,
            "total_capital_cost_crores": len(selected_gdf) * 8.0,
            "coverage_radius_km": coverage_radius_km,
        }
