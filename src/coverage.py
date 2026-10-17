"""
CRADLE Population Coverage Module
Calculates multi-tier catchment coverage (2 km, 3 km, 5 km) around facilities or candidate sites,
evaluating aggregate population served, percentage coverage, and ward reach.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

import config
from src.spatial_analysis import SpatialAnalyzer


class PopulationCoverageAnalyzer:
    """
    Computes multi-radius spatial catchment coverage and area-weighted population
    aggregation for existing facilities, candidate locations, and scenario configurations.
    """

    def __init__(self, radii_km: List[float] = None):
        self.radii_km = radii_km or config.COVERAGE_RADII_KM
        self.spatial = SpatialAnalyzer()

    def evaluate_multi_radius_coverage(
        self,
        candidate_or_point: Point,
        wards_gdf: gpd.GeoDataFrame,
    ) -> Dict[str, Any]:
        """
        Evaluates population coverage across 2km, 3km, and 5km concentric buffers
        for a single candidate point.
        """
        results = {}
        total_city_pop = wards_gdf["Population"].sum()

        for r_km in self.radii_km:
            r_meters = r_km * 1000.0
            # Buffer around point
            pt_gdf = gpd.GeoDataFrame(geometry=[candidate_or_point], crs=config.CRS_GEO)
            buf_gdf = self.spatial.create_buffers(pt_gdf, radius_meters=r_meters)
            buf_geom = buf_gdf.geometry.iloc[0]

            cov = self.spatial.compute_buffer_coverage(buf_geom, wards_gdf)
            pop_cov = cov["population_covered"]
            pct_cov = round((pop_cov / max(total_city_pop, 1)) * 100.0, 2)

            results[f"{int(r_km)}km"] = {
                "radius_km": r_km,
                "population_covered": pop_cov,
                "percentage_city_covered": pct_cov,
                "wards_reached_count": cov["ward_count"],
                "high_gap_wards_covered": cov["high_gap_wards_covered"],
                "wards_reached": cov["wards_reached"],
                "coverage_details": cov["coverage_details"],
            }

        return results

    def evaluate_systemwide_coverage(
        self,
        facilities_gdf: gpd.GeoDataFrame,
        wards_gdf: gpd.GeoDataFrame,
        radius_km: float = 3.0,
    ) -> Dict[str, Any]:
        """
        Evaluates cumulative systemwide healthcare coverage across all facilities
        by dissolving catchment buffers.
        """
        if len(facilities_gdf) == 0:
            return {
                "total_population_covered": 0,
                "percentage_covered": 0.0,
                "underserved_population": int(wards_gdf["Population"].sum()),
            }

        radius_m = radius_km * 1000.0
        buffers = self.spatial.create_buffers(facilities_gdf, radius_meters=radius_m)
        dissolved_buffer = buffers.geometry.unary_union

        cov = self.spatial.compute_buffer_coverage(dissolved_buffer, wards_gdf)
        total_pop = int(wards_gdf["Population"].sum())
        pop_covered = cov["population_covered"]
        pct_covered = round((pop_covered / max(total_pop, 1)) * 100.0, 2)
        underserved_pop = max(0, total_pop - pop_covered)

        return {
            "radius_km": radius_km,
            "total_population_covered": pop_covered,
            "percentage_covered": pct_covered,
            "underserved_population": underserved_pop,
            "wards_reached_count": cov["ward_count"],
            "wards_reached": cov["wards_reached"],
        }
