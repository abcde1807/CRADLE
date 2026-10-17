"""
CRADLE Dashboard - Page 1: Multi-City Infrastructure Overview
Zone-level healthcare and demographic indicators, facility distributions,
interactive spatial overview, and cross-city benchmarking.
"""

import streamlit as st
import geopandas as gpd
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium

import config
from app import load_cached_system_data

st.set_page_config(page_title="Overview | CRADLE", page_icon="🗺️", layout="wide")

selected_city = st.session_state.get("selected_city", config.DEFAULT_CITY)
city_cfg = config.get_city_config(selected_city)

st.title(f"🏙️ {city_cfg['city_name']} Healthcare Infrastructure Overview")
st.caption(f"Administrative Authority: {city_cfg['admin_body']} ({city_cfg['state_name']}) | Metric Projection: {city_cfg['crs_proj']}")

wards_gdf, facilities_gdf = load_cached_system_data(selected_city)

tab1, tab2 = st.tabs([f"📍 {city_cfg['city_name']} Detailed Profile", "🌐 Cross-City Comparative Benchmarking"])

# ------------------------------------------------------------------------------
# TAB 1: Selected City Detailed Profile
# ------------------------------------------------------------------------------
with tab1:
    # 1. Zone Aggregations
    zone_summary = wards_gdf.groupby("Zone").agg(
        Wards=("Ward_ID", "count"),
        Population=("Population", "sum"),
        Area_km2=("Area_km2", "sum") if "Area_km2" in wards_gdf.columns else ("Ward_ID", lambda x: 10.0),
        Facilities=("Healthcare_Facilities", "sum"),
        Beds=("Hospital_Beds", "sum"),
        Doctors=("Total_Doctors", "sum") if "Total_Doctors" in wards_gdf.columns else ("Ward_ID", lambda x: 0),
        Critical_Wards=("Priority_Category", lambda x: (x == "Critical").sum()),
        Desert_Wards=("Healthcare_Desert", "sum"),
    ).reset_index()

    safe_pop = zone_summary["Population"].replace(0, 1)
    zone_summary["Beds_per_1000"] = ((zone_summary["Beds"] / safe_pop) * 1000).round(2)
    if "Area_km2" in zone_summary.columns:
        zone_summary["Pop_Density"] = (zone_summary["Population"] / zone_summary["Area_km2"].replace(0, 1)).round(1)

    # KPI Cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Population", f"{wards_gdf['Population'].sum():,}")
    c2.metric("Total Inpatient Beds", f"{wards_gdf['Hospital_Beds'].sum():,}")
    pub_count = (facilities_gdf['Ownership'] == 'Public').sum() if 'Ownership' in facilities_gdf.columns else len(facilities_gdf) // 2
    priv_count = len(facilities_gdf) - pub_count
    c3.metric("Public Healthcare Posts", f"{pub_count}")
    c4.metric("Private Healthcare Centres", f"{priv_count}")

    st.markdown("---")

    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader(f"Interactive Infrastructure Map ({city_cfg['city_name']})")
        color_opts = ["Population_Density", "Hospital_Beds", "Beds_per_1000", "Nearest_Hospital_Distance"]
        valid_opts = [c for c in color_opts if c in wards_gdf.columns]
        map_layer = st.selectbox("Color Wards By:", valid_opts, index=0)

        m = folium.Map(location=city_cfg["center"], zoom_start=11, tiles="OpenStreetMap")

        folium.Choropleth(
            geo_data=wards_gdf.to_json(),
            name=map_layer,
            data=wards_gdf,
            columns=["Ward_ID", map_layer],
            key_on="feature.properties.Ward_ID",
            fill_color="YlGnBu",
            fill_opacity=0.7,
            line_opacity=0.2,
            legend_name=map_layer.replace("_", " "),
        ).add_to(m)

        for _, fac in facilities_gdf.head(100).iterrows():
            is_hosp = "Hospital" in str(fac.get("Facility_Type", ""))
            folium.CircleMarker(
                location=[fac["Latitude"], fac["Longitude"]],
                radius=3 if not is_hosp else 6,
                color="red" if is_hosp else "blue",
                fill=True,
                fill_opacity=0.8,
                popup=f"<b>{fac.get('Facility_Name', 'Facility')}</b><br>Beds: {fac.get('Beds', 0)}",
            ).add_to(m)

        st_folium(m, width=None, height=460)

    with col_right:
        st.subheader("Zone-Level Healthcare Deficit Breakdown")
        st.dataframe(
            zone_summary[["Zone", "Wards", "Population", "Beds", "Beds_per_1000", "Critical_Wards", "Desert_Wards"]],
            hide_index=True,
            height=320,
        )

        fig = px.bar(
            zone_summary.sort_values(by="Critical_Wards", ascending=False),
            x="Zone",
            y="Critical_Wards",
            title=f"Critical Priority Wards by Zone ({city_cfg['city_name']})",
            color="Critical_Wards",
            color_continuous_scale="Reds",
        )
        st.plotly_chart(fig, width="stretch")

# ------------------------------------------------------------------------------
# TAB 2: Cross-City Comparative Benchmarking
# ------------------------------------------------------------------------------
with tab2:
    st.subheader("🌐 Cross-City Healthcare Infrastructure Benchmarking")
    st.markdown("Comparative spatial analytics across all active metropolitan jurisdictions:")

    bench_data = []
    active_cities = [k for k, v in config.SUPPORTED_CITIES.items() if v.get("is_active") is True]

    for ckey in active_cities:
        w_df, f_df = load_cached_system_data(ckey)
        ccfg = config.get_city_config(ckey)
        tot_pop = int(w_df["Population"].sum())
        tot_beds = int(w_df["Hospital_Beds"].sum())
        beds_k = round((tot_beds / max(tot_pop, 1)) * 1000, 2)
        mean_gap = round(float(w_df["Gap_Score"].mean()), 1)
        desert_count = int(w_df["Healthcare_Desert"].sum())
        desert_pct = round((desert_count / len(w_df)) * 100, 1)

        bench_data.append({
            "City": ccfg["city_name"],
            "State": ccfg["state_name"],
            "Admin Body": ccfg["admin_body"],
            "Wards": len(w_df),
            "Facilities": len(f_df),
            "Population": tot_pop,
            "Total Beds": tot_beds,
            "Beds / 1000 Pop": beds_k,
            "Mean Gap Score": mean_gap,
            "Desert Wards (%)": f"{desert_count} ({desert_pct}%)",
            "Projection CRS": ccfg["crs_proj"],
        })

    bench_df = pd.DataFrame(bench_data)
    st.dataframe(bench_df, hide_index=True, width="stretch")

    st.markdown("---")
    bc1, bc2 = st.columns(2)

    with bc1:
        fig_beds = px.bar(
            bench_df,
            x="City",
            y="Beds / 1000 Pop",
            color="City",
            title="Hospital Beds per 1,000 Population (vs WHO Benchmark 3.0)",
            text="Beds / 1000 Pop"
        )
        fig_beds.add_hline(y=3.0, line_dash="dash", line_color="green", annotation_text="WHO Target (3.0)")
        fig_beds.add_hline(y=1.5, line_dash="dot", line_color="orange", annotation_text="National Baseline (1.5)")
        st.plotly_chart(fig_beds, width="stretch")

    with bc2:
        fig_gap = px.bar(
            bench_df,
            x="City",
            y="Mean Gap Score",
            color="City",
            title="Average Healthcare Gap Score (0-100)",
            text="Mean Gap Score"
        )
        st.plotly_chart(fig_gap, width="stretch")
