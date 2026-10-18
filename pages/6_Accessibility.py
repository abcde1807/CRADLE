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
)
from src.two_sfca import TwoSFCAAnalyzer
from src.accessibility import RoadNetworkAccessibility

st.set_page_config(page_title="Accessibility & 2SFCA | CRADLE", page_icon="🚗", layout="wide")

selected_city, city_cfg, wards_gdf, facilities_gdf = render_page_header_and_city_selector(
    page_title=f"Road Network & 2SFCA Spatial Accessibility",
    page_icon="🚗",
    page_subtitle=f"Floating catchment supply-demand equilibrium, distance decay kernels & road network isochrones",
    page_key="accessibility",
)

render_methodology_card(
    module_title="Two-Step Floating Catchment Area (2SFCA) & Isochrone Mechanics",
    mathematical_formula=r"""
    \text{Step 1 (Provider Bed-to-Demand Ratio): } R_j = \frac{S_j}{\sum_{k \in \{d_{kj} \le d_0\}} P_k \cdot f(d_{kj})}
    \\[8pt]
    \text{Step 2 (Accessible Bed Supply to Ward } i\text{): } A_i = \sum_{j \in \{d_{ij} \le d_0\}} R_j \cdot f(d_{ij})
    \\[8pt]
    \text{Decay Kernels: } f(d) = d^{-\beta} \text{ (Gravity)}, \quad f(d) = \exp\left(-\frac{d^2}{\beta^2}\right) \text{ (Gaussian)}, \quad f(d) = 1 \text{ (Binary)}
    """,
    conceptual_explanation="""
    Conventional straight-line distance ignores provider capacity congestion and competing demand from neighboring populations. 
    The Two-Step Floating Catchment Area (2SFCA) model resolves this by creating two interdependent spatial catchments: 
    First, it computes the ratio of hospital beds ($S_j$) to the distance-decayed population residing within travel threshold $d_0$. 
    Second, it aggregates all accessible provider ratios for each ward's centroid. 
    Isochrones model actual network driving times (5, 10, 15 mins) accounting for urban topological constraints.
    """,
    interpretation_points=[
        "**Score < 20 (Severely Deficient Access):** Population has acute bed scarcity even within driving distance due to massive surrounding population competition.",
        "**Score 60 - 100 (High / Very High Access):** Population is within reach of adequate, uncrowded bed capacity.",
        "**Distance Decay (β):** Friction factor capturing how willingness to travel drops with distance (β = 1.5 aligns with empirical urban Indian travel studies).",
        "**Catchment Threshold (d0):** The maximum radius (e.g. 4.0 km) within which residents feasibly seek primary and secondary healthcare."
    ],
    policy_implications=[
        "Deploy mobile medical units and outreach clinics to wards exhibiting high straight-line proximity but severe 2SFCA congestion deficits.",
        "Use isochrone contours to establish emergency trauma response centers guaranteeing sub-15-minute ambulance access.",
        "Avoid adding bed capacity to existing mega-hospitals that already experience diminishing returns from localized gridlock."
    ]
)

# 2SFCA Controls in Sidebar
with st.sidebar:
    st.header("⚙️ 2SFCA Model Parameters")
    d0_radius = st.slider("Catchment Threshold d0 (km):", 2.0, 8.0, 4.0, 0.5)
    decay_mode = st.selectbox("Distance Decay Kernel:", ["gravity", "gaussian", "binary"], index=0)
    gravity_beta = st.slider("Gravity Impedance β:", 1.0, 2.5, 1.5, 0.1)

    st.markdown("---")
    st.header("⏱️ Isochrone Center")
    city_zones = city_cfg.get("zones", [])
    zone_options = [z["zone_name"] for z in city_zones] if city_zones else sorted(wards_gdf["Zone"].dropna().unique().tolist())
    selected_node = st.selectbox(
        "Generate Isochrones Around Zone Center:",
        options=zone_options,
        index=0 if len(zone_options) > 0 else 0,
    )


@st.cache_data(show_spinner="Computing Two-Step Floating Catchment Area (2SFCA)...")
def run_2sfca_model(city_key, d0, decay, beta):
    w_gdf, f_gdf = load_cached_system_data(city_key)
    analyzer = TwoSFCAAnalyzer(catchment_radius_km=d0, decay_type=decay, gravity_beta=beta)
    return analyzer.calculate_accessibility(w_gdf, f_gdf)


wards_2sfca = run_2sfca_model(selected_city, d0_radius, decay_mode, gravity_beta)

# Summary KPIs
c1, c2, c3, c4 = st.columns(4)
c1.metric("Mean 2SFCA Access Score", f"{wards_2sfca['Two_SFCA_Norm'].mean():.1f} / 100")
c2.metric("Severely Deficient Wards", f"{(wards_2sfca['Accessibility_Tier'] == 'Severely Deficient Access').sum()} Wards", delta="Score < 20", delta_color="inverse")
c3.metric("High Access Wards", f"{(wards_2sfca['Accessibility_Tier'].isin(['High Access', 'Very High Access'])).sum()} Wards", delta="Score >= 60")
c4.metric("Catchment Radius d0", f"{d0_radius} km", f"{decay_mode.title()} decay")

