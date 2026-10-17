"""
CRADLE Dashboard - Page 4: Candidate Location Finder
Generates and ranks 500m x 500m spatial candidate sites in high-need wards,
evaluates multi-radius population catchment coverage, and delivers site-specific recommendations.
"""

import streamlit as st
import geopandas as gpd
import pandas as pd
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium

import config
from app import load_cached_system_data
from src.candidate_generator import CandidateLocationGenerator
from src.candidate_ranking import CandidateRanker
from src.coverage import PopulationCoverageAnalyzer
from src.intervention import InterventionEngine

st.set_page_config(page_title="Candidate Finder | CRADLE", page_icon="📍", layout="wide")

selected_city = st.session_state.get("selected_city", config.DEFAULT_CITY)
city_cfg = config.get_city_config(selected_city)

st.title(f"📍 Candidate Facility Location Finder: {city_cfg['city_name']}")
st.caption(f"Identifies and ranks candidate locations in deficit zones of {city_cfg['city_name']} ({city_cfg['admin_body']}) using gap severity and catchment coverage contribution.")

wards_gdf, facilities_gdf = load_cached_system_data(selected_city)

# Sidebar: Candidate Scoring Weights & Filters
with st.sidebar:
    st.header("⚙️ Candidate Scoring Weights")
    w_gap = st.slider("Gap Severity", 0.0, 1.0, 0.40, 0.05)
    w_pop = st.slider("Population Coverage", 0.0, 1.0, 0.30, 0.05)
    w_dist = st.slider("Existing Facility Distance", 0.0, 1.0, 0.20, 0.05)
    w_road = st.slider("Road Proximity", 0.0, 1.0, 0.10, 0.05)

    tot = w_gap + w_pop + w_dist + w_road
    cand_weights = {
        "gap_severity": w_gap / max(tot, 0.01),
        "population_coverage": w_pop / max(tot, 0.01),
        "facility_distance": w_dist / max(tot, 0.01),
        "road_proximity": w_road / max(tot, 0.01),
    }

    st.markdown("---")
    st.header("🎯 Spatial Grid Parameters")
    grid_size = st.select_slider("Grid Size (Meters)", options=[400, 500, 750, 1000], value=500)
    buffer_dist = st.slider("Buffer from Existing Facility (m)", 300, 1000, 600, 50)
    cov_radius = st.selectbox("Analysis Catchment Radius", [2.0, 3.0, 5.0], index=1)


@st.cache_data(show_spinner="Generating candidate grid in priority wards...")
def get_candidates(city_key, grid_m, buf_m, weights, radius_km):
    w_gdf, f_gdf = load_cached_system_data(city_key)
    gen = CandidateLocationGenerator(grid_size_meters=grid_m, buffer_meters=buf_m)
    cands = gen.generate_candidates(w_gdf, f_gdf)
    ranker = CandidateRanker(weights=weights)
    ranked = ranker.rank_candidates(cands, w_gdf, f_gdf, coverage_radius_m=radius_km * 1000.0)
    return ranked


ranked_candidates = get_candidates(selected_city, grid_size, buffer_dist, cand_weights, cov_radius)

# Summary KPIs
c1, c2, c3, c4 = st.columns(4)
c1.metric("Candidates Evaluated", f"{len(ranked_candidates)} Sites")
c2.metric("Highly Recommended", f"{(ranked_candidates['Recommendation'] == 'Highly Recommended').sum()} Sites", delta="Score >= 75")
c3.metric("Top Candidate Score", f"{ranked_candidates.iloc[0]['Candidate_Score']:.1f} / 100", f"{ranked_candidates.iloc[0]['Candidate_ID']}")
c4.metric("Max Catchment Reach", f"{ranked_candidates['Population_Covered'].max():,} Residents")

st.markdown("---")

col_map, col_details = st.columns([3, 2])

# Candidate selection
selected_cid = col_details.selectbox(
    "Select Candidate Site to Inspect:",
    options=ranked_candidates["Candidate_ID"].tolist(),
    format_func=lambda cid: f"{cid} - Rank #{int(ranked_candidates.set_index('Candidate_ID').loc[cid, 'Rank'])} in {ranked_candidates.set_index('Candidate_ID').loc[cid, 'Ward_Name']} (Score: {ranked_candidates.set_index('Candidate_ID').loc[cid, 'Candidate_Score']:.1f})",
)

sel_cand = ranked_candidates.set_index("Candidate_ID").loc[selected_cid]

