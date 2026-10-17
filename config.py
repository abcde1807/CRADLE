"""
CRADLE Configuration Module
Critical Resource Allocation, Distribution & Location Engine
Multi-City Urban Healthcare Spatial Decision-Support System
Supporting Tamil Nadu (Chennai, Coimbatore), Karnataka (Bengaluru), Telangana (Hyderabad)
"""

from pathlib import Path
from typing import Dict, Any, List, Optional

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SAMPLE_DATA_DIR = DATA_DIR / "sample"

OUTPUTS_DIR = BASE_DIR / "outputs"
MAPS_DIR = OUTPUTS_DIR / "maps"
REPORTS_DIR = OUTPUTS_DIR / "reports"
RESULTS_DIR = OUTPUTS_DIR / "results"
MODELS_DIR = BASE_DIR / "models"
MODEL_METRICS_DIR = OUTPUTS_DIR / "model_metrics"
R_PROJECT_DIR = BASE_DIR / "r_project"

# Ensure all primary runtime directories exist
for p in [RAW_DATA_DIR, PROCESSED_DATA_DIR, SAMPLE_DATA_DIR, MAPS_DIR, REPORTS_DIR, RESULTS_DIR, MODELS_DIR, MODEL_METRICS_DIR]:
    p.mkdir(parents=True, exist_ok=True)

# Coordinate Reference Systems
# EPSG 4326: WGS84 Geographic (Lat/Lon) - Global Standard
CRS_GEO = "EPSG:4326"

# Default CRS for backwards compatibility (Chennai)
CRS_PROJ = "EPSG:32644"

# ==============================================================================
# MULTI-CITY REGISTRY & METADATA
# ==============================================================================

