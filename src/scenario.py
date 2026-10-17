"""
CRADLE Scenario Simulation Module
Executes Before vs After intervention simulations: models the impact of adding or upgrading
healthcare facilities on ward Gap Scores, desert status, and citywide coverage.
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

import config
from src.spatial_analysis import SpatialAnalyzer
from src.gap_analyzer import HealthcareGapAnalyzer
from src.healthcare_desert import HealthcareDesertDetector


class ScenarioSimulator:
    """
    Simulates counterfactual scenarios by adding hypothetical facilities to the network
    and calculating quantitative Before vs After deltas.
    """

    def __init__(self):
        self.spatial = SpatialAnalyzer()
        self.gap_analyzer = HealthcareGapAnalyzer()
        self.desert_detector = HealthcareDesertDetector()

    def simulate_facility_addition(
        self,
        wards_gdf: gpd.GeoDataFrame,
        facilities_gdf: gpd.GeoDataFrame,
        candidate_location: Point,
        facility_type: str = "CHC",
        beds: int = 50,
        coverage_radius_km: float = 3.0,
        custom_weights: Optional[Dict[str, float]] = None,
    ) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, Dict[str, Any]]:
        """
        Simulates adding a single new facility at candidate_location.
        Returns:
            Tuple: (simulated_wards_gdf, simulated_facilities_gdf, impact_metrics)
        """
        return self.simulate_multi_facility_addition(
            wards_gdf=wards_gdf,
            facilities_gdf=facilities_gdf,
            new_facilities=[{
                "geometry": candidate_location,
                "Facility_Type": facility_type,
                "Beds": beds,
                "Doctors": max(2, beds // 8),
                "Facility_Name": f"Simulated {facility_type}",
            }],
            coverage_radius_km=coverage_radius_km,
            custom_weights=custom_weights,
        )

    def simulate_multi_facility_addition(
        self,
        wards_gdf: gpd.GeoDataFrame,
        facilities_gdf: gpd.GeoDataFrame,
        new_facilities: List[Dict[str, Any]],
        coverage_radius_km: float = 3.0,
        custom_weights: Optional[Dict[str, float]] = None,
    ) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, Dict[str, Any]]:
        """
        Simulates adding multiple new facilities simultaneously.
        """
        # 1. Capture BEFORE metrics
        before_wards = wards_gdf.copy()
        if custom_weights:
            self.gap_analyzer.update_weights(custom_weights)
            before_wards = self.gap_analyzer.calculate_gap_scores(before_wards)
            before_wards = self.desert_detector.detect_deserts(before_wards)

        before_avg_gap = float(before_wards["Gap_Score"].mean())
        before_crit_count = int((before_wards["Priority_Category"] == "Critical").sum())
        before_high_count = int((before_wards["Priority_Category"] == "High").sum())
        before_desert_count = int(before_wards["Healthcare_Desert"].sum())
        before_desert_pop = int(before_wards["Desert_Affected_Population"].sum())

        # 2. Construct simulated facilities GeoDataFrame
        sim_fac_records = []
        next_id_num = len(facilities_gdf) + 1

        for i, nf in enumerate(new_facilities):
            fid = f"SIM_{next_id_num + i:03d}"
            pt = nf["geometry"]
            sim_fac_records.append({
                "Facility_ID": fid,
                "Facility_Name": nf.get("Facility_Name", f"Simulated Facility {i+1}"),
                "Latitude": pt.y,
                "Longitude": pt.x,
                "Facility_Type": nf.get("Facility_Type", "CHC"),
                "Beds": nf.get("Beds", 40),
                "Doctors": nf.get("Doctors", 6),
                "Ownership": "Public",
                "geometry": pt,
            })

        new_fac_gdf = gpd.GeoDataFrame(sim_fac_records, crs=config.CRS_GEO)
        updated_facilities = pd.concat([facilities_gdf, new_fac_gdf], ignore_index=True)
        updated_facilities = gpd.GeoDataFrame(updated_facilities, geometry="geometry", crs=config.CRS_GEO)

        # 3. Recompute ward distance metrics to nearest facility & hospital
        updated_wards = before_wards.copy()
        wards_utm = updated_wards.to_crs(config.CRS_PROJ)
        fac_utm = updated_facilities.to_crs(config.CRS_PROJ)
        ward_centroids = wards_utm.geometry.centroid

        hosp_mask = fac_utm["Facility_Type"].isin([
            "CHC", "Government Hospital", "General Hospital", "Multi-Speciality Hospital"
        ])
        hospitals_utm = fac_utm[hosp_mask]

        new_dist_fac = [round(fac_utm.geometry.distance(c).min() / 1000.0, 2) for c in ward_centroids]
        new_dist_hosp = [round(hospitals_utm.geometry.distance(c).min() / 1000.0, 2) for c in ward_centroids]

        updated_wards["Nearest_Facility_Distance"] = new_dist_fac
        updated_wards["Nearest_Hospital_Distance"] = new_dist_hosp

        # 4. Spatially allocate new facility beds to intersecting / containing ward
        for _, nfac in new_fac_gdf.iterrows():
            pt_geom = nfac.geometry
            # Find ward containing or closest to this point
            contains_mask = updated_wards.geometry.contains(pt_geom)
            if contains_mask.any():
                ward_idx = updated_wards[contains_mask].index[0]
            else:
                ward_idx = updated_wards.geometry.distance(pt_geom).idxmin()

            updated_wards.loc[ward_idx, "Healthcare_Facilities"] += 1
            updated_wards.loc[ward_idx, "Hospital_Beds"] += nfac["Beds"]
            updated_wards.loc[ward_idx, "Total_Doctors"] += nfac["Doctors"]

        # Recalculate beds per 1000
        updated_wards["Beds_per_1000"] = (
            (updated_wards["Hospital_Beds"] / updated_wards["Population"].replace(0, 1)) * 1000
        ).round(2)
        updated_wards["Facilities_per_10k"] = (
            (updated_wards["Healthcare_Facilities"] / updated_wards["Population"].replace(0, 1)) * 10000
        ).round(2)

        # 5. Recompute Gap Scores and Deserts AFTER simulation
        after_wards = self.gap_analyzer.calculate_gap_scores(updated_wards)
        after_wards = self.desert_detector.detect_deserts(after_wards)

        after_avg_gap = float(after_wards["Gap_Score"].mean())
        after_crit_count = int((after_wards["Priority_Category"] == "Critical").sum())
        after_high_count = int((after_wards["Priority_Category"] == "High").sum())
        after_desert_count = int(after_wards["Healthcare_Desert"].sum())
        after_desert_pop = int(after_wards["Desert_Affected_Population"].sum())

        # 6. Calculate coverage of the new facilities
        new_buffers = self.spatial.create_buffers(new_fac_gdf, radius_meters=coverage_radius_km * 1000.0)
        dissolved_new_buf = new_buffers.geometry.union_all() if hasattr(new_buffers.geometry, "union_all") else new_buffers.geometry.unary_union
        cov_info = self.spatial.compute_buffer_coverage(dissolved_new_buf, after_wards)

        # Wards with improved Gap Scores
        gap_delta = before_wards["Gap_Score"] - after_wards["Gap_Score"]
        after_wards["Gap_Reduction"] = gap_delta.round(1)
        improved_wards_mask = gap_delta > 0.5
        improved_wards_count = int(improved_wards_mask.sum())

        max_ward_improvement = {
            "Ward_ID": int(after_wards.loc[gap_delta.idxmax(), "Ward_ID"]),
            "Ward_Name": after_wards.loc[gap_delta.idxmax(), "Ward_Name"],
            "Old_Gap": float(before_wards.loc[gap_delta.idxmax(), "Gap_Score"]),
            "New_Gap": float(after_wards.loc[gap_delta.idxmax(), "Gap_Score"]),
            "Delta": float(gap_delta.max()),
        } if improved_wards_count > 0 else {}

        impact_metrics = {
            "facilities_added": len(new_facilities),
            "total_new_beds": sum(nf.get("Beds", 0) for nf in new_facilities),
            "before_avg_gap": round(before_avg_gap, 2),
            "after_avg_gap": round(after_avg_gap, 2),
            "citywide_gap_reduction": round(before_avg_gap - after_avg_gap, 2),
            "before_critical_wards": before_crit_count,
            "after_critical_wards": after_crit_count,
            "critical_wards_reduced": before_crit_count - after_crit_count,
            "before_high_wards": before_high_count,
            "after_high_wards": after_high_count,
            "before_desert_wards": before_desert_count,
            "after_desert_wards": after_desert_count,
            "desert_wards_resolved": before_desert_count - after_desert_count,
            "desert_pop_alleviated": before_desert_pop - after_desert_pop,
            "improved_wards_count": improved_wards_count,
            "population_newly_served": cov_info["population_covered"],
            "wards_reached_by_catchment": cov_info["ward_count"],
            "max_ward_improvement": max_ward_improvement,
        }

        return after_wards, updated_facilities, impact_metrics
