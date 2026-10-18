"""
CRADLE: Critical Resource Allocation, Distribution & Location Engine
Main Application Portal & Multi-City Executive Dashboard
Chennai, Coimbatore, Bengaluru, Hyderabad, Delhi (India)
"""

import streamlit as st
import geopandas as gpd
import pandas as pd
from pathlib import Path
import folium
from streamlit_folium import st_folium

import config
from src.ui_components import (
    render_page_header_and_city_selector,
    render_methodology_card,
    load_cached_system_data,
    inject_custom_css
)

# Page configuration
st.set_page_config(
    page_title="CRADLE | Multi-City Urban Healthcare Spatial Decision-Support",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    # 1. Top Navbar, Header and Persistent City Controller
    selected_city, city_cfg, wards_gdf, facilities_gdf = render_page_header_and_city_selector(
        page_title="CRADLE: Urban Healthcare Spatial Decision-Support Engine",
        page_icon="🏥",
        page_subtitle="Gap-First Resource Allocation, Facility Siting & Optimization Platform",
        page_key="home"
    )

    # 2. High-Level Municipal Infrastructure KPIs
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
        st.metric("Spatial Units", f"{len(wards_gdf)} Wards", help=f"{city_cfg['zones_count']} Administrative Zones")
    with c2:
        st.metric("Healthcare Facilities", f"{total_fac}", help="Hospitals, CHCs, UPHCs, PHCs")
        st.metric("Registered Beds", f"{total_beds:,}", help="Public & Private registered inpatient beds")
    with c3:
        st.metric("Beds / 1,000 Pop", f"{city_beds_k}", delta=f"{city_beds_k - 3.0:.2f} vs WHO Target (3.0)")
        st.metric("Critical Gap Wards", f"{crit_wards}", delta="Requires Urgent Siting", delta_color="inverse")
    with c4:
        st.metric("Healthcare Deserts", f"{desert_wards} Wards", delta=f"{desert_wards/len(wards_gdf)*100:.1f}% of City", delta_color="inverse")
        st.metric("Desert Pop Affected", f"{desert_pop:,}", delta="Underserved residents", delta_color="inverse")

    st.markdown("---")

    # 3. Workflow & System Deliverables Breakdown
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader("Gap-First Healthcare Planning Architecture")
        st.markdown("""
        Conventional facility planning asks: *"Where is suitable vacant land for a hospital?"*  
        **CRADLE inverts this paradigm through a Gap-First Spatial Allocation Framework:**
        """)

        st.markdown("""
        ```text
        1. Healthcare Need  ──► Population pressure & demographic vulnerability (898 Wards)
                │
        2. Resource Gap     ──► 4-Indicator Gap Score (0-100) per ward
                │
        3. Priority Wards   ──► Pinpoint Critical wards & Healthcare Deserts (57.3% Desert Prevalence)
                │
        4. Candidate Siting ──► 500m spatial grid within priority voids
                │
        5. Site Ranking     ──► Multi-factor scoring (Gap + Coverage + Spacing)
                │
        6. Interventions    ──► PHC vs CHC vs Secondary Hospital allocation
                │
        7. Optimization     ──► MCLP integer programming & AIPS robustness
                │
        8. Machine Learning ──► Leave-One-City-Out predictive priority model (85.1% LOCO Acc)
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

    # 4. Interactive Infrastructure Map
    st.subheader(f"Healthcare Infrastructure Overview Map: {city_cfg['city_name']}")

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

    # 5. Methodological Reference Card
    render_methodology_card(
        module_title="Gap-First Spatial Decision-Support Architecture",
        mathematical_formula=r"\text{Siting Priority} = f(\text{Need}, \text{Gap}, \text{Accessibility}, \text{Spatial Isolation})",
        conceptual_explanation="""
        CRADLE prioritizes spatial justice over commercial land availability. By computing continuous 
        healthcare deficit indicators, identifying acute spatial voids, and solving integer linear programs, 
        the engine provides public health authorities with defensible, mathematically validated location decisions.
        """,
        interpretation_points=[
            "**Total Beds / 1,000 Pop:** Benchmarked against the World Health Organization (WHO) standard of 3.0 beds per 1,000 residents.",
            "**Critical Wards:** Administrative areas exhibiting extreme composite gap scores (≥ 70/100) requiring urgent public capital investment.",
            "**Healthcare Deserts:** Severe spatial voids where residents lack both local bed capacity and reasonable travel proximity to secondary hospitals.",
        ],
        policy_implications=[
            "Direct primary care capital budgets towards designated Healthcare Desert clusters.",
            "Deploy Urban Primary Health Centres (UPHCs) to relieve patient congestion at secondary and tertiary hospitals.",
            "Use cross-city comparative benchmarks to establish statewide resource rebalancing policies.",
        ]
    )


if __name__ == "__main__":
    main()
