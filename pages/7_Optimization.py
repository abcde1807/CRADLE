"""
CRADLE Dashboard - Page 7: Optimization & Decision Robustness
Phase 3 Advanced Decision Science:
1. Maximal Covering Location Problem (MCLP) Integer Programming Optimizer
2. Budget Allocation Scenarios
3. AHP Physical Site Suitability
4. Cross-Regime Sensitivity Analysis
5. Adaptive Infrastructure Planning Score (AIPS) Robustness Index
"""

import streamlit as st
import geopandas as gpd
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium

import config
from app import load_cached_system_data
from src.candidate_generator import CandidateLocationGenerator
from src.candidate_ranking import CandidateRanker
from src.ahp import AHPSuitabilityModel
from src.mclp import MCLPOptimizer
from src.sensitivity import SensitivityAnalyzer
from src.aips import AIPSScorer

st.set_page_config(page_title="Optimization & Robustness | CRADLE", page_icon="⚡", layout="wide")

selected_city = st.session_state.get("selected_city", config.DEFAULT_CITY)
city_cfg = config.get_city_config(selected_city)

st.title(f"⚡ Optimization, Budget Scenarios & AIPS Robustness: {city_cfg['city_name']}")
st.caption(f"Phase 3 Decision Analytics in {city_cfg['city_name']} ({city_cfg['admin_body']}): Solves integer programs for optimal multi-site allocation and evaluates recommendation stability.")

wards_gdf, facilities_gdf = load_cached_system_data(selected_city)


@st.cache_data(show_spinner="Generating and evaluating candidate network...")
def get_base_candidates(city_key):
    w_gdf, f_gdf = load_cached_system_data(city_key)
    gen = CandidateLocationGenerator()
    cands = gen.generate_candidates(w_gdf, f_gdf)
    ranker = CandidateRanker()
    ranked = ranker.rank_candidates(cands, w_gdf, f_gdf)
    ahp = AHPSuitabilityModel()
    return ahp.evaluate_candidates(ranked, w_gdf)


candidates_gdf = get_base_candidates(selected_city)

tabs = st.tabs(["🎯 MCLP Mathematical Optimizer", "💰 Budget Scenarios", "📐 AHP Physical Suitability", "🔬 Sensitivity & AIPS Robustness"])

# -------------------------------------------------------------
# TAB 1: MCLP OPTIMIZER
# -------------------------------------------------------------
with tabs[0]:
    st.subheader("Maximal Covering Location Problem (MCLP)")
    st.markdown("""
    Formulates a binary integer linear program solved via `PuLP`:
    $$\max \sum_{i \in I} w_i y_i \quad \\text{s.t.} \quad \sum_{j \in N_i} x_j \ge y_i, \quad \sum_{j \in J} x_j = p$$
    Where demand weight $w_i = \text{Population}_i \\times \text{Gap Score}_i$ prioritizes high-need wards.
    """)

    opt_col1, opt_col2 = st.columns([1, 1])
    with opt_col1:
        num_facs = st.slider("Number of Facilities to Site (p):", 1, 10, 5, 1)
    with opt_col2:
        cov_rad = st.select_slider("Service Catchment Radius R (km):", options=[2.0, 3.0, 4.0, 5.0], value=3.0)

    mclp = MCLPOptimizer()
    mclp_res = mclp.solve_mclp(
        candidates_gdf=candidates_gdf,
        wards_gdf=wards_gdf,
        num_facilities=num_facs,
        coverage_radius_km=cov_rad,
    )

    # Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Solver Status", f"{mclp_res['status']}")
    m2.metric("Optimal Sites Selected", f"{mclp_res['num_facilities_selected']} Facilities")
    m3.metric("System Population Covered", f"{mclp_res['total_population_covered']:,} Pop", f"{mclp_res['percentage_population_covered']}% Coverage")
    m4.metric("High-Gap Wards Reached", f"{mclp_res['high_gap_wards_covered']} Wards", "Needs Remediated")

    st.markdown("---")

    col_mclp_map, col_mclp_list = st.columns([3, 2])

    with col_mclp_map:
        st.subheader("Optimal Siting Configuration Map")
        sel_cands_gdf = mclp_res["selected_candidates_gdf"]

        m_opt = folium.Map(location=city_cfg["center"], zoom_start=11, tiles="OpenStreetMap")

        # Plot all candidates in grey
        for _, cand in candidates_gdf.iterrows():
            folium.CircleMarker(
                location=[cand["Latitude"], cand["Longitude"]],
                radius=2,
                color="#94A3B8",
                fill=True,
                fill_opacity=0.4,
            ).add_to(m_opt)

        # Plot selected optimal candidates with buffers
        for _, sc in sel_cands_gdf.iterrows():
            folium.Marker(
                location=[sc["Latitude"], sc["Longitude"]],
                popup=f"<b>MCLP Selected: {sc['Candidate_ID']}</b><br>Ward: {sc['Ward_Name']}<br>Score: {sc['Candidate_Score']:.1f}",
                icon=folium.Icon(color="red", icon="star"),
            ).add_to(m_opt)

            folium.Circle(
                location=[sc["Latitude"], sc["Longitude"]],
                radius=cov_rad * 1000.0,
                color="#DC2626",
                fill=True,
                fill_opacity=0.15,
            ).add_to(m_opt)

        st_folium(m_opt, width=None, height=450)

    with col_mclp_list:
        st.subheader("Optimal Candidate Portfolio")
        st.dataframe(
            sel_cands_gdf[["MCLP_Rank", "Candidate_ID", "Ward_Name", "Zone", "Candidate_Score", "Population_Covered", "Recommendation"]],
            column_config={
                "MCLP_Rank": "Order",
                "Candidate_Score": st.column_config.NumberColumn(format="%.1f"),
                "Population_Covered": st.column_config.NumberColumn(format="%d"),
            },
            hide_index=True,
            use_container_width=True,
        )

        st.info(f"💡 **Coverage Efficiency:** siting {num_facs} strategically placed facilities covers **{mclp_res['percentage_population_covered']}%** of the metropolitan population.")


