"""
CRADLE Multi-City Data Loader Module
Handles data ingestion, schema validation, type standardization, and fallback handling
for administrative units, population, and healthcare facilities across all supported cities.
"""

import os
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon

import config


class DataLoader:
    """
    Ingests and validates geospatial and tabular datasets for CRADLE across cities.
    Automatically handles city-specific coordinate boundaries, metric projections,
    and switches between user-supplied raw datasets and validated development datasets.
    """

    REQUIRED_WARD_COLS = ["Ward_ID", "Ward_Name", "Zone", "geometry"]
    REQUIRED_POP_COLS = ["Ward_ID", "Population", "Population_Density"]
    REQUIRED_FACILITY_COLS = [
        "Facility_ID",
        "Facility_Name",
        "Latitude",
        "Longitude",
        "Facility_Type",
        "Beds",
        "Doctors",
        "Ownership",
    ]

    def __init__(
        self,
        raw_dir: Path = config.RAW_DATA_DIR,
        sample_dir: Path = config.SAMPLE_DATA_DIR,
        processed_dir: Path = config.PROCESSED_DATA_DIR,
    ):
        self.raw_dir = Path(raw_dir)
        self.sample_dir = Path(sample_dir)
        self.processed_dir = Path(processed_dir)

        # Create directories if they don't exist
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.sample_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def load_wards(self, city_key: str = config.DEFAULT_CITY) -> Tuple[gpd.GeoDataFrame, bool]:
        """
        Loads ward boundaries for the specified city.
        First checks raw directory, then falls back to sample directory.
        Returns:
            Tuple of (GeoDataFrame, is_synthetic_flag)
        """
        key = (city_key or config.DEFAULT_CITY).lower().strip()
        paths = config.get_city_data_paths(key)

        source_path = None
        is_synthetic = False

        if paths["raw_wards_geojson"].exists():
            source_path = paths["raw_wards_geojson"]
        elif paths["raw_wards_shp"].exists():
            source_path = paths["raw_wards_shp"]
        elif paths["sample_wards_geojson"].exists():
            source_path = paths["sample_wards_geojson"]
            is_synthetic = True
        else:
            # Fallback legacy check
            legacy_sample = self.sample_dir / f"{key}_wards.geojson"
            if legacy_sample.exists():
                source_path = legacy_sample
                is_synthetic = True
            else:
                raise FileNotFoundError(
                    f"No ward boundaries found for city '{key}'. "
                    "Run `python scripts/generate_sample_data.py` to generate multi-city datasets."
                )

        gdf = gpd.read_file(source_path)
        gdf = self._validate_and_clean_wards(gdf, key)
        gdf.attrs["is_synthetic"] = is_synthetic
        gdf.attrs["city_key"] = key
        gdf.attrs["source_path"] = str(source_path)
        return gdf, is_synthetic

    def load_population(self, city_key: str = config.DEFAULT_CITY) -> Tuple[pd.DataFrame, bool]:
        """
        Loads population and demographic data for the specified city.
        Returns:
            Tuple of (DataFrame, is_synthetic_flag)
        """
        key = (city_key or config.DEFAULT_CITY).lower().strip()
        paths = config.get_city_data_paths(key)

        if paths["raw_pop_csv"].exists():
            df = pd.read_csv(paths["raw_pop_csv"])
            is_synthetic = False
        elif paths["sample_pop_csv"].exists():
            df = pd.read_csv(paths["sample_pop_csv"])
            is_synthetic = True
        else:
            raise FileNotFoundError(
                f"No population data found for city '{key}' in raw or sample directories."
            )

        df = self._validate_and_clean_population(df, key)
        df.attrs["is_synthetic"] = is_synthetic
        df.attrs["city_key"] = key
        return df, is_synthetic

    def load_facilities(self, city_key: str = config.DEFAULT_CITY) -> Tuple[gpd.GeoDataFrame, bool]:
        """
        Loads healthcare facilities for the specified city and converts to spatial points.
        Returns:
            Tuple of (GeoDataFrame, is_synthetic_flag)
        """
        key = (city_key or config.DEFAULT_CITY).lower().strip()
        paths = config.get_city_data_paths(key)

        if paths["raw_fac_csv"].exists():
            df = pd.read_csv(paths["raw_fac_csv"])
            is_synthetic = False
        elif paths["sample_fac_csv"].exists():
            df = pd.read_csv(paths["sample_fac_csv"])
            is_synthetic = True
        else:
            raise FileNotFoundError(
                f"No healthcare facility data found for city '{key}' in raw or sample directories."
            )

        gdf = self._validate_and_clean_facilities(df, key)
        gdf.attrs["is_synthetic"] = is_synthetic
        gdf.attrs["city_key"] = key
        return gdf, is_synthetic

    def _validate_and_clean_wards(self, gdf: gpd.GeoDataFrame, city_key: str) -> gpd.GeoDataFrame:
        """Validates and cleans ward spatial dataset with city-specific metric projection."""
        city_cfg = config.get_city_config(city_key)
        crs_proj = city_cfg.get("crs_proj", config.CRS_PROJ)

        # Ensure CRS
        if gdf.crs is None:
            gdf.set_crs(config.CRS_GEO, inplace=True)
        elif gdf.crs != config.CRS_GEO:
            gdf = gdf.to_crs(config.CRS_GEO)

        # Standardize composite metadata
        if "City" not in gdf.columns:
            gdf["City"] = city_cfg["city_name"]
        if "City_Key" not in gdf.columns:
            gdf["City_Key"] = city_key
        if "State" not in gdf.columns:
            gdf["State"] = city_cfg["state_name"]
        if "Country" not in gdf.columns:
            gdf["Country"] = "India"

        # Check required columns
        for col in self.REQUIRED_WARD_COLS:
            if col not in gdf.columns:
                if col == "Ward_Name" and "Ward_ID" in gdf.columns:
                    gdf["Ward_Name"] = "Ward " + gdf["Ward_ID"].astype(str)
                elif col == "Zone":
                    gdf["Zone"] = f"{city_cfg['city_name']} Central"
                else:
                    raise ValueError(f"Missing required ward column for {city_key}: {col}")

        # Compute accurate Area_km2 in city-specific projected CRS
        if "Area_km2" not in gdf.columns or gdf["Area_km2"].isna().any():
            utm_gdf = gdf.to_crs(crs_proj)
            gdf["Area_km2"] = (utm_gdf.geometry.area / 1e6).round(3)

        # Drop invalid geometries or null Ward_ID
        gdf = gdf.dropna(subset=["Ward_ID", "geometry"]).copy()
        gdf = gdf[gdf.geometry.is_valid].copy()
        gdf["Ward_ID"] = pd.to_numeric(gdf["Ward_ID"], errors="coerce").fillna(0).astype(int)

        # Ensure composite ID
        if "Composite_ID" not in gdf.columns:
            sc = city_cfg.get("state_code", "IN")
            gdf["Composite_ID"] = gdf["Ward_ID"].apply(lambda wid: f"IND_{sc}_{city_key[:3].upper()}_{wid:03d}")

        return gdf.drop_duplicates(subset=["Ward_ID"])

    def _validate_and_clean_population(self, df: pd.DataFrame, city_key: str) -> pd.DataFrame:
        """Validates and cleans demographic dataset."""
        df = df.copy()
        city_cfg = config.get_city_config(city_key)

        for col in ["Ward_ID", "Population"]:
            if col not in df.columns:
                raise ValueError(f"Missing required population column for {city_key}: {col}")

        df["Ward_ID"] = pd.to_numeric(df["Ward_ID"], errors="coerce").fillna(0).astype(int)
        df["Population"] = pd.to_numeric(df["Population"], errors="coerce").fillna(0).astype(int)

        if "Area_km2" not in df.columns:
            df["Area_km2"] = 2.0
        else:
            df["Area_km2"] = pd.to_numeric(df["Area_km2"], errors="coerce").fillna(2.0).astype(float)

        if "Population_Density" not in df.columns:
            df["Population_Density"] = (df["Population"] / df["Area_km2"].replace(0, 0.001)).round(1)
        else:
            df["Population_Density"] = pd.to_numeric(df["Population_Density"], errors="coerce").fillna(0.0).astype(float)

        if "Elderly" not in df.columns:
            df["Elderly"] = (df["Population"] * 0.10).astype(int)
        if "Children" not in df.columns:
            df["Children"] = (df["Population"] * 0.18).astype(int)
        if "Working_Age" not in df.columns:
            df["Working_Age"] = df["Population"] - df["Elderly"] - df["Children"]
        if "Households" not in df.columns:
            df["Households"] = (df["Population"] / 4.0).round().astype(int)

        if "City" not in df.columns:
            df["City"] = city_cfg["city_name"]
        if "City_Key" not in df.columns:
            df["City_Key"] = city_key
        if "State" not in df.columns:
            df["State"] = city_cfg["state_name"]
        if "Country" not in df.columns:
            df["Country"] = "India"

        if "Composite_ID" not in df.columns:
            sc = city_cfg.get("state_code", "IN")
            df["Composite_ID"] = df["Ward_ID"].apply(lambda wid: f"IND_{sc}_{city_key[:3].upper()}_{wid:03d}")

        return df.drop_duplicates(subset=["Ward_ID"])

    def _validate_and_clean_facilities(self, df: pd.DataFrame, city_key: str) -> gpd.GeoDataFrame:
        """Validates facility dataset and converts to GeoDataFrame."""
        df = df.copy()
        city_cfg = config.get_city_config(city_key)
        bbox = city_cfg.get("bbox", {})

        for col in self.REQUIRED_FACILITY_COLS:
            if col not in df.columns:
                if col == "Doctors" and "Beds" in df.columns:
                    df["Doctors"] = (df["Beds"] / 10).clip(lower=1).astype(int)
                elif col == "Ownership":
                    df["Ownership"] = "Public"
                else:
                    raise ValueError(f"Missing required facility column for {city_key}: {col}")

        df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
        df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")
        df["Beds"] = pd.to_numeric(df["Beds"], errors="coerce").fillna(0).astype(int)
        df["Doctors"] = pd.to_numeric(df["Doctors"], errors="coerce").fillna(0).astype(int)

        # Coordinate bounding box check
        if bbox:
            valid_coords = (
                (df["Latitude"] >= bbox["min_lat"] - 0.25)
                & (df["Latitude"] <= bbox["max_lat"] + 0.25)
                & (df["Longitude"] >= bbox["min_lon"] - 0.25)
                & (df["Longitude"] <= bbox["max_lon"] + 0.25)
            )
            df = df[valid_coords].copy()

        if "City" not in df.columns:
            df["City"] = city_cfg["city_name"]
        if "City_Key" not in df.columns:
            df["City_Key"] = city_key
        if "State" not in df.columns:
            df["State"] = city_cfg["state_name"]

        geometry = [Point(xy) for xy in zip(df["Longitude"], df["Latitude"])]
        gdf = gpd.GeoDataFrame(df, geometry=geometry, crs=config.CRS_GEO)
        return gdf.drop_duplicates(subset=["Facility_ID"])
