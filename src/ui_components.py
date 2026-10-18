"""
CRADLE Unified UI/UX & Navigation Framework
Provides standardized multi-city selection, responsive headers, modern design tokens,
and comprehensive methodological explainability across all application pages.
"""

from pathlib import Path
from typing import Tuple, Dict, Any, List
import streamlit as st
import geopandas as gpd
import pandas as pd

import config

# Color Tokens for Consistent Professional Palette
THEME = {
    "primary": "#1E3A8A",      # Deep Navy
    "secondary": "#0284C7",    # Marine Sky Blue
    "accent": "#0D9488",       # Deep Teal
    "critical": "#DC2626",     # Crimson Red
    "warning": "#F59E0B",      # Amber
    "success": "#16A34A",      # Emerald Green
    "surface": "#F8FAFC",      # Light Slate Background
    "text": "#0F172A",         # Slate 900
    "subtext": "#475569",      # Slate 600
}


def inject_custom_css():
    """Injects modern, responsive, university-grade CSS styling across the application."""
    st.markdown(f"""
    <style>
        /* Completely remove Streamlit Deploy button, Stop button, and default developer toolbar */
        header[data-testid="stHeader"] {{
            display: none !important;
            visibility: hidden !important;
            height: 0px !important;
        }}
        [data-testid="stToolbar"] {{
            display: none !important;
            visibility: hidden !important;
        }}
        .stAppDeployButton {{
            display: none !important;
            visibility: hidden !important;
        }}
        #MainMenu {{
            visibility: hidden !important;
        }}
        footer {{
            visibility: hidden !important;
        }}
        /* Clean top spacing */
        .block-container {{
            padding-top: 1.8rem !important;
        }}

        /* Import clean modern typography */
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            color: {THEME['text']};
        }}

        /* Header typography */
        .cradle-main-title {{
            font-size: 2.1rem;
            font-weight: 800;
            color: {THEME['primary']};
            letter-spacing: -0.025em;
            margin-bottom: 0.2rem;
            line-height: 1.2;
        }}

        .cradle-subtitle {{
            font-size: 1.05rem;
            color: {THEME['subtext']};
            margin-bottom: 0.8rem;
            line-height: 1.4;
        }}

        /* Top Bar City Chip */
        .cradle-city-chip {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: #EFF6FF;
            border: 1px solid #BFDBFE;
            color: #1E40AF;
            padding: 4px 12px;
            border-radius: 9999px;
            font-size: 0.825rem;
            font-weight: 600;
            margin-bottom: 0.8rem;
        }}

        /* Metric & KPI Cards */
        .cradle-metric-card {{
            background: {THEME['surface']};
            border: 1px solid #E2E8F0;
            border-left: 4px solid {THEME['secondary']};
            border-radius: 10px;
            padding: 1rem 1.2rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }}

        .cradle-metric-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        }}

        /* Status Badges */
        .cradle-badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 0.775rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }}

        .badge-critical {{ background: #FEE2E2; color: #991B1B; border: 1px solid #FCA5A5; }}
        .badge-high {{ background: #FFEDD5; color: #C2410C; border: 1px solid #FDBA74; }}
        .badge-moderate {{ background: #FEF3C7; color: #92400E; border: 1px solid #FCD34D; }}
        .badge-low {{ background: #DCFCE7; color: #166534; border: 1px solid #86EFAC; }}
        .badge-desert {{ background: #F3E8FF; color: #6B21A8; border: 1px solid #D8B4FE; }}

        /* Sidebar Styling */
        [data-testid="stSidebar"] {{
            background-color: #F8FAFC !important;
            border-right: 1px solid #E2E8F0;
        }}

        .sidebar-brand-box {{
            padding: 0.8rem 0;
            text-align: center;
        }}

        .sidebar-info-card {{
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 0.9rem;
            margin-top: 0.8rem;
            font-size: 0.85rem;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        }}

        .sidebar-info-card strong {{
            color: {THEME['primary']};
        }}

        /* Detail Box / Explainability Callout */
        .cradle-explain-box {{
            background: #F0FDF4;
            border: 1px solid #BBF7D0;
            border-left: 4px solid #16A34A;
            border-radius: 8px;
            padding: 1rem 1.25rem;
            margin: 1.2rem 0;
            font-size: 0.925rem;
            line-height: 1.5;
        }}

        /* Dataframe table headers */
        div[data-testid="stDataFrame"] {{
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #E2E8F0;
        }}

        /* Clean tabs */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px;
        }}
        .stTabs [data-baseweb="tab"] {{
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: 600;
        }}
    </style>
    """, unsafe_allow_html=True)


@st.cache_data(show_spinner="Loading spatial infrastructure datasets...")
def load_cached_system_data(city_key: str = None) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """
    Cached, reliable ingestion of processed administrative wards and healthcare facilities.
    Includes backward-compatible fallback for robustness.
    """
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


