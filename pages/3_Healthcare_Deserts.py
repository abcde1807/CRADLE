"""
CRADLE Dashboard - Page 3: Healthcare Deserts & Facility Pressure
Identifies spatial healthcare deserts, evaluates affected vulnerable populations,
and tracks facility operating strain across Chennai.
"""

import streamlit as st
import geopandas as gpd
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium

import config
from app import load_cached_system_data
from src.healthcare_desert import HealthcareDesertDetector
from src.facility_pressure import FacilityPressureAnalyzer

st.set_page_config(page_title="Healthcare Deserts | CRADLE", page_icon="🏜️", layout="wide")

selected_city = st.session_state.get("selected_city", config.DEFAULT_CITY)
city_cfg = config.get_city_config(selected_city)

st.title(f"🏜️ Healthcare Desert Detection & Facility Pressure: {city_cfg['city_name']}")
st.caption(f"Pinpoints geographical healthcare deserts in {city_cfg['city_name']} and quantifies operational strain on existing hospitals.")

wards_gdf, facilities_gdf = load_cached_system_data(selected_city)

detector = HealthcareDesertDetector()
wards_deserts = detector.detect_deserts(wards_gdf)
desert_stats = detector.summarize_deserts(wards_deserts)

pressure_analyzer = FacilityPressureAnalyzer()
facilities_pressure = pressure_analyzer.calculate_facility_pressure(facilities_gdf, wards_deserts)
pressure_stats = pressure_analyzer.summarize_pressure(facilities_pressure)

# KPI Summary Cards
c1, c2, c3, c4 = st.columns(4)
c1.metric("Healthcare Desert Wards", f"{desert_stats['total_desert_wards']} Wards", f"{desert_stats['percentage_desert_wards']}% of city")
c2.metric("Desert Population Affected", f"{desert_stats['total_affected_population']:,}", f"{desert_stats['percentage_population_affected']}% of population")
c3.metric("Critical Strained Facilities", f"{pressure_stats['critical_facilities_count']} Facilities", delta="Overburdened Catchment", delta_color="inverse")
c4.metric("Average Facility Pressure", f"{pressure_stats['mean_pressure_ratio']:.2f}x", help="Ratio of allocated population to standard bed capacity")

st.markdown("---")

col_map, col_table = st.columns([3, 2])

with col_map:
    st.subheader("Spatial Healthcare Deserts & Facility Strain Map")
    st.markdown("🔴 **Red Polygon:** Healthcare Desert Wards | 🟠 **Markers:** Facilities by Strain Level")

    m = folium.Map(location=city_cfg["center"], zoom_start=11, tiles="OpenStreetMap")

    # Add Desert Wards
    desert_subset = wards_deserts[wards_deserts["Healthcare_Desert"]]
    if len(desert_subset) > 0:
        folium.GeoJson(
            desert_subset.to_json(),
            name="Healthcare Deserts",
            style_function=lambda x: {
                "fillColor": "#DC2626",
                "color": "#991B1B",
                "weight": 2,
                "fillOpacity": 0.55,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=["Ward_ID", "Ward_Name", "Zone", "Gap_Score", "Healthcare_Desert_Severity", "Population"],
                aliases=["Ward ID:", "Ward Name:", "Zone:", "Gap Score:", "Desert Severity:", "Population:"],
            ),
        ).add_to(m)

    # Add Facilities colored by pressure
    pressure_colors = {"Critical": "#991B1B", "High": "#EA580C", "Moderate": "#EAB308", "Low": "#16A34A"}
    for _, fac in facilities_pressure.iterrows():
        cat = fac.get("Pressure_Category", "Moderate")
        folium.CircleMarker(
            location=[fac["Latitude"], fac["Longitude"]],
            radius=6 if cat in ["Critical", "High"] else 4,
            color=pressure_colors.get(cat, "#3B82F6"),
            fill=True,
            fill_opacity=0.85,
            tooltip=f"{fac['Facility_Name']}<br>Type: {fac['Facility_Type']}<br>Beds: {fac['Beds']}<br>Pop Served: {fac['Estimated_Pop_Served']:,}<br>Pressure: {fac['Pressure_Ratio']}x ({cat})",
        ).add_to(m)

    st_folium(m, width=None, height=480)

with col_table:
    st.subheader("Top Healthcare Deserts by Severity")
    top_deserts_df = desert_subset.sort_values("Healthcare_Desert_Severity", ascending=False)[
        ["Ward_ID", "Ward_Name", "Zone", "Gap_Score", "Healthcare_Desert_Severity", "Nearest_Hospital_Distance", "Population"]
    ]

    st.dataframe(
        top_deserts_df.head(10),
        column_config={
            "Gap_Score": st.column_config.NumberColumn(format="%.1f"),
            "Healthcare_Desert_Severity": st.column_config.ProgressColumn(format="%.1f", min_value=0, max_value=100),
            "Nearest_Hospital_Distance": st.column_config.NumberColumn(format="%.1f km"),
            "Population": st.column_config.NumberColumn(format="%d"),
        },
        hide_index=True,
        use_container_width=True,
    )

st.markdown("---")

# Facility Strain Breakdown
col_chart, col_facs = st.columns([1, 1])

with col_chart:
    st.subheader("Facility Operating Strain Distribution")
    pressure_counts = pd.DataFrame(list(pressure_stats["pressure_breakdown"].items()), columns=["Category", "Count"])
    fig_pressure = px.bar(
        pressure_counts,
        x="Category",
        y="Count",
        color="Category",
        color_discrete_map={"Low": "#16A34A", "Moderate": "#EAB308", "High": "#EA580C", "Critical": "#DC2626"},
        title="Facility Strain Classification Breakdown",
    )
    st.plotly_chart(fig_pressure, use_container_width=True)

with col_facs:
    st.subheader("Highest Pressure Healthcare Facilities")
    high_press_df = facilities_pressure.sort_values("Pressure_Ratio", ascending=False)[
        ["Facility_ID", "Facility_Name", "Facility_Type", "Beds", "Estimated_Pop_Served", "Pressure_Ratio", "Pressure_Category"]
    ]
    st.dataframe(
        high_press_df.head(8),
        column_config={
            "Beds": st.column_config.NumberColumn(format="%d"),
            "Estimated_Pop_Served": st.column_config.NumberColumn(format="%d"),
            "Pressure_Ratio": st.column_config.NumberColumn(format="%.2fx"),
        },
        hide_index=True,
        use_container_width=True,
    )
