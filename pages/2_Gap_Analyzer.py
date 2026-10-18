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
from src.ui_components import (
    render_page_header_and_city_selector,
    render_methodology_card,
    load_cached_system_data,
    inject_custom_css
)
from src.gap_analyzer import HealthcareGapAnalyzer
from src.intervention import InterventionEngine

st.set_page_config(page_title="Gap Analyzer | CRADLE", page_icon="⚖️", layout="wide")

# Universal top-corner city switcher and header
selected_city, city_cfg, wards_gdf, facilities_gdf = render_page_header_and_city_selector(
    page_title=f"Healthcare Resource Gap Analyzer: {city_cfg['city_name'] if 'city_cfg' in locals() else 'Metro'}",
    page_icon="⚖️",
    page_subtitle=f"4-factor composite gap scoring (0-100), priority tiering, and explainability drill-down.",
    page_key="gap_analyzer"
)

# Sidebar: Configurable Gap Weights
with st.sidebar:
    st.markdown("### ⚙️ Gap Weight Calibration")
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
    st.subheader(f"Healthcare Gap Score Choropleth ({city_cfg['city_name']})")
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
        format_func=lambda wid: f"{ward_options.set_index('Ward_ID').loc[wid, 'Ward_Name']} - {ward_options.set_index('Ward_ID').loc[wid, 'Zone']} (Gap: {ward_options.set_index('Ward_ID').loc[wid, 'Gap_Score']:.1f})",
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
        title=f"Ward Gap Score Histogram ({city_cfg['city_name']})",
        labels={"Gap_Score": "Healthcare Gap Score", "count": "Number of Wards"},
    )
    st.plotly_chart(fig_hist, width="stretch")

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
        title=f"Wards by Healthcare Priority ({city_cfg['city_name']})",
    )
    st.plotly_chart(fig_pie, width="stretch")

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
    width="stretch",
)

# Download CSV
csv_data = wards_analyzed[display_cols].to_csv(index=False).encode("utf-8")
st.download_button(
    label=f"📥 Export {city_cfg['city_name']} Ward Gap Rankings (CSV)",
    data=csv_data,
    file_name=f"CRADLE_{city_cfg['city_name']}_Ward_Gap_Rankings.csv",
    mime="text/csv",
)

# Methodological Card
render_methodology_card(
    module_title="4-Factor Healthcare Gap Score & Diagnostic Explainability",
    mathematical_formula=r"\text{Gap Score}_i = \left( 0.30 \cdot P_i + 0.30 \cdot C_i + 0.25 \cdot D_i + 0.15 \cdot S_i \right) \times 100",
    conceptual_explanation="""
    The composite Gap Score (0–100) measures multidimensional urban healthcare deprivation:
    1. **Population Pressure ($P_i$):** $0.70 \times \text{Density Percentile} + 0.30 \times \text{Vulnerability Ratio}$ (Children & Elderly).
    2. **Capacity Deficit ($C_i$):** Shortfall relative to the WHO target of 3.0 hospital beds per 1,000 residents.
    3. **Distance Gap ($D_i$):** Normalized travel distance to nearest primary clinic (2.5km benchmark) and secondary hospital (5.0km benchmark).
    4. **Facility Scarcity ($S_i$):** Deficiency relative to the standard of 1.5 primary healthcare facilities per 10,000 residents.
    """,
    interpretation_points=[
        "**Score ≥ 75.0 (Critical):** Immediate intervention required; acute bed deficit compounded by spatial isolation.",
        "**Score 50.0–74.9 (High):** Substantial deficit; priority target for Primary Health Centre expansion.",
        "**Score 25.0–49.9 (Moderate):** Average urban service level with moderate localized pressure.",
        "**Score < 25.0 (Low):** Well-served administrative area meeting or exceeding national healthcare standards.",
    ],
    policy_implications=[
        "Prioritize capital funding for municipal wards appearing in the top 15% of the Gap Ranking.",
        "Use indicator breakdowns to determine whether an area needs physical beds vs. closer clinic proximity.",
        "Export ward gap tables for municipal budget defense hearings and urban master planning.",
    ]
)
