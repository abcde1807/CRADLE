"""
CRADLE Candidate Location Generator Module
Generates regular spatial grid candidate sites within high-gap priority wards,
filtering out locations within exclusion buffers of existing facilities.
"""

from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, MultiPoint

import config


class CandidateLocationGenerator:
    """
    Generates 500m x 500m spatial grid points across priority wards,
    clips them to ward polygons, and filters out points near existing facilities.
    """

    def __init__(
        self,
        grid_size_meters: float = config.CANDIDATE_CONFIG["grid_size_meters"],
        buffer_meters: float = config.CANDIDATE_CONFIG["existing_facility_buffer_m"],
        target_priorities: List[str] = None,
    ):
        self.grid_size = grid_size_meters
        self.buffer_meters = buffer_meters
        self.target_priorities = target_priorities or config.CANDIDATE_CONFIG["target_priorities"]

    def generate_candidates(
        self,
        wards_gdf: gpd.GeoDataFrame,
        facilities_gdf: gpd.GeoDataFrame,
    ) -> gpd.GeoDataFrame:
        """
        Generates candidate locations.
        Returns GeoDataFrame with Candidate_ID, Ward_ID, Zone, Gap_Score, Latitude, Longitude, geometry.
        """
        # 1. Filter priority wards
        priority_wards = wards_gdf[wards_gdf["Priority_Category"].isin(self.target_priorities)].copy()
        if len(priority_wards) == 0:
            # Fallback to top 20% highest gap wards if none matched
            threshold = wards_gdf["Gap_Score"].quantile(0.8)
            priority_wards = wards_gdf[wards_gdf["Gap_Score"] >= threshold].copy()

        # Determine metric CRS
        if "City_Key" in wards_gdf.columns and len(wards_gdf["City_Key"].dropna()) > 0:
            crs_proj = config.get_city_crs(wards_gdf["City_Key"].dropna().iloc[0])
        elif wards_gdf.crs and wards_gdf.crs.is_projected:
            crs_proj = wards_gdf.crs
        else:
            crs_proj = config.CRS_PROJ

        # Project priority wards and facilities to metric UTM
        priority_utm = priority_wards.to_crs(crs_proj)
        facilities_utm = facilities_gdf.to_crs(crs_proj)

        # 2. Create exclusion buffer around existing facilities
        buf_series = facilities_utm.geometry.buffer(self.buffer_meters)
        existing_buffer_union = buf_series.union_all() if hasattr(buf_series, "union_all") else buf_series.unary_union

        candidate_points = []
        candidate_meta = []
        counter = 1

        # 3. Generate grid points within each priority ward polygon
        for _, ward in priority_utm.iterrows():
            geom = ward.geometry
            minx, miny, maxx, maxy = geom.bounds

            # Generate grid coordinates
            x_coords = np.arange(minx + self.grid_size / 2, maxx, self.grid_size)
            y_coords = np.arange(miny + self.grid_size / 2, maxy, self.grid_size)

            if len(x_coords) == 0 or len(y_coords) == 0:
                # If ward is very small, use its centroid
                candidate_pts = [geom.centroid]
            else:
                xv, yv = np.meshgrid(x_coords, y_coords)
                grid_pts = [Point(x, y) for x, y in zip(xv.ravel(), yv.ravel())]
                # Filter points strictly within the ward polygon
                candidate_pts = [pt for pt in grid_pts if geom.contains(pt)]

            # 4. Filter out points too close to existing facilities
            for pt in candidate_pts:
                if existing_buffer_union is not None and existing_buffer_union.contains(pt):
                    continue

                cid = f"C{counter:03d}"
                counter += 1
                candidate_points.append(pt)
                candidate_meta.append({
                    "Candidate_ID": cid,
                    "Ward_ID": int(ward["Ward_ID"]) if str(ward["Ward_ID"]).isdigit() else ward["Ward_ID"],
                    "Ward_Name": ward["Ward_Name"],
                    "Zone": ward["Zone"],
                    "Gap_Score": ward["Gap_Score"],
                    "Priority_Category": ward["Priority_Category"],
                    "Composite_ID": ward.get("Composite_ID", f"WARD_{ward['Ward_ID']}"),
                    "City_Key": ward.get("City_Key", "chennai"),
                })

        if len(candidate_points) == 0:
            # Fallback: centroids of top priority wards
            for _, ward in priority_utm.head(10).iterrows():
                cid = f"C{counter:03d}"
                counter += 1
                pt = ward.geometry.centroid
                candidate_points.append(pt)
                candidate_meta.append({
                    "Candidate_ID": cid,
                    "Ward_ID": int(ward["Ward_ID"]) if str(ward["Ward_ID"]).isdigit() else ward["Ward_ID"],
                    "Ward_Name": ward["Ward_Name"],
                    "Zone": ward["Zone"],
                    "Gap_Score": ward["Gap_Score"],
                    "Priority_Category": ward["Priority_Category"],
                    "Composite_ID": ward.get("Composite_ID", f"WARD_{ward['Ward_ID']}"),
                    "City_Key": ward.get("City_Key", "chennai"),
                })

        # Build GeoDataFrame and reproject to Geographic CRS (EPSG:4326)
        candidates_utm_gdf = gpd.GeoDataFrame(candidate_meta, geometry=candidate_points, crs=crs_proj)
        candidates_geo_gdf = candidates_utm_gdf.to_crs(config.CRS_GEO)

        candidates_geo_gdf["Latitude"] = candidates_geo_gdf.geometry.y.round(6)
        candidates_geo_gdf["Longitude"] = candidates_geo_gdf.geometry.x.round(6)

        return candidates_geo_gdf