# -------------------------------------------------------------
# TAB 2: BUDGET SCENARIOS
# -------------------------------------------------------------
with tabs[1]:
    st.subheader("💰 Capital Budget Allocation Scenarios")
    st.markdown("Compares marginal returns on population coverage across standard municipal budget allocations:")

    budget_cols = st.columns(3)
    b_data = []

    for bname, bcfg in config.BUDGET_SCENARIOS.items():
        res = mclp.solve_mclp(
            candidates_gdf=candidates_gdf,
            wards_gdf=wards_gdf,
            num_facilities=bcfg["max_facilities"],
            coverage_radius_km=3.0,
            budget_crores=bcfg["budget_crores"],
        )
        b_data.append({
            "Scenario": bname,
            "Budget (₹ Cr)": bcfg["budget_crores"],
            "Facilities Built": res["num_facilities_selected"],
            "Facility Type": bcfg["preferred_type"],
            "Pop Covered": res["total_population_covered"],
            "Coverage %": res["percentage_population_covered"],
            "Remaining Underserved": res["remaining_underserved_population"],
        })

    budget_df = pd.DataFrame(b_data)

    st.dataframe(
        budget_df,
        column_config={
            "Budget (₹ Cr)": st.column_config.NumberColumn(format="₹%.1f Cr"),
            "Pop Covered": st.column_config.NumberColumn(format="%d"),
            "Coverage %": st.column_config.NumberColumn(format="%.1f%%"),
            "Remaining Underserved": st.column_config.NumberColumn(format="%d"),
        },
        hide_index=True,
        use_container_width=True,
    )

    fig_budget = px.bar(
        budget_df,
        x="Scenario",
        y="Pop Covered",
        color="Scenario",
        text="Coverage %",
        title="Population Covered by Capital Budget Scenario",
        labels={"Pop Covered": "Population Covered (Residents)"},
    )
    st.plotly_chart(fig_budget, use_container_width=True)


