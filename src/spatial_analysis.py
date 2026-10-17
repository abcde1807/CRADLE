"""
CRADLE Spatial Analysis Module
Provides spatial computations: distance matrices, meter-accurate geodesic/projected buffers,
spatial intersections, and centroid-based proximity metrics.
"""

from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon, MultiPolygon
from scipy.spatial.distance import cdist

import config


class SpatialAnalyzer:
    """
    Spatial utility class for meter-projected buffering, distance matrix computation,
    and area-weighted population spatial intersections.
    """

    def __init__(self, crs_geo: str = config.CRS_GEO, crs_proj: str = config.CRS_PROJ):
        self.crs_geo = crs_geo
        self.crs_proj = crs_proj

    def compute_distance_matrix(
        self,
        origins: gpd.GeoDataFrame,
        destinations: gpd.GeoDataFrame,
    ) -> np.ndarray:
        """
        Computes pairwise Euclidean distance matrix in meters between origins and destinations.
        """
        orig_proj = origins.to_crs(self.crs_proj)
        dest_proj = destinations.to_crs(self.crs_proj)

        orig_coords = np.array([(geom.centroid.x, geom.centroid.y) for geom in orig_proj.geometry])
        dest_coords = np.array([(geom.centroid.x, geom.centroid.y) for geom in dest_proj.geometry])

        if len(orig_coords) == 0 or len(dest_coords) == 0:
            return np.zeros((len(orig_coords), len(dest_coords)))

        return cdist(orig_coords, dest_coords, metric="euclidean")

    def create_buffers(
        self,
        points: gpd.GeoDataFrame,
        radius_meters: float,
    ) -> gpd.GeoDataFrame:
        """
        Creates circular buffer polygons of specified radius around point geometries
        using projected UTM CRS, and reprojects back to geographic CRS.
        """
        pts_proj = points.to_crs(self.crs_proj)
        buffers_proj = pts_proj.copy()
        buffers_proj["geometry"] = pts_proj.geometry.buffer(radius_meters)
        buffers_geo = buffers_proj.to_crs(self.crs_geo)
        return buffers_geo

    def compute_buffer_coverage(
        self,
        buffer_geom: Polygon,
        wards_gdf: gpd.GeoDataFrame,
    ) -> Dict[str, Any]:
        """
        Calculates area-weighted population coverage for a given buffer polygon intersecting wards.
        
        Args:
            buffer_geom: Buffer polygon in geographic CRS (EPSG:4326)
            wards_gdf: Wards GeoDataFrame with Population and Area_km2
            
        Returns:
            Dict containing:
                - population_covered: estimated total population covered
                - wards_reached: list of Ward_IDs intersected
                - ward_count: count of distinct wards touched
                - high_gap_wards_covered: count of high/critical gap wards reached
        """
        # Convert to projected CRS for accurate area intersection
        buffer_gdf = gpd.GeoDataFrame(geometry=[buffer_geom], crs=self.crs_geo).to_crs(self.crs_proj)
        wards_proj = wards_gdf if str(wards_gdf.crs) == str(self.crs_proj) else wards_gdf.to_crs(self.crs_proj)

        buffer_poly = buffer_gdf.geometry.iloc[0]

        # Spatial query: find candidate intersecting wards
        intersecting_indices = wards_proj.sindex.query(buffer_poly, predicate="intersects")
        if len(intersecting_indices) == 0:
            return {
                "population_covered": 0,
                "wards_reached": [],
                "ward_count": 0,
                "high_gap_wards_covered": 0,
                "coverage_details": [],
            }

        candidate_wards = wards_proj.iloc[intersecting_indices].copy()

        total_pop_covered = 0.0
        wards_reached = []
        high_gap_count = 0
        coverage_details = []

        for _, ward in candidate_wards.iterrows():
            intersection = ward.geometry.intersection(buffer_poly)
            if not intersection.is_empty and intersection.area > 0:
                area_fraction = min(1.0, intersection.area / max(1.0, ward.geometry.area))
                ward_pop = ward.get("Population", 0)
                pop_in_buffer = int(round(ward_pop * area_fraction))
                total_pop_covered += pop_in_buffer

                ward_id = int(ward["Ward_ID"])
                wards_reached.append(ward_id)

                gap_score = ward.get("Gap_Score", 0)
                if gap_score >= 50.0:
                    high_gap_count += 1

                coverage_details.append({
                    "Ward_ID": ward_id,
                    "Ward_Name": ward.get("Ward_Name", f"Ward {ward_id}"),
                    "Area_Fraction": round(area_fraction, 4),
                    "Pop_Covered": pop_in_buffer,
                    "Gap_Score": round(gap_score, 1),
                })

        return {
            "population_covered": int(round(total_pop_covered)),
            "wards_reached": sorted(wards_reached),
            "ward_count": len(wards_reached),
            "high_gap_wards_covered": high_gap_count,
            "coverage_details": coverage_details,
        }

    def find_nearest_facilities(
        self,
        point_geom: Point,
        facilities_gdf: gpd.GeoDataFrame,
        k: int = 3,
    ) -> gpd.GeoDataFrame:
        """
        Returns the k nearest facilities to a given point geometry.
        """
        pt_proj = gpd.GeoDataFrame(geometry=[point_geom], crs=self.crs_geo).to_crs(self.crs_proj).geometry.iloc[0]
        fac_proj = facilities_gdf.to_crs(self.crs_proj)

        distances = fac_proj.geometry.distance(pt_proj) / 1000.0  # km
        nearest_indices = distances.nsmallest(k).index

        res = facilities_gdf.loc[nearest_indices].copy()
        res["Distance_km"] = distances.loc[nearest_indices].round(2)
        return res
