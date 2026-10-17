"""
CRADLE Multi-City Preprocessing Pipeline
Integrates administrative units, demographics, and healthcare facilities through spatial joins,
city-specific metric CRS transformations (EPSG:32644 / EPSG:32643), and calculation of ward-level indicators.
"""

from pathlib import Path
from typing import Tuple, Dict, Any, Optional
import numpy as np
import pandas as pd
import geopandas as gpd

import config
from src.data_loader import DataLoader


class PreprocessingPipeline:
    """
    Executes end-to-end data cleaning, projection, spatial joining,
    and aggregation of healthcare indicators per administrative unit across cities.
    """

    def __init__(self, data_loader: DataLoader = None):
        self.loader = data_loader or DataLoader()

    def run(self, city_key: str = config.DEFAULT_CITY) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, Dict[str, Any]]:
        """
        Executes the preprocessing pipeline for a specific city:
        1. Loads ward, demographic, and facility datasets.
        2. Merges demographics with ward geometries.
        3. Spatially joins facilities to wards.
        4. Calculates ward-level aggregations: facilities, beds, doctors.
        5. Computes indicators: beds/1,000 pop, facilities/10,000 pop, population density.
        6. Computes metric distance to nearest facility & hospital using city CRS.
        7. Saves processed GeoDataFrames.

        Returns:
            Tuple: (processed_wards_gdf, processed_facilities_gdf, metadata_dict)
        """
        key = (city_key or config.DEFAULT_CITY).lower().strip()
        city_cfg = config.get_city_config(key)
        crs_proj = city_cfg.get("crs_proj", config.CRS_PROJ)

        # 1. Load raw/sample data for this city
        wards_gdf, wards_synth = self.loader.load_wards(key)
        pop_df, pop_synth = self.loader.load_population(key)
        facilities_gdf, fac_synth = self.loader.load_facilities(key)

        is_synthetic = wards_synth or pop_synth or fac_synth

        # 2. Merge demographics into wards GeoDataFrame
        pop_cols = ["Ward_ID"] + [c for c in pop_df.columns if c not in wards_gdf.columns and c != "Area_km2"]
        merged_wards = wards_gdf.merge(pop_df[pop_cols], on="Ward_ID", how="left")

        # Fallback for missing population
        if merged_wards["Population"].isna().any():
            mean_pop = merged_wards["Population"].mean() or 35000
            merged_wards["Population"] = merged_wards["Population"].fillna(mean_pop).astype(int)

        # Ensure accurate area in km2 using city-specific projected UTM
        wards_utm = merged_wards.to_crs(crs_proj)
        merged_wards["Area_km2"] = (wards_utm.geometry.area / 1e6).round(3)
        merged_wards["Population_Density"] = (
            merged_wards["Population"] / merged_wards["Area_km2"].replace(0, 0.001)
        ).round(1)

        # 3. Spatial join facilities to wards
        join_cols = ["Ward_ID", "Zone", "geometry"]
        facilities_with_ward = gpd.sjoin(
            facilities_gdf,
            merged_wards[join_cols],
            how="left",
            predicate="within",
        )

        # If any facility is slightly outside ward boundaries, assign to nearest ward
        unmatched = facilities_with_ward[facilities_with_ward["Ward_ID"].isna()]
        if len(unmatched) > 0:
            fac_utm = facilities_gdf.loc[unmatched.index].to_crs(crs_proj)
            for idx, fac_geom in fac_utm.geometry.items():
                nearest_idx = wards_utm.geometry.distance(fac_geom).idxmin()
                facilities_with_ward.loc[idx, "Ward_ID"] = merged_wards.loc[nearest_idx, "Ward_ID"]
                facilities_with_ward.loc[idx, "Zone"] = merged_wards.loc[nearest_idx, "Zone"]

        facilities_with_ward["Ward_ID"] = facilities_with_ward["Ward_ID"].fillna(0).astype(int)

        # 4. Aggregations per ward
        ward_fac_agg = facilities_with_ward.groupby("Ward_ID").agg(
            Healthcare_Facilities=("Facility_ID", "count"),
            Hospital_Beds=("Beds", "sum"),
            Total_Doctors=("Doctors", "sum"),
            Public_Facilities=("Ownership", lambda x: (x == "Public").sum()),
            Private_Facilities=("Ownership", lambda x: (x == "Private").sum()),
        ).reset_index()

        # Merge aggregations back into wards
        wards_processed = merged_wards.merge(ward_fac_agg, on="Ward_ID", how="left")
        wards_processed["Healthcare_Facilities"] = wards_processed["Healthcare_Facilities"].fillna(0).astype(int)
        wards_processed["Hospital_Beds"] = wards_processed["Hospital_Beds"].fillna(0).astype(int)
        wards_processed["Total_Doctors"] = wards_processed["Total_Doctors"].fillna(0).astype(int)
        wards_processed["Public_Facilities"] = wards_processed["Public_Facilities"].fillna(0).astype(int)
        wards_processed["Private_Facilities"] = wards_processed["Private_Facilities"].fillna(0).astype(int)

        # 5. Calculate per-capita indicators
        wards_processed["Beds_per_1000"] = (
            (wards_processed["Hospital_Beds"] / wards_processed["Population"].replace(0, 1)) * 1000
        ).round(2)

        wards_processed["Facilities_per_10k"] = (
            (wards_processed["Healthcare_Facilities"] / wards_processed["Population"].replace(0, 1)) * 10000
        ).round(2)

        # 6. Calculate spatial distance from ward centroid to nearest facility & hospital
        wards_utm_full = wards_processed.to_crs(crs_proj)
        fac_utm_full = facilities_with_ward.to_crs(crs_proj)
        ward_centroids_utm = wards_utm_full.geometry.centroid

        hospital_mask = fac_utm_full["Facility_Type"].isin([
            "CHC", "Government Hospital", "General Hospital", "Multi-Speciality Hospital"
        ])
        hospitals_utm = fac_utm_full[hospital_mask]
        if len(hospitals_utm) == 0:
            hospitals_utm = fac_utm_full

        nearest_fac_dist_km = []
        nearest_hosp_dist_km = []

        for c in ward_centroids_utm:
            if len(fac_utm_full) > 0:
                dist_fac = fac_utm_full.geometry.distance(c).min() / 1000.0
            else:
                dist_fac = 15.0
            nearest_fac_dist_km.append(round(dist_fac, 2))

            if len(hospitals_utm) > 0:
                dist_hosp = hospitals_utm.geometry.distance(c).min() / 1000.0
            else:
                dist_hosp = 25.0
            nearest_hosp_dist_km.append(round(dist_hosp, 2))

        wards_processed["Nearest_Facility_Distance"] = nearest_fac_dist_km
        wards_processed["Nearest_Hospital_Distance"] = nearest_hosp_dist_km

        # Add centroid Lat/Lon coordinates from projected UTM centroids
        ward_centroids_geo = ward_centroids_utm.to_crs(config.CRS_GEO)
        wards_processed["Centroid_Lat"] = ward_centroids_geo.y.round(6)
        wards_processed["Centroid_Lon"] = ward_centroids_geo.x.round(6)

        # Clean facilities dataframe
        facilities_clean = facilities_with_ward.drop(columns=["index_right"], errors="ignore").copy()

        # Save processed outputs
        paths = config.get_city_data_paths(key)
        output_wards_file = paths["processed_wards_geojson"]
        output_fac_file = paths["processed_fac_geojson"]

        wards_processed.to_file(output_wards_file, driver="GeoJSON")
        facilities_clean.to_file(output_fac_file, driver="GeoJSON")

        # For backwards compatibility with single-city calls
        if key == "chennai":
            legacy_wards = config.PROCESSED_DATA_DIR / "processed_wards.geojson"
            legacy_facs = config.PROCESSED_DATA_DIR / "processed_facilities.geojson"
            wards_processed.to_file(legacy_wards, driver="GeoJSON")
            facilities_clean.to_file(legacy_facs, driver="GeoJSON")

        metadata = {
            "city_key": key,
            "city_name": city_cfg["city_name"],
            "state_name": city_cfg["state_name"],
            "crs_proj": crs_proj,
            "is_synthetic": is_synthetic,
            "total_wards": len(wards_processed),
            "total_facilities": len(facilities_clean),
            "total_population": int(wards_processed["Population"].sum()),
            "total_beds": int(wards_processed["Hospital_Beds"].sum()),
            "city_beds_per_1000": round(
                (wards_processed["Hospital_Beds"].sum() / wards_processed["Population"].sum()) * 1000, 2
            ),
        }

        return wards_processed, facilities_clean, metadata
