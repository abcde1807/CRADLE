import streamlit as st
import geopandas as gpd
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium

import config
from src.ui_components import (
    render_page_header_and_city_selector,
    render_methodology_card,
    load_cached_system_data,
)
from src.candidate_generator import CandidateLocationGenerator
from src.candidate_ranking import CandidateRanker
from src.scenario import ScenarioSimulator

st.set_page_config(page_title="Scenario Simulator | CRADLE", page_icon="🔬", layout="wide")

selected_city, city_cfg, wards_gdf, facilities_gdf = render_page_header_and_city_selector(
    page_title=f"Before vs After Scenario Simulator",
    page_icon="🔬",
    page_subtitle=f"Counterfactual spatial intervention simulation & quantitative deficit remediation assessment",
    page_key="scenario_sim",
)

render_methodology_card(
    module_title="Counterfactual Spatial Intervention Simulation Methodology",
    mathematical_formula=r"""
    \Delta G_i = G_i^{(\text{baseline})} - G_i^{(\text{simulated})}
    \\[8pt]
    d_{i,\text{hosp}}' = \min\left(d_{i,\text{hosp}}, \| \mathbf{x}_i - \mathbf{x}_{\text{new}} \|\right), \quad 
    B_i' = B_i + \text{Beds}_{\text{new}} \cdot \mathbb{I}\left(\| \mathbf{x}_i - \mathbf{x}_{\text{new}} \| \le R_{\text{catchment}}\right)
    """,
    conceptual_explanation="""
    The Scenario Simulator models the counterfactual spatial impact of constructing a new facility or augmenting capacity at a candidate site. 
    Upon placing a facility of type $T$ with bed capacity $B$ at coordinates $(x_{\text{new}}, y_{\text{new}})$, the engine recalculates centroid-to-hospital geodesic distances across all wards, redistributes bed capacity across the overlapping catchment radius $R_{\text{catchment}}$, and re-evaluates the 4-factor composite Gap Score.
    """,
    interpretation_points=[
        "**Delta Gap Score ($\\Delta G_i$):** Quantifies points of deficit alleviation achieved by the investment in ward $i$.",
        "**Desert Remediation:** A ward transitions out of 'Healthcare Desert' status when nearest hospital distance drops under 3.0 km or local bed capacity surpasses 1.0 bed per 1,000 residents.",
        "**Priority Category Transitions:** Visualizes how many wards successfully de-escalate from 'Critical' or 'High' into 'Moderate' or 'Low' priority tiers.",
        "**Newly Served Catchment Population:** Aggregates residents residing within the newly established service catchment radius."
    ],
    policy_implications=[
        "Conduct comparative simulation of candidate locations before finalizing land acquisitions to maximize population impact per rupee invested.",
        "Verify whether expanding bed capacity at an existing peripheral clinic yields greater spatial equity than establishing a greenfield hospital.",
        "Provide municipal standing committees with defensible Before-vs-After impact scorecards for public hearings."
    ]
)

# Generate or load candidates
@st.cache_data
def get_sim_candidates(city_key):
    w_gdf, f_gdf = load_cached_system_data(city_key)
    gen = CandidateLocationGenerator()
    cands = gen.generate_candidates(w_gdf, f_gdf)
    ranker = CandidateRanker()
    return ranker.rank_candidates(cands, w_gdf, f_gdf)

candidates_df = get_sim_candidates(selected_city)
top_candidates = candidates_df.head(50)

