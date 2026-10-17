"""
CRADLE Dashboard - Page 2: Healthcare Gap Analyzer
The core gap-first analytical interface: 4-factor Healthcare Gap Score (0-100),
interactive choropleth map, priority classification, and natural explainability drill-down.
"""

import streamlit as st
import geopandas as gpd
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium

import config
from app import load_cached_system_data
from src.gap_analyzer import HealthcareGapAnalyzer
from src.intervention import InterventionEngine

st.set_page_config(page_title="Gap Analyzer | CRADLE", page_icon="⚖️", layout="wide")

selected_city = st.session_state.get("selected_city", config.DEFAULT_CITY)
city_cfg = config.get_city_config(selected_city)

st.title(f"⚖️ Healthcare Resource Gap Analyzer: {city_cfg['city_name']}")
st.caption(f"Quantifies ward-level healthcare service deficiency in {city_cfg['city_name']} ({city_cfg['admin_body']}) using the Gap-First methodology.")

wards_gdf, facilities_gdf = load_cached_system_data(selected_city)

# Sidebar: Configurable Gap Weights
with st.sidebar:
    st.header("⚙️ Gap Weight Calibration")
    st.markdown("Adjust relative importance of gap indicators:")

    w_pop = st.slider("Population Pressure", 0.0, 1.0, 0.30, 0.05)
    w_cap = st.slider("Capacity Deficit", 0.0, 1.0, 0.30, 0.05)
    w_dist = st.slider("Distance Gap", 0.0, 1.0, 0.25, 0.05)
    w_scarcity = st.slider("Facility Scarcity", 0.0, 1.0, 0.15, 0.05)

    tot_weight = w_pop + w_cap + w_dist + w_scarcity
    if tot_weight > 0:
        norm_weights = {
            "population_pressure": w_pop / tot_weight,
            "capacity_deficit": w_cap / tot_weight,
            "distance_gap": w_dist / tot_weight,
            "facility_scarcity": w_scarcity / tot_weight,
        }
    else:
        norm_weights = config.DEFAULT_GAP_WEIGHTS

    st.caption(f"Normalized Weights Total: {sum(norm_weights.values()):.2f}")

# Recompute gaps dynamically if weights adjusted
gap_engine = HealthcareGapAnalyzer(weights=norm_weights)
wards_analyzed = gap_engine.calculate_gap_scores(wards_gdf)

# High-level Gap Summary
c1, c2, c3, c4 = st.columns(4)
c1.metric("Average Gap Score", f"{wards_analyzed['Gap_Score'].mean():.1f} / 100")
c2.metric("Critical Priority Wards", f"{(wards_analyzed['Priority_Category'] == 'Critical').sum()}", delta="Score >= 75", delta_color="inverse")
c3.metric("High Priority Wards", f"{(wards_analyzed['Priority_Category'] == 'High').sum()}", delta="Score 50-75", delta_color="inverse")
c4.metric("Low / Well-Served Wards", f"{(wards_analyzed['Priority_Category'] == 'Low').sum()}", delta="Score < 25")

st.markdown("---")

col_map, col_details = st.columns([3, 2])

with col_map:
    st.subheader("Healthcare Gap Score Choropleth (0 - 100)")
    st.markdown("**Color Gradient:** Green (Low Gap) ➔ Yellow (Moderate) ➔ Orange (High) ➔ Red (Critical)")

    m = folium.Map(location=city_cfg["center"], zoom_start=11, tiles="OpenStreetMap")

    # Choropleth layer
    folium.Choropleth(
        geo_data=wards_analyzed.to_json(),
        name="Gap Score",
        data=wards_analyzed,
        columns=["Ward_ID", "Gap_Score"],
        key_on="feature.properties.Ward_ID",
        fill_color="YlOrRd",
        fill_opacity=0.7,
        line_opacity=0.3,
        legend_name="Healthcare Gap Score (0-100)",
    ).add_to(m)

    st_folium(m, width=None, height=480)