SUPPORTED_CITIES: Dict[str, Dict[str, Any]] = {
    "chennai": {
        "city_key": "chennai",
        "city_name": "Chennai",
        "state_name": "Tamil Nadu",
        "state_code": "TN",
        "country": "India",
        "admin_level": "Ward",
        "admin_body": "Greater Chennai Corporation (GCC)",
        "admin_count": 200,
        "zones_count": 15,
        "center": [13.0827, 80.2707],  # [Lat, Lon]
        "crs_proj": "EPSG:32644",        # UTM Zone 44N (meters)
        "bbox": {
            "min_lat": 12.85,
            "max_lat": 13.25,
            "min_lon": 80.12,
            "max_lon": 80.34,
        },
        "approx_population": 9514495,
        "data_provenance": "SYNTHETIC DEVELOPMENT DATA (Calibrated to GCC 2024)",
        "is_active": True,
        "zones": [
            {"zone_id": 1, "zone_name": "Thiruvottiyur", "region": "North"},
            {"zone_id": 2, "zone_name": "Manali", "region": "North"},
            {"zone_id": 3, "zone_name": "Madhavaram", "region": "North"},
            {"zone_id": 4, "zone_name": "Tondiarpet", "region": "North"},
            {"zone_id": 5, "zone_name": "Royapuram", "region": "North"},
            {"zone_id": 6, "zone_name": "Thiru-Vi-Ka Nagar", "region": "Central"},
            {"zone_id": 7, "zone_name": "Ambattur", "region": "Central"},
            {"zone_id": 8, "zone_name": "Anna Nagar", "region": "Central"},
            {"zone_id": 9, "zone_name": "Teynampet", "region": "Central"},
            {"zone_id": 10, "zone_name": "Kodambakkam", "region": "Central"},
            {"zone_id": 11, "zone_name": "Valasaravakkam", "region": "South"},
            {"zone_id": 12, "zone_name": "Alandur", "region": "South"},
            {"zone_id": 13, "zone_name": "Adyar", "region": "South"},
            {"zone_id": 14, "zone_name": "Perungudi", "region": "South"},
            {"zone_id": 15, "zone_name": "Sholinganallur", "region": "South"},
        ]
    },
    "coimbatore": {
        "city_key": "coimbatore",
        "city_name": "Coimbatore",
        "state_name": "Tamil Nadu",
        "state_code": "TN",
        "country": "India",
        "admin_level": "Ward",
        "admin_body": "Coimbatore City Municipal Corporation (CCMC)",
        "admin_count": 100,
        "zones_count": 5,
        "center": [11.0168, 76.9558],
        "crs_proj": "EPSG:32643",        # UTM Zone 43N (meters)
        "bbox": {
            "min_lat": 10.92,
            "max_lat": 11.14,
            "min_lon": 76.85,
            "max_lon": 77.08,
        },
        "approx_population": 2150000,
        "data_provenance": "SYNTHETIC DEVELOPMENT DATA (Calibrated to CCMC 2024)",
        "is_active": True,
        "zones": [
            {"zone_id": 1, "zone_name": "East Zone", "region": "East"},
            {"zone_id": 2, "zone_name": "West Zone", "region": "West"},
            {"zone_id": 3, "zone_name": "North Zone", "region": "North"},
            {"zone_id": 4, "zone_name": "South Zone", "region": "South"},
            {"zone_id": 5, "zone_name": "Central Zone", "region": "Central"},
        ]
    },
    "bengaluru": {
        "city_key": "bengaluru",
        "city_name": "Bengaluru",
        "state_name": "Karnataka",
        "state_code": "KA",
        "country": "India",
        "admin_level": "Ward",
        "admin_body": "Bruhat Bengaluru Mahanagara Palike (BBMP)",
        "admin_count": 198,
        "zones_count": 8,
        "center": [12.9716, 77.5946],
        "crs_proj": "EPSG:32643",        # UTM Zone 43N (meters)
        "bbox": {
            "min_lat": 12.82,
            "max_lat": 13.16,
            "min_lon": 77.44,
            "max_lon": 77.78,
        },
        "approx_population": 12400000,
        "data_provenance": "SYNTHETIC DEVELOPMENT DATA (Calibrated to BBMP 2024)",
        "is_active": True,
        "zones": [
            {"zone_id": 1, "zone_name": "East Zone", "region": "East"},
            {"zone_id": 2, "zone_name": "West Zone", "region": "West"},
            {"zone_id": 3, "zone_name": "South Zone", "region": "South"},
            {"zone_id": 4, "zone_name": "Bommanahalli", "region": "South-East"},
            {"zone_id": 5, "zone_name": "Dasarahalli", "region": "North-West"},
            {"zone_id": 6, "zone_name": "Mahadevapura", "region": "East"},
            {"zone_id": 7, "zone_name": "Rajarajeshwarinagar", "region": "South-West"},
            {"zone_id": 8, "zone_name": "Yelahanka", "region": "North"},
        ]
    },
    "hyderabad": {
        "city_key": "hyderabad",
        "city_name": "Hyderabad",
        "state_name": "Telangana",
        "state_code": "TS",
        "country": "India",
        "admin_level": "Ward",
        "admin_body": "Greater Hyderabad Municipal Corporation (GHMC)",
        "admin_count": 150,
        "zones_count": 6,
        "center": [17.3850, 78.4867],
        "crs_proj": "EPSG:32644",        # UTM Zone 44N (meters)
        "bbox": {
            "min_lat": 17.25,
            "max_lat": 17.58,
            "min_lon": 78.26,
            "max_lon": 78.64,
        },
        "approx_population": 9800000,
        "data_provenance": "SYNTHETIC DEVELOPMENT DATA (Calibrated to GHMC 2024)",
        "is_active": True,
        "zones": [
            {"zone_id": 1, "zone_name": "Charminar", "region": "South"},
            {"zone_id": 2, "zone_name": "Khairatabad", "region": "Central"},
            {"zone_id": 3, "zone_name": "Secunderabad", "region": "North"},
            {"zone_id": 4, "zone_name": "Serilingampally", "region": "West"},
            {"zone_id": 5, "zone_name": "Kukatpally", "region": "North-West"},
            {"zone_id": 6, "zone_name": "LB Nagar", "region": "East"},
        ]
    },
    "delhi": {
        "city_key": "delhi",
        "city_name": "Delhi (NCT)",
        "state_name": "Delhi",
        "state_code": "DL",
        "country": "India",
        "admin_level": "Ward",
        "admin_body": "Municipal Corporation of Delhi (MCD)",
        "admin_count": 250,
        "zones_count": 12,
        "center": [28.6139, 77.2090],
        "crs_proj": "EPSG:32643",        # UTM Zone 43N (meters)
        "bbox": {
            "min_lat": 28.40,
            "max_lat": 28.88,
            "min_lon": 76.84,
            "max_lon": 77.35,
        },
        "approx_population": 19500000,
        "data_provenance": "SYNTHETIC DEVELOPMENT DATA (Calibrated to MCD 2024)",
        "is_active": True,
        "zones": [
            {"zone_id": 1, "zone_name": "Central Zone", "region": "Central"},
            {"zone_id": 2, "zone_name": "South Zone", "region": "South"},
            {"zone_id": 3, "zone_name": "West Zone", "region": "West"},
            {"zone_id": 4, "zone_name": "Najafgarh", "region": "South-West"},
            {"zone_id": 5, "zone_name": "Rohini", "region": "North-West"},
            {"zone_id": 6, "zone_name": "Civil Lines", "region": "North"},
            {"zone_id": 7, "zone_name": "Karol Bagh", "region": "Central-West"},
            {"zone_id": 8, "zone_name": "City-SP Zone", "region": "Central"},
            {"zone_id": 9, "zone_name": "Keshav Puram", "region": "North-Central"},
            {"zone_id": 10, "zone_name": "Narela", "region": "North"},
            {"zone_id": 11, "zone_name": "Shahdara North", "region": "East"},
            {"zone_id": 12, "zone_name": "Shahdara South", "region": "East"},
        ]
    },
    # Target expansion cities (documented roadmap)
    "madurai": {
        "city_key": "madurai",
        "city_name": "Madurai",
        "state_name": "Tamil Nadu",
        "state_code": "TN",
        "country": "India",
        "admin_level": "Ward",
        "admin_body": "Madurai Municipal Corporation",
        "admin_count": 100,
        "zones_count": 5,
        "center": [9.9252, 78.1198],
        "crs_proj": "EPSG:32644",
        "bbox": {"min_lat": 9.85, "max_lat": 10.02, "min_lon": 78.05, "max_lon": 78.22},
        "approx_population": 1600000,
        "data_provenance": "PLANNED ROADMAP EXPANSION",
        "is_active": False,
        "zones": []
    },
    "mumbai": {
        "city_key": "mumbai",
        "city_name": "Mumbai",
        "state_name": "Maharashtra",
        "state_code": "MH",
        "country": "India",
        "admin_level": "Ward",
        "admin_body": "Brihanmumbai Municipal Corporation (BMC)",
        "admin_count": 227,
        "zones_count": 7,
        "center": [19.0760, 72.8777],
        "crs_proj": "EPSG:32643",
        "bbox": {"min_lat": 18.89, "max_lat": 19.28, "min_lon": 72.77, "max_lon": 72.99},
        "approx_population": 13000000,
        "data_provenance": "PLANNED ROADMAP EXPANSION",
        "is_active": False,
        "zones": []
    }
}

