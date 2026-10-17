"""
CRADLE: Critical Resource Allocation, Distribution & Location Engine
Main Application Portal & Multi-City Executive Dashboard
Chennai, Coimbatore, Bengaluru, Hyderabad (India)
"""

import streamlit as st
import geopandas as gpd
import pandas as pd
from pathlib import Path
import folium
from streamlit_folium import st_folium

import config
from src.data_loader import DataLoader
from src.preprocessing import PreprocessingPipeline
from src.gap_analyzer import HealthcareGapAnalyzer
from src.healthcare_desert import HealthcareDesertDetector
from src.facility_pressure import FacilityPressureAnalyzer

# Page configuration
st.set_page_config(
    page_title="CRADLE | Multi-City Urban Healthcare Spatial Decision-Support",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern academic styling
st.markdown("""
<style>
    .main-header {
        font-family: 'Segoe UI', sans-serif;
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-family: 'Segoe UI', sans-serif;
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #F8FAFC;
        border-left: 5px solid #3B82F6;
        padding: 1.2rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    .badge-critical {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(show_spinner="Loading and preparing spatial decision data...")
def load_cached_system_data(city_key: str = None):
    """Ensures datasets exist and returns processed wards and facilities for the requested city."""
    if city_key is None:
        city_key = st.session_state.get("selected_city", config.DEFAULT_CITY)
    city_key = city_key.lower().strip()

    paths = config.get_city_data_paths(city_key)
    wards_file = paths["processed_wards_geojson"]
    fac_file = paths["processed_fac_geojson"]

    if not wards_file.exists() or not fac_file.exists():
        # Fallback to single-city legacy path
        wards_file = config.PROCESSED_DATA_DIR / "processed_wards.geojson"
        fac_file = config.PROCESSED_DATA_DIR / "processed_facilities.geojson"

    wards_gdf = gpd.read_file(wards_file)
    facilities_gdf = gpd.read_file(fac_file)

    return wards_gdf, facilities_gdf


def main():
    # Sidebar Multi-City Control
    with st.sidebar:
        st.image("https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=400&q=80")
        st.title("CRADLE Engine")
        st.caption("Urban Health Geospatial Decision Support")
        st.markdown("---")

        active_cities = [k for k, v in config.SUPPORTED_CITIES.items() if v.get("is_active") is True]
        default_idx = 0
        if "selected_city" in st.session_state and st.session_state["selected_city"] in active_cities:
            default_idx = active_cities.index(st.session_state["selected_city"])

        selected_city = st.selectbox(
            "📍 Select Metropolitan City",
            options=active_cities,
            index=default_idx,
            format_func=lambda k: f"{config.SUPPORTED_CITIES[k]['city_name']} ({config.SUPPORTED_CITIES[k]['state_code']})"
        )
        st.session_state["selected_city"] = selected_city

        city_cfg = config.get_city_config(selected_city)
        st.markdown(f"**Jurisdiction:** {city_cfg['admin_body']}")
        st.markdown(f"**Spatial Units:** {city_cfg['admin_count']} Wards ({city_cfg['zones_count']} Zones)")
        st.markdown(f"**Metric Projection:** {city_cfg['crs_proj']}")
        st.markdown(f"**Methodology:** Gap-First Spatial Allocation")

        st.info(f"💡 **Provenance:** {city_cfg['data_provenance']}")

    city_cfg = config.get_city_config(selected_city)
    st.markdown('<div class="main-header">CRADLE: Critical Resource Allocation, Distribution & Location Engine</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">Urban Healthcare Spatial Decision-Support System | {city_cfg["city_name"]}, {city_cfg["state_name"]} ({city_cfg["admin_body"]})</div>', unsafe_allow_html=True)

    wards_gdf, facilities_gdf = load_cached_system_data(selected_city)

    # High-level KPI summary
    total_pop = int(wards_gdf["Population"].sum())
    total_fac = len(facilities_gdf)
    total_beds = int(wards_gdf["Hospital_Beds"].sum())
    city_beds_k = round((total_beds / max(total_pop, 1)) * 1000, 2)
    crit_wards = int((wards_gdf["Priority_Category"] == "Critical").sum())
    desert_wards = int(wards_gdf["Healthcare_Desert"].sum())
    desert_pop = int(wards_gdf["Desert_Affected_Population"].sum()) if "Desert_Affected_Population" in wards_gdf.columns else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Population", f"{total_pop:,}", help=f"Census and municipal population estimate for {city_cfg['city_name']}")
        st.metric(f"Total Wards", f"{len(wards_gdf)} Wards", help=f"{city_cfg['zones_count']} Administrative Zones")
    with c2:
        st.metric("Total Facilities", f"{total_fac}", help="Hospitals, CHCs, UPHCs, PHCs")
        st.metric("Inpatient Beds", f"{total_beds:,}", help="Public & Private registered beds")
    with c3:
        st.metric("Beds / 1,000 Pop", f"{city_beds_k}", delta=f"{city_beds_k - 3.0:.2f} vs WHO (3.0)")
        st.metric("Critical Priority Wards", f"{crit_wards}", delta="Requires Urgent Siting", delta_color="inverse")
    with c4:
        st.metric("Healthcare Deserts", f"{desert_wards} Wards", delta=f"{desert_wards/len(wards_gdf)*100:.1f}% of City", delta_color="inverse")
        st.metric("Desert Pop Affected", f"{desert_pop:,}", delta="Underserved residents", delta_color="inverse")

    st.markdown("---")

    # Workflow & Navigation Tabs
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader("Gap-First Healthcare Planning Workflow")
        st.markdown("""
        Conventional facility planning asks: *"Where is suitable vacant land for a hospital?"*  
        **CRADLE inverts this paradigm** by identifying where the population is most critically underserved first:
        """)

        st.markdown("""
        ```text
        1. Healthcare Need  ──► Population pressure & demographic vulnerability
                │
        2. Resource Gap     ──► 4-Indicator Gap Score (0-100) per ward
                │
        3. Priority Wards   ──► Pinpoint Critical wards & Healthcare Deserts
                │
        4. Candidate Siting ──► 500m spatial grid within priority voids
                │
        5. Site Ranking     ──► Multi-factor scoring (Gap + Coverage + Spacing)
                │
        6. Interventions    ──► PHC vs CHC vs Secondary Hospital allocation
                │
        7. Optimization     ──► MCLP integer programming & AIPS robustness
                │
        8. Machine Learning ──► Leave-One-City-Out predictive priority model
        ```
        """)

    with col_right:
        st.subheader("System Modules & Review-3 Deliverables")
        st.markdown("""
        Explore the analytical pages via the sidebar navigation:
        - **1. Overview:** City infrastructure, zone breakdown & cross-city benchmark
        - **2. Gap Analyzer:** 4-factor Healthcare Gap Score (0-100) & explainability
        - **3. Healthcare Deserts:** Spatial desert detection & facility gravity pressure
        - **4. Candidate Finder:** 500m candidate location grid & ranking
        - **5. Scenario Simulator:** Before vs After investment simulation
        - **6. Accessibility:** 2SFCA accessibility & road network isochrones
        - **7. Optimization:** MCLP integer optimizer & AIPS robustness
        - **8. Machine Learning:** Spatial LOCO cross-validation & interactive predictor
        - **9. Data Quality:** Provenance audit & Python-vs-R numerical validation
        """)

    st.markdown("---")
    st.subheader(f"Healthcare Infrastructure Overview Map: {city_cfg['city_name']}")

    # Interactive Folium map of Selected City
    city_center = city_cfg["center"]
    m = folium.Map(location=city_center, zoom_start=11, tiles="OpenStreetMap")

    # Add facilities as markers
    for _, fac in facilities_gdf.head(150).iterrows():
        color = "red" if "Hospital" in str(fac.get("Facility_Type", "")) else "blue"
        folium.CircleMarker(
            location=[fac["Latitude"], fac["Longitude"]],
            radius=4,
            color=color,
            fill=True,
            fill_opacity=0.7,
            popup=f"<b>{fac.get('Facility_Name', 'Facility')}</b><br>Type: {fac.get('Facility_Type', 'N/A')}<br>Beds: {fac.get('Beds', 0)}<br>Doctors: {fac.get('Doctors', 0)}",
        ).add_to(m)

    st_folium(m, width=None, height=480)


if __name__ == "__main__":
    main()