with col_details:
    st.subheader("🔍 Ward Explainability Diagnostic")

    # Ward selector
    ward_options = wards_analyzed.sort_values("Gap_Score", ascending=False)
    selected_ward_id = st.selectbox(
        "Select Ward to Inspect Diagnostic Drivers:",
        options=ward_options["Ward_ID"].tolist(),
        format_func=lambda wid: f"Ward {wid:03d} - {ward_options.set_index('Ward_ID').loc[wid, 'Zone']} (Gap: {ward_options.set_index('Ward_ID').loc[wid, 'Gap_Score']:.1f})",
    )

    selected_ward = ward_options.set_index("Ward_ID").loc[selected_ward_id]
    priority = selected_ward["Priority_Category"]
    badge_color = "#DC2626" if priority == "Critical" else ("#EA580C" if priority == "High" else "#16A34A")

    st.markdown(f"""
    <div style="background: #F1F5F9; padding: 15px; border-radius: 8px; border-left: 6px solid {badge_color};">
        <h3 style="margin-top:0; color:#0F172A;">{selected_ward['Ward_Name']} ({selected_ward['Zone']})</h3>
        <p style="margin-bottom:5px;"><b>Priority Category:</b> <span style="color:{badge_color}; font-weight:bold;">{priority}</span> | <b>Citywide Gap Rank:</b> #{int(selected_ward['Gap_Rank'])}</p>
        <p style="margin-bottom:0;"><b>Healthcare Gap Score:</b> <span style="font-size:1.4rem; font-weight:bold; color:{badge_color};">{selected_ward['Gap_Score']:.1f} / 100</span></p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### Indicator Breakdown (0-100 Scale)")
    comp_df = pd.DataFrame({
        "Component": ["Population Pressure", "Capacity Deficit", "Distance Gap", "Facility Scarcity"],
        "Normalized Score": [
            selected_ward["Pop_Pressure_Norm"],
            selected_ward["Capacity_Deficit_Norm"],
            selected_ward["Distance_Gap_Norm"],
            selected_ward["Facility_Scarcity_Norm"],
        ]
    })
    st.bar_chart(comp_df.set_index("Component"), height=180)

    st.markdown(f"**Primary Diagnostic:** {selected_ward['Primary_Issue']}")

    # Policy Intervention Recommendation
    interv = InterventionEngine.recommend_ward_intervention(selected_ward)
    st.info(f"📋 **Recommended Action:** {interv['Intervention']} ({interv['Facility_Type']})\n\n*{interv['Rationale']}*")

st.markdown("---")

# Ranking & Distribution section
c_dist1, c_dist2 = st.columns([1, 1])

with c_dist1:
    st.subheader("Distribution of Healthcare Gap Scores")
    fig_hist = px.histogram(
        wards_analyzed,
        x="Gap_Score",
        nbins=20,
        color="Priority_Category",
        color_discrete_map={"Low": "#22C55E", "Moderate": "#EAB308", "High": "#F97316", "Critical": "#EF4444"},
        title="Ward Gap Score Histogram",
        labels={"Gap_Score": "Healthcare Gap Score", "count": "Number of Wards"},
    )
    st.plotly_chart(fig_hist, use_container_width=True)

with c_dist2:
    st.subheader("Priority Classification Count")
    prior_counts = wards_analyzed["Priority_Category"].value_counts().reset_index()
    prior_counts.columns = ["Priority", "Count"]
    fig_pie = px.pie(
        prior_counts,
        names="Priority",
        values="Count",
        color="Priority",
        color_discrete_map={"Low": "#22C55E", "Moderate": "#EAB308", "High": "#F97316", "Critical": "#EF4444"},
        hole=0.4,
        title="Wards by Healthcare Priority Classification",
    )
    st.plotly_chart(fig_pie, use_container_width=True)

st.markdown("---")
st.subheader("📊 Complete Ward Healthcare Gap Rankings")

display_cols = [
    "Gap_Rank", "Ward_ID", "Ward_Name", "Zone", "Population", "Population_Density",
    "Healthcare_Facilities", "Hospital_Beds", "Beds_per_1000",
    "Nearest_Facility_Distance", "Nearest_Hospital_Distance", "Gap_Score", "Priority_Category", "Primary_Issue"
]

st.dataframe(
    wards_analyzed[display_cols].sort_values("Gap_Rank"),
    column_config={
        "Gap_Rank": "Rank",
        "Population": st.column_config.NumberColumn(format="%d"),
        "Beds_per_1000": st.column_config.NumberColumn(format="%.2f"),
        "Gap_Score": st.column_config.ProgressColumn(format="%.1f", min_value=0, max_value=100),
    },
    hide_index=True,
    use_container_width=True,
)

# Download CSV
csv_data = wards_analyzed[display_cols].to_csv(index=False).encode("utf-8")
st.download_button(
    label="📥 Export Ward Gap Rankings (CSV)",
    data=csv_data,
    file_name="CRADLE_Chennai_Ward_Gap_Rankings.csv",
    mime="text/csv",
)