st.markdown("---")

col_map, col_details = st.columns([3, 2])

with col_map:
    st.subheader("2SFCA Spatial Accessibility Map (0 - 100)")
    st.markdown("🟢 **Green:** High Spatial Supply-to-Demand | 🔴 **Red:** Severe Access Deficiency")

    m = folium.Map(location=city_cfg["center"], zoom_start=11, tiles="OpenStreetMap")

    folium.Choropleth(
        geo_data=wards_2sfca.to_json(),
        name="2SFCA Accessibility",
        data=wards_2sfca,
        columns=["Ward_ID", "Two_SFCA_Norm"],
        key_on="feature.properties.Ward_ID",
        fill_color="RdYlGn",
        fill_opacity=0.7,
        line_opacity=0.3,
        legend_name="2SFCA Healthcare Accessibility (0-100)",
    ).add_to(m)

    # Road Network Isochrones
    road_net = RoadNetworkAccessibility()

    # Find lat/lon for zone
    zone_wards = wards_gdf[wards_gdf["Zone"] == selected_node]
    if len(zone_wards) > 0:
        clat = float(zone_wards.geometry.centroid.y.mean())
        clon = float(zone_wards.geometry.centroid.x.mean())
    else:
        clat, clon = city_cfg["center"]

    isochrones_gdf = road_net.generate_isochrones(clat, clon, time_thresholds_min=[5, 10, 15])
    iso_colors = {5: "#22C55E", 10: "#EAB308", 15: "#3B82F6"}

    for _, iso in isochrones_gdf.iterrows():
        t = iso["Travel_Time_Min"]
        folium.GeoJson(
            iso.geometry.__geo_interface__,
            style_function=lambda x, col=iso_colors.get(t, "#999999"): {
                "fillColor": col,
                "color": col,
                "weight": 2,
                "fillOpacity": 0.2,
            },
            tooltip=f"{t}-Minute Driving Service Area",
        ).add_to(m)

    # Marker for isochrone center
    folium.Marker(
        location=[clat, clon],
        popup=f"Isochrone Focus: {selected_node}",
        icon=folium.Icon(color="darkblue", icon="info-sign"),
    ).add_to(m)

    st_folium(m, width=None, height=480)

with col_details:
    st.subheader("2SFCA Methodological Mechanics")
    st.markdown(r"""
    The **Two-Step Floating Catchment Area (2SFCA)** model calculates spatial accessibility by:
    1. **Step 1 (Provider to Population):**
       $$R_j = \frac{S_j}{\sum_{k \in \{d_{kj} \le d_0\}} P_k \cdot f(d_{kj})}$$
       For every hospital $j$, computes bed supply per unit distance-decayed population demand in catchment $d_0$.

    2. **Step 2 (Accessible Supply to Resident):**
       $$A_i = \sum_{j \in \{d_{ij} \le d_0\}} R_j \cdot f(d_{ij})$$
       For each ward $i$, sums all accessible provider ratios $R_j$ to yield composite accessibility.
    """)

    st.subheader("Accessibility Tier Distribution")
    tier_counts = wards_2sfca["Accessibility_Tier"].value_counts().reset_index()
    tier_counts.columns = ["Tier", "Wards"]
    fig_tier = px.bar(
        tier_counts,
        x="Tier",
        y="Wards",
        color="Tier",
        color_discrete_map={
            "Very High Access": "#15803D",
            "High Access": "#22C55E",
            "Moderate Access": "#EAB308",
            "Low Access": "#F97316",
            "Severely Deficient Access": "#DC2626",
        },
    )
    st.plotly_chart(fig_tier, use_container_width=True)

st.markdown("---")

# Straight-Line vs Road Network Travel Time Comparison
st.subheader("⏱️ Euclidean Distance vs Road Network Travel Time Comparison")
st.markdown("Illustrates why straight-line distance misjudges accessibility due to urban road congestion and network winding.")

sample_wards_comp = wards_2sfca.head(10).copy()
sample_wards_comp["Straight_Line_km"] = sample_wards_comp["Nearest_Hospital_Distance"]
sample_wards_comp["Est_Drive_Time_Min"] = [
    road_net.compute_travel_time(row["Centroid_Lat"], row["Centroid_Lon"], city_cfg["center"][0], city_cfg["center"][1])
    for _, row in sample_wards_comp.iterrows()
]

fig_scatter = px.scatter(
    sample_wards_comp,
    x="Straight_Line_km",
    y="Est_Drive_Time_Min",
    text="Ward_Name",
    size="Population",
    color="Two_SFCA_Norm",
    labels={
        "Straight_Line_km": "Straight-Line Distance to Hospital (km)",
        "Est_Drive_Time_Min": "Network Driving Travel Time (Minutes)",
        "Two_SFCA_Norm": "2SFCA Accessibility",
    },
    title="Straight-Line Distance vs Road Travel Time across Sample Wards",
    color_continuous_scale="Viridis",
)
fig_scatter.update_traces(textposition="top center")
st.plotly_chart(fig_scatter, use_container_width=True)