DEFAULT_CITY = "chennai"

def get_city_config(city_key: str = DEFAULT_CITY) -> Dict[str, Any]:
    """Retrieves full configuration dict for a specified city."""
    key = (city_key or DEFAULT_CITY).lower().strip()
    if key not in SUPPORTED_CITIES:
        key = DEFAULT_CITY
    return SUPPORTED_CITIES[key]

def get_city_crs(city_key: str = DEFAULT_CITY) -> str:
    """Returns the projected metric CRS (e.g. EPSG:32644 or EPSG:32643)."""
    return get_city_config(city_key).get("crs_proj", CRS_PROJ)

get_metric_crs_for_city = get_city_crs

def get_city_center(city_key: str = DEFAULT_CITY) -> List[float]:
    """Returns [Lat, Lon] center coordinates."""
    return get_city_config(city_key).get("center", [13.0827, 80.2707])

def get_city_bbox(city_key: str = DEFAULT_CITY) -> Dict[str, float]:
    """Returns bounding box dictionary."""
    return get_city_config(city_key).get("bbox", {})

def get_city_data_paths(city_key: str = DEFAULT_CITY) -> Dict[str, Path]:
    """Returns paths for raw, sample, and processed datasets for the city."""
    key = (city_key or DEFAULT_CITY).lower().strip()
    return {
        "raw_wards_geojson": RAW_DATA_DIR / f"{key}_wards.geojson",
        "raw_wards_shp": RAW_DATA_DIR / f"{key}_wards.shp",
        "raw_pop_csv": RAW_DATA_DIR / f"{key}_population.csv",
        "raw_fac_csv": RAW_DATA_DIR / f"{key}_healthcare_facilities.csv",
        "sample_wards_geojson": SAMPLE_DATA_DIR / f"{key}_wards.geojson",
        "sample_pop_csv": SAMPLE_DATA_DIR / f"{key}_population.csv",
        "sample_fac_csv": SAMPLE_DATA_DIR / f"{key}_healthcare_facilities.csv",
        "processed_wards_geojson": PROCESSED_DATA_DIR / f"processed_{key}_wards.geojson",
        "processed_fac_geojson": PROCESSED_DATA_DIR / f"processed_{key}_facilities.geojson",
    }

# Backwards-compatible aliases for single-city Chennai calls
CHENNAI_CENTER = SUPPORTED_CITIES["chennai"]["center"]
CHENNAI_BBOX = SUPPORTED_CITIES["chennai"]["bbox"]
GCC_ZONES = SUPPORTED_CITIES["chennai"]["zones"]

# ==============================================================================
# HEALTHCARE BENCHMARKS & PLANNING ASSUMPTIONS
# ==============================================================================