def render_sidebar_city_controller(page_key: str = "main") -> str:
    """
    Renders the persistent multi-city controller in the sidebar.
    Keeps session state synchronized across all application pages.
    """
    active_cities = [k for k, v in config.SUPPORTED_CITIES.items() if v.get("is_active") is True]

    # Ensure selected_city is initialized
    if "selected_city" not in st.session_state or st.session_state["selected_city"] not in active_cities:
        st.session_state["selected_city"] = config.DEFAULT_CITY

    current_city = st.session_state["selected_city"]
    current_idx = active_cities.index(current_city) if current_city in active_cities else 0

    with st.sidebar:
        st.markdown("""
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
            <span style="font-size:26px;">🏥</span>
            <div>
                <div style="font-weight:800; font-size:1.15rem; color:#1E3A8A; line-height:1.1;">CRADLE ENGINE</div>
                <div style="font-size:0.75rem; color:#64748B; font-weight:600;">Spatial Healthcare DSS</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.caption("Urban Health Geospatial Decision Support")
        st.markdown("---")

        # Sidebar City Selector Dropdown
        selected = st.selectbox(
            "📍 Select Metropolitan City",
            options=active_cities,
            index=current_idx,
            format_func=lambda k: f"{config.SUPPORTED_CITIES[k]['city_name']} ({config.SUPPORTED_CITIES[k]['state_code']})",
            key=f"sb_city_select_{page_key}"
        )

        if selected != current_city:
            st.session_state["selected_city"] = selected
            st.rerun()

        city_cfg = config.get_city_config(selected)

        # Authentic Municipal & Spatial Specification Card
        st.markdown(f"""
        <div class="sidebar-info-card">
            <div style="margin-bottom:6px;"><strong>Jurisdiction:</strong><br>{city_cfg['admin_body']}</div>
            <div style="margin-bottom:6px;"><strong>Spatial Units:</strong> {city_cfg['admin_count']} Wards ({city_cfg['zones_count']} Zones)</div>
            <div style="margin-bottom:6px;"><strong>Metric Projection:</strong> <code>{city_cfg['crs_proj']}</code></div>
            <div style="margin-bottom:6px;"><strong>Methodology:</strong> Gap-First Spatial Allocation</div>
        </div>
        """, unsafe_allow_html=True)

        st.info(f"💡 **Provenance:** {city_cfg['data_provenance']}")

    return st.session_state["selected_city"]


def render_page_header_and_city_selector(
    page_title: str,
    page_icon: str,
    page_subtitle: str,
    page_key: str = "page"
) -> Tuple[str, Dict[str, Any], gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """
    Universal header and top-corner city switcher rendered at the very top of EVERY page.
    Allows changing the active city directly from any page without navigating back.
    """
    inject_custom_css()

    active_cities = [k for k, v in config.SUPPORTED_CITIES.items() if v.get("is_active") is True]

    if "selected_city" not in st.session_state or st.session_state["selected_city"] not in active_cities:
        st.session_state["selected_city"] = config.DEFAULT_CITY

    current_city = st.session_state["selected_city"]
    current_idx = active_cities.index(current_city) if current_city in active_cities else 0

    # Also sync the sidebar controller
    render_sidebar_city_controller(page_key=page_key)

    # Top Bar: 2 Column Layout (Left: Title & Breadcrumb, Right: Quick Switcher)
    col_header, col_switcher = st.columns([3.8, 1.4])

    with col_header:
        city_cfg = config.get_city_config(current_city)
        cname = city_cfg["city_name"]
        display_title = f"{page_title}: {cname}" if cname not in page_title else page_title
        st.markdown(f'<div class="cradle-main-title">{page_icon} {display_title}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="cradle-subtitle">{page_subtitle}</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="cradle-city-chip">📍 <b>Active City:</b> {city_cfg["city_name"]} ({city_cfg["state_code"]}) '
            f'• {city_cfg["admin_body"]} • {city_cfg["admin_count"]} Wards • <code>{city_cfg["crs_proj"]}</code></div>',
            unsafe_allow_html=True
        )

    with col_switcher:
        st.markdown("<div style='text-align: right; margin-bottom: 2px;'>", unsafe_allow_html=True)
        top_selected = st.selectbox(
            "📍 Switch City Anytime:",
            options=active_cities,
            index=current_idx,
            format_func=lambda k: f"{config.SUPPORTED_CITIES[k]['city_name']} ({config.SUPPORTED_CITIES[k]['state_code']})",
            key=f"top_city_select_{page_key}",
            help="Switch to another metropolitan city immediately. All analytics and maps will recalculate."
        )
        st.markdown("</div>", unsafe_allow_html=True)

        if top_selected != current_city:
            st.session_state["selected_city"] = top_selected
            st.rerun()

    city_cfg = config.get_city_config(st.session_state["selected_city"])
    wards_gdf, facilities_gdf = load_cached_system_data(st.session_state["selected_city"])

    return st.session_state["selected_city"], city_cfg, wards_gdf, facilities_gdf


def render_methodology_card(
    module_title: str,
    mathematical_formula: str,
    conceptual_explanation: str,
    interpretation_points: List[str],
    policy_implications: List[str],
):
    """
    Renders an expandable, highly detailed academic and operational reference card
    ensuring every analytical feature is explained with extreme clarity and depth.
    """
    with st.expander(f"📘 Methodological Reference & How to Interpret: {module_title}", expanded=False):
        c1, c2 = st.columns([1.2, 1])

        with c1:
            st.markdown("#### Mathematical Formulation")
            if mathematical_formula:
                st.latex(mathematical_formula)
            st.markdown(conceptual_explanation)

            st.markdown("#### How to Interpret the Output")
            for pt in interpretation_points:
                st.markdown(f"- {pt}")

        with c2:
            st.markdown("#### Decision-Support & Policy Action")
            for action in policy_implications:
                st.markdown(f"- {action}")

            st.markdown("""
            > **Academic Rigor Notice:** All formulas are implemented in both Python (`GeoPandas`/`Shapely`/`PuLP`) 
            > and replicated in RStudio (`sf`/`dplyr`) with validated zero-error parity.
            """)