# Scenario Controls in Sidebar (Form avoids slider lag)
with st.sidebar.form("scenario_form"):
    st.header("🎛️ Intervention Parameters")

    selected_candidate_id = st.selectbox(
        "Target Candidate Location (Top 50 Sites):",
        options=top_candidates["Candidate_ID"].tolist(),
        format_func=lambda cid: f"{cid} - #{int(top_candidates.set_index('Candidate_ID').loc[cid, 'Rank'])} in {top_candidates.set_index('Candidate_ID').loc[cid, 'Ward_Name']} ({top_candidates.set_index('Candidate_ID').loc[cid, 'Zone']})",
    )

    fac_type = st.selectbox(
        "Facility Classification:",
        ["Community Health Centre (CHC)", "Urban Primary Health Centre (UPHC)", "Government Hospital", "General Hospital"],
        index=0,
    )

    bed_defaults = {"UPHC": 15, "CHC": 50, "Government Hospital": 200, "General Hospital": 500}
    clean_type = "UPHC" if "UPHC" in fac_type else ("CHC" if "CHC" in fac_type else ("General Hospital" if "General" in fac_type else "Government Hospital"))

    beds = st.slider("Target Inpatient Bed Capacity:", 10, 600, bed_defaults.get(clean_type, 50), 10)
    cov_radius = st.select_slider("Assumed Effective Service Catchment (km):", options=[2.0, 3.0, 5.0], value=3.0)

    st.markdown("---")
    st.header("⚖️ Scenario Gap Weights")
    w_pop = st.slider("Pop Pressure Weight", 0.0, 1.0, 0.30, 0.05)
    w_cap = st.slider("Capacity Weight", 0.0, 1.0, 0.30, 0.05)
    w_dist = st.slider("Distance Gap Weight", 0.0, 1.0, 0.25, 0.05)
    w_scarcity = st.slider("Scarcity Weight", 0.0, 1.0, 0.15, 0.05)

    run_button = st.form_submit_button("🚀 RUN SCENARIO SIMULATION", type="primary", use_container_width=True)

tot = w_pop + w_cap + w_dist + w_scarcity
scenario_weights_tuple = (
    ("population_pressure", round(w_pop / max(tot, 0.01), 3)),
    ("capacity_deficit", round(w_cap / max(tot, 0.01), 3)),
    ("distance_gap", round(w_dist / max(tot, 0.01), 3)),
    ("facility_scarcity", round(w_scarcity / max(tot, 0.01), 3)),
)

target_cand = top_candidates.set_index("Candidate_ID").loc[selected_candidate_id]

@st.cache_data(show_spinner="Executing counterfactual intervention simulation...")
def run_cached_simulation(city_key, cand_id, lat, lon, ftype, bed_count, radius_km, weights_tuple):
    w_gdf, f_gdf = load_cached_system_data(city_key)
    weights = dict(weights_tuple)
    simulator = ScenarioSimulator()
    from shapely.geometry import Point
    sim_w, sim_f, imp = simulator.simulate_facility_addition(
        wards_gdf=w_gdf,
        facilities_gdf=f_gdf,
        candidate_location=Point(lon, lat),
        facility_type=ftype,
        beds=bed_count,
        coverage_radius_km=radius_km,
        custom_weights=weights,
    )
    return sim_w, sim_f, imp

# Run cached simulation
sim_wards, sim_facs, impact = run_cached_simulation(
    selected_city,
    selected_candidate_id,
    float(target_cand["Latitude"]),
    float(target_cand["Longitude"]),
    clean_type,
    beds,
    cov_radius,
    scenario_weights_tuple
)

# Display Key Impact Metrics (BEFORE vs AFTER)
st.subheader("🎯 Quantitative Impact Assessment (Before vs After)")

c1, c2, c3, c4 = st.columns(4)
c1.metric(
    "Citywide Avg Gap Score",
    f"{impact['after_avg_gap']:.2f}",
    delta=f"-{impact['citywide_gap_reduction']:.2f} pts",
    delta_color="normal",
)
c2.metric(
    "Critical Priority Wards",
    f"{impact['after_critical_wards']}",
    delta=f"-{impact['critical_wards_reduced']} Wards",
    delta_color="inverse",
)
c3.metric(
    "Healthcare Desert Wards",
    f"{impact['after_desert_wards']}",
    delta=f"-{impact['desert_wards_resolved']} Deserts Remediated",
    delta_color="inverse",
)
c4.metric(
    "Newly Served Catchment Pop",
    f"{impact['population_newly_served']:,} Residents",
    delta=f"{impact['wards_reached_by_catchment']} Wards Touched",
)

st.markdown("---")

col_map, col_deltas = st.columns([3, 2])