with col_map:
    st.subheader("Candidate Locations & Spatial Coverage Map")
    st.markdown("🔵 **Blue Points:** Ranked Candidates | 🟢 **Green Pin:** Selected Candidate | 🟡 **Circle:** Catchment Buffer")

    m = folium.Map(location=[sel_cand["Latitude"], sel_cand["Longitude"]], zoom_start=12, tiles="OpenStreetMap")

    # Add all candidates as small markers
    for _, cand in ranked_candidates.iterrows():
        folium.CircleMarker(
            location=[cand["Latitude"], cand["Longitude"]],
            radius=3,
            color="#2563EB",
            fill=True,
            fill_opacity=0.7,
            tooltip=f"{cand['Candidate_ID']}: Score {cand['Candidate_Score']:.1f} ({cand['Recommendation']})",
        ).add_to(m)

    # Highlight selected candidate with larger marker and coverage buffer
    folium.Marker(
        location=[sel_cand["Latitude"], sel_cand["Longitude"]],
        popup=f"<b>Selected Site: {sel_cand.name}</b><br>Score: {sel_cand['Candidate_Score']:.1f}",
        icon=folium.Icon(color="green", icon="plus-sign"),
    ).add_to(m)

    # Add coverage circle
    folium.Circle(
        location=[sel_cand["Latitude"], sel_cand["Longitude"]],
        radius=cov_radius * 1000.0,
        color="#10B981",
        fill=True,
        fill_opacity=0.2,
        tooltip=f"{cov_radius} km Coverage Buffer ({sel_cand['Population_Covered']:,} pop covered)",
    ).add_to(m)

    st_folium(m, width=None, height=480)

with col_details:
    rec_tier = sel_cand["Recommendation"]
    rec_color = "#16A34A" if "Highly" in rec_tier else ("#2563EB" if "Recommended" in rec_tier else "#EAB308")

    st.markdown(f"""
    <div style="background: #F8FAFC; padding: 15px; border-radius: 8px; border-left: 6px solid {rec_color};">
        <h3 style="margin-top:0; color:#0F172A;">Candidate {sel_cand.name}</h3>
        <p><b>Rank:</b> #{int(sel_cand['Rank'])} | <b>Classification:</b> <span style="color:{rec_color}; font-weight:bold;">{rec_tier}</span></p>
        <p><b>Host Ward:</b> {sel_cand['Ward_Name']} ({sel_cand['Zone']}) | <b>Ward Gap Score:</b> {sel_cand['Gap_Score']:.1f}/100</p>
        <p style="margin-bottom:0;"><b>Overall Candidate Score:</b> <span style="font-size:1.4rem; font-weight:bold; color:{rec_color};">{sel_cand['Candidate_Score']:.1f} / 100</span></p>
    </div>
    """, unsafe_allow_html=True)

    # Radar/Bar Breakdown of scores
    sub_df = pd.DataFrame({
        "Criterion": ["Gap Severity (40%)", "Pop Coverage (30%)", "Fac Distance (20%)", "Road Proximity (10%)"],
        "Score": [
            sel_cand["Score_Gap_Severity"],
            sel_cand["Score_Pop_Coverage"],
            sel_cand["Score_Fac_Distance"],
            sel_cand["Score_Road_Proximity"],
        ]
    })
    st.bar_chart(sub_df.set_index("Criterion"), height=160)

    # Policy Recommendation from Intervention Engine
    interv_rec = InterventionEngine.recommend_candidate_intervention(sel_cand)
    st.markdown(f"**Recommended Facility:** `{interv_rec['Recommended_Facility_Type']}` ({interv_rec['Target_Bed_Capacity']} Beds)")
    st.markdown(f"**Estimated Capital Outlay:** `₹{interv_rec['Estimated_Capital_Expenditure_Cr']:.1f} Crores`")
    st.markdown(f"**Direct Catchment Population:** `{sel_cand['Population_Covered']:,} residents` across `{sel_cand['Wards_Reached']} wards`")

st.markdown("---")

# Multi-Radius Catchment breakdown for selected candidate
st.subheader(f"📊 Multi-Radius Catchment Reach: Candidate {sel_cand.name}")
cov_analyzer = PopulationCoverageAnalyzer()
multi_cov = cov_analyzer.evaluate_multi_radius_coverage(sel_cand.geometry, wards_gdf)

mc_cols = st.columns(3)
for idx, (rad_key, rad_data) in enumerate(multi_cov.items()):
    with mc_cols[idx]:
        st.metric(
            f"{rad_key} Service Radius",
            f"{rad_data['population_covered']:,} Pop",
            f"{rad_data['wards_reached_count']} Wards ({rad_data['high_gap_wards_covered']} High Gap)",
        )

st.markdown("---")
st.subheader("📋 Top Ranked Candidate Locations Table")

display_cols = [
    "Rank", "Candidate_ID", "Ward_ID", "Ward_Name", "Zone", "Candidate_Score",
    "Gap_Score", "Population_Covered", "Facility_Distance_km", "Recommendation"
]

st.dataframe(
    ranked_candidates[display_cols].head(25),
    column_config={
        "Candidate_Score": st.column_config.ProgressColumn(format="%.1f", min_value=0, max_value=100),
        "Population_Covered": st.column_config.NumberColumn(format="%d"),
        "Facility_Distance_km": st.column_config.NumberColumn(format="%.2f km"),
    },
    hide_index=True,
    use_container_width=True,
)

# Export Candidate Rankings
cand_csv = ranked_candidates[display_cols].to_csv(index=False).encode("utf-8")
st.download_button(
    "📥 Export Candidate Site Rankings (CSV)",
    data=cand_csv,
    file_name="CRADLE_Chennai_Candidate_Rankings.csv",
    mime="text/csv",
)