# -------------------------------------------------------------
# TAB 3: AHP SUITABILITY
# -------------------------------------------------------------
with tabs[2]:
    st.subheader("📐 AHP Multi-Criteria Site Suitability Analysis")
    st.markdown("""
    > [!IMPORTANT]
    > **CRADLE Core Design Principle:** **Gap Score and Suitability Score remain strictly separated.**  
    > - **Gap Score** answers: *"Where is the healthcare deficit greatest?"* (Demand/Need)  
    > - **AHP Suitability** answers: *"Where is the physical ground suitable for a hospital?"* (Supply/Site Feasibility)
    """)

    ahp = AHPSuitabilityModel()
    pairwise_mat = ahp.create_pairwise_matrix()
    weights_dict, cr, is_consistent = ahp.compute_weights(pairwise_mat)

    c_ahp1, c_ahp2 = st.columns([1, 1])
    with c_ahp1:
        st.markdown(f"**Consistency Ratio (CR):** `{cr:.4f}` ({'✅ Consistent (CR < 0.10)' if is_consistent else '❌ Inconsistent'})")
        ahp_weights_df = pd.DataFrame(list(weights_dict.items()), columns=["Criterion", "Weight"])
        fig_ahp = px.pie(ahp_weights_df, names="Criterion", values="Weight", title="AHP Criteria Priority Weights", hole=0.4)
        st.plotly_chart(fig_ahp, use_container_width=True)

    with c_ahp2:
        st.subheader("Gap vs Suitability Quadrant")
        fig_quad = px.scatter(
            candidates_gdf,
            x="Gap_Score",
            y="AHP_Suitability_Score",
            color="Recommendation",
            hover_name="Candidate_ID",
            hover_data=["Ward_Name", "Zone", "Population_Covered"],
            title="Candidate Matrix: Healthcare Need (Gap) vs Site Suitability (AHP)",
            labels={"Gap_Score": "Healthcare Gap Score (Need)", "AHP_Suitability_Score": "AHP Physical Suitability"},
        )
        fig_quad.add_vline(x=60, line_dash="dash", line_color="red", annotation_text="High Need Threshold")
        fig_quad.add_hline(y=60, line_dash="dash", line_color="green", annotation_text="High Suitability Threshold")
        st.plotly_chart(fig_quad, use_container_width=True)


# -------------------------------------------------------------
# TAB 4: SENSITIVITY & AIPS ROBUSTNESS
# -------------------------------------------------------------
with tabs[3]:
    st.subheader("🔬 Sensitivity Analysis & Adaptive Planning Score (AIPS)")
    st.markdown("""
    A site recommendation is **robust** when it stays highly ranked across competing planning objectives  
    (e.g., Population-focused vs Capacity-focused vs Spatial Accessibility-focused).
    """)

    aips_scorer = AIPSScorer()
    aips_df = aips_scorer.compute_aips(candidates_gdf, wards_gdf, facilities_gdf)

    # Summary
    rob_counts = aips_df["Robustness_Category"].value_counts().to_dict()
    rc1, rc2, rc3, rc4 = st.columns(4)
    rc1.metric("Very Robust Sites", f"{rob_counts.get('Very Robust', 0)} Sites", "Stable across all regimes")
    rc2.metric("Robust Sites", f"{rob_counts.get('Robust', 0)} Sites", "Minor rank shifts")
    rc3.metric("Moderately Robust", f"{rob_counts.get('Moderately Robust', 0)} Sites", "Scenario-sensitive")
    rc4.metric("Sensitive Sites", f"{rob_counts.get('Sensitive', 0)} Sites", "Highly volatile rank")

    st.markdown("---")
    st.subheader("AIPS Candidate Robustness Ranking Table")

    st.dataframe(
        aips_df[[
            "AIPS_Rank", "Candidate_ID", "Ward_Name", "Zone", "Baseline_Rank",
            "Population-Focused Rank", "Capacity & Gap-Focused Rank", "Spatial Accessibility-Focused Rank",
            "AHP Scenario Rank", "Cross_Scenario_StdDev", "AIPS", "Robustness_Category"
        ]].head(25),
        column_config={
            "AIPS_Rank": "Rank",
            "AIPS": st.column_config.ProgressColumn(format="%.1f", min_value=0, max_value=100),
            "Cross_Scenario_StdDev": st.column_config.NumberColumn(format="±%.1f"),
        },
        hide_index=True,
        use_container_width=True,
    )

    # Download AIPS Table
    aips_csv_data = aips_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Export AIPS Robustness Rankings (CSV)",
        data=aips_csv_data,
        file_name="CRADLE_AIPS_Robustness_Rankings.csv",
        mime="text/csv",
    )