FACILITY_TYPES = {
    "PHC": {"name": "Primary Health Centre", "min_beds": 4, "max_beds": 10, "avg_doctors": 2, "level": 1, "cost_crores": 2.5},
    "UPHC": {"name": "Urban Primary Health Centre", "min_beds": 6, "max_beds": 15, "avg_doctors": 3, "level": 1, "cost_crores": 3.5},
    "CHC": {"name": "Community Health Centre", "min_beds": 30, "max_beds": 50, "avg_doctors": 6, "level": 2, "cost_crores": 8.0},
    "Government Hospital": {"name": "Government Sub-District/District Hospital", "min_beds": 100, "max_beds": 350, "avg_doctors": 25, "level": 3, "cost_crores": 25.0},
    "General Hospital": {"name": "Government General Hospital", "min_beds": 400, "max_beds": 1200, "avg_doctors": 80, "level": 4, "cost_crores": 65.0},
    "Multi-Speciality Hospital": {"name": "Multi-Speciality Hospital", "min_beds": 150, "max_beds": 600, "avg_doctors": 50, "level": 4, "cost_crores": 50.0},
    "Private Clinic": {"name": "Private Nursing Home/Clinic", "min_beds": 5, "max_beds": 30, "avg_doctors": 4, "level": 1, "cost_crores": 5.0},
}

BENCHMARKS = {
    "beds_per_1000_who": 3.0,          # WHO recommendation
    "beds_per_1000_national": 1.5,     # Indian National Health Policy baseline
    "target_facility_distance_km": 2.5,# Target max travel distance for primary care
    "hospital_distance_km": 5.0,       # Target max travel distance for secondary/tertiary hospital
}

DEFAULT_GAP_WEIGHTS = {
    "population_pressure": 0.30,
    "capacity_deficit": 0.30,
    "distance_gap": 0.25,
    "facility_scarcity": 0.15,
}

GAP_THRESHOLDS = {
    "Low": (0.0, 25.0),
    "Moderate": (25.0, 50.0),
    "High": (50.0, 70.0),
    "Critical": (70.0, 100.0),
}

DESERT_CRITERIA = {
    "min_gap_score": 60.0,
    "min_distance_to_hospital_km": 3.5,
    "max_beds_per_1000": 1.0,
}

CANDIDATE_CONFIG = {
    "grid_size_meters": 500,
    "existing_facility_buffer_m": 600,
    "target_priorities": ["Critical", "High"],
}

DEFAULT_CANDIDATE_WEIGHTS = {
    "gap_severity": 0.40,
    "population_coverage": 0.30,
    "facility_distance": 0.20,
    "road_proximity": 0.10,
}

CANDIDATE_CATEGORIES = {
    "Highly Recommended": (75.0, 100.0),
    "Recommended": (60.0, 75.0),
    "Moderate": (45.0, 60.0),
    "Low Priority": (0.0, 45.0),
}

COVERAGE_RADII_KM = [2.0, 3.0, 5.0]
COVERAGE_RADII_METERS = [2000, 3000, 5000]

TWO_SFCA_CONFIG = {
    "catchment_radius_km": 4.0,
    "decay_type": "gravity",
    "gravity_beta": 1.5,
}

ROAD_SPEEDS = {
    "motorway": 60.0,
    "trunk": 50.0,
    "primary": 40.0,
    "secondary": 30.0,
    "tertiary": 25.0,
    "residential": 20.0,
    "default": 25.0,
}

AHP_CRITERIA = [
    "population_density",
    "road_accessibility",
    "existing_facility_distance",
    "land_availability",
    "flood_safety",
]

DEFAULT_AHP_WEIGHTS = {
    "population_density": 0.28,
    "road_accessibility": 0.24,
    "existing_facility_distance": 0.22,
    "land_availability": 0.16,
    "flood_safety": 0.10,
}

BUDGET_SCENARIOS = {
    "Low Budget": {"budget_crores": 15.0, "max_facilities": 3, "preferred_type": "UPHC"},
    "Medium Budget": {"budget_crores": 35.0, "max_facilities": 6, "preferred_type": "CHC"},
    "High Budget": {"budget_crores": 80.0, "max_facilities": 10, "preferred_type": "Government Hospital"},
}

SENSITIVITY_PROFILES = {
    "Balanced (Baseline)": {
        "gap_severity": 0.40,
        "population_coverage": 0.30,
        "facility_distance": 0.20,
        "road_proximity": 0.10,
    },
    "Population-Focused": {
        "gap_severity": 0.25,
        "population_coverage": 0.55,
        "facility_distance": 0.10,
        "road_proximity": 0.10,
    },
    "Capacity & Gap-Focused": {
        "gap_severity": 0.60,
        "population_coverage": 0.20,
        "facility_distance": 0.10,
        "road_proximity": 0.10,
    },
    "Spatial Accessibility-Focused": {
        "gap_severity": 0.25,
        "population_coverage": 0.20,
        "facility_distance": 0.35,
        "road_proximity": 0.20,
    },
}