with col_map:
    st.subheader("Spatial Gap Reduction Map (Delta Score)")
    st.markdown("🟡 **Yellow to Red:** Wards with Measurable Gap Reductions | 🟢 **Green Star:** New Sited Facility")

    m = folium.Map(location=[target_cand["Latitude"], target_cand["Longitude"]], zoom_start=12, tiles="OpenStreetMap")

    # Fast lightweight choropleth with only essential columns
    map_gdf = sim_wards[["Ward_ID", "Gap_Reduction", "geometry"]].copy()
    folium.Choropleth(
        geo_data=map_gdf.to_json(),
        name="Gap Reduction",
        data=map_gdf,
        columns=["Ward_ID", "Gap_Reduction"],
        key_on="feature.properties.Ward_ID",
        fill_color="YlGn",
        fill_opacity=0.7,
        line_opacity=0.3,
        legend_name="Gap Score Reduction (Points)",
    ).add_to(m)

    # Plot simulated facility
    folium.Marker(
        location=[target_cand["Latitude"], target_cand["Longitude"]],
        popup=f"<b>NEW FACILITY: {clean_type}</b><br>Beds: {beds}<br>Catchment: {cov_radius} km",
        icon=folium.Icon(color="green", icon="star"),
    ).add_to(m)

    # Plot catchment circle
    folium.Circle(
        location=[target_cand["Latitude"], target_cand["Longitude"]],
        radius=cov_radius * 1000.0,
        color="#10B981",
        fill=True,
        fill_opacity=0.15,
        tooltip=f"{cov_radius} km Service Reach",
    ).add_to(m)

    st_folium(m, width=None, height=480, returned_objects=[])

with col_deltas:
    st.subheader("Priority Transition Comparison")

    before_counts = wards_gdf["Priority_Category"].value_counts()
    after_counts = sim_wards["Priority_Category"].value_counts()

    cat_order = ["Critical", "High", "Moderate", "Low"]
    fig_comp = go.Figure(data=[
        go.Bar(name="Before Intervention", x=cat_order, y=[before_counts.get(c, 0) for c in cat_order], marker_color="#DC2626"),
        go.Bar(name="After Intervention", x=cat_order, y=[after_counts.get(c, 0) for c in cat_order], marker_color="#16A34A"),
    ])
    fig_comp.update_layout(barmode="group", height=280, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig_comp, use_container_width=True)

    if impact["max_ward_improvement"]:
        mwi = impact["max_ward_improvement"]
        st.success(f"🏆 **Most Improved Ward:** {mwi['Ward_Name']} (Ward {mwi['Ward_ID']})\n\n"
                   f"Gap dropped from **{mwi['Old_Gap']:.1f}** ➔ **{mwi['New_Gap']:.1f}** (**-{mwi['Delta']:.1f} pts**)")

    st.info(f"💡 **Healthcare Desert Alleviation:** Direct relief to **{impact['desert_pop_alleviated']:,} citizens** previously in healthcare desert conditions.")

st.markdown("---")
st.subheader("Top Benefiting Wards from This Intervention")

improved_wards_df = sim_wards[sim_wards["Gap_Reduction"] > 0.1].sort_values("Gap_Reduction", ascending=False)[
    ["Ward_ID", "Ward_Name", "Zone", "Population", "Beds_per_1000", "Nearest_Hospital_Distance", "Gap_Score", "Gap_Reduction", "Priority_Category"]
]

st.dataframe(
    improved_wards_df.head(15),
    column_config={
        "Population": st.column_config.NumberColumn(format="%d"),
        "Beds_per_1000": st.column_config.NumberColumn(format="%.2f"),
        "Nearest_Hospital_Distance": st.column_config.NumberColumn(format="%.1f km"),
        "Gap_Score": st.column_config.NumberColumn(format="%.1f"),
        "Gap_Reduction": st.column_config.ProgressColumn(format="-%.1f pts", min_value=0, max_value=max(improved_wards_df["Gap_Reduction"].max(), 1.0)),
    },
    hide_index=True,
    use_container_width=True,
)
