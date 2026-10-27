"""UI Theme and Styling Module for DataLens Live.

Applies the Hackathon Color Palette:
- Background: #EEF2FF
- Cards: #FFFFFF
- Primary blue: #4169E1
- Purple: #8B5CF6
- Light blue: #BAE6FD
- Dark navy text: #172554
- Borders: #E5E7EB
"""

import streamlit as st
import plotly.graph_objects as go

# Color Palette Constants
COLOR_BG = "#EEF2FF"
COLOR_CARD = "#FFFFFF"
COLOR_PRIMARY_BLUE = "#4169E1"
COLOR_PURPLE = "#8B5CF6"
COLOR_LIGHT_BLUE = "#BAE6FD"
COLOR_DARK_NAVY = "#172554"
COLOR_BORDER = "#E5E7EB"
COLOR_SUCCESS = "#10B981"
COLOR_DANGER = "#EF4444"
COLOR_WARNING = "#F59E0B"

# Plotly Color Palette Sequence
CHART_COLOR_SEQUENCE = [
    COLOR_PRIMARY_BLUE,
    COLOR_PURPLE,
    "#0284C7",  # Cerulean
    "#818CF8",  # Indigo light
    "#C084FC",  # Violet light
    "#38BDF8",  # Sky light
]


def apply_theme():
    """Inject global CSS rules to apply the DataLens Live color palette."""
    css = f"""
    <style>
        /* Base page styling */
        .stApp {{
            background-color: {COLOR_BG};
            color: {COLOR_DARK_NAVY};
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }}

        /* Headings */
        h1, h2, h3, h4, h5, h6 {{
            color: {COLOR_DARK_NAVY} !important;
            font-weight: 700 !important;
        }}

        /* Sidebar styling */
        section[data-testid="stSidebar"] {{
            background-color: {COLOR_CARD} !important;
            border-right: 1px solid {COLOR_BORDER};
        }}

        /* Buttons */
        .stButton > button {{
            background: linear-gradient(135deg, {COLOR_PRIMARY_BLUE} 0%, {COLOR_PURPLE} 100%) !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            padding: 0.5rem 1.25rem !important;
            transition: all 0.2s ease-in-out !important;
            box-shadow: 0 2px 4px rgba(65, 105, 225, 0.2) !important;
        }}
        .stButton > button:hover {{
            opacity: 0.92 !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 10px rgba(65, 105, 225, 0.35) !important;
        }}

        /* Secondary / Form inputs */
        .stTextInput > div > div > input,
        .stSelectbox > div > div,
        .stTextArea > div > div > textarea {{
            background-color: {COLOR_CARD} !important;
            color: {COLOR_DARK_NAVY} !important;
            border: 1px solid {COLOR_BORDER} !important;
            border-radius: 8px !important;
        }}

        /* Card container */
        .datalens-card {{
            background-color: {COLOR_CARD};
            border: 1px solid {COLOR_BORDER};
            border-radius: 12px;
            padding: 1.25rem;
            box-shadow: 0 2px 6px rgba(23, 37, 84, 0.04);
            margin-bottom: 1rem;
        }}

        /* KPI Metric Card */
        .metric-card {{
            background-color: {COLOR_CARD};
            border: 1px solid {COLOR_BORDER};
            border-radius: 12px;
            padding: 1.15rem 1.25rem;
            box-shadow: 0 2px 6px rgba(23, 37, 84, 0.05);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            position: relative;
            overflow: hidden;
        }}
        .metric-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 14px rgba(65, 105, 225, 0.12);
        }}
        .metric-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: linear-gradient(180deg, {COLOR_PRIMARY_BLUE}, {COLOR_PURPLE});
        }}
        .metric-title {{
            font-size: 0.825rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #64748B;
            font-weight: 600;
            margin-bottom: 0.35rem;
        }}
        .metric-value {{
            font-size: 1.75rem;
            font-weight: 700;
            color: {COLOR_DARK_NAVY};
            line-height: 1.2;
        }}
        .metric-subtitle {{
            font-size: 0.8rem;
            color: #64748B;
            margin-top: 0.35rem;
        }}

        /* Badges */
        .badge {{
            display: inline-block;
            padding: 0.25rem 0.65rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        .badge-success {{
            background-color: #DEF7EC;
            color: #03543F;
            border: 1px solid #BCF0DA;
        }}
        .badge-danger {{
            background-color: #FDE8E8;
            color: #9B1C1C;
            border: 1px solid #FBD5D5;
        }}
        .badge-info {{
            background-color: {COLOR_LIGHT_BLUE};
            color: {COLOR_DARK_NAVY};
            border: 1px solid #7DD3FC;
        }}
        .badge-purple {{
            background-color: #EDE9FE;
            color: #5B21B6;
            border: 1px solid #DDD6FE;
        }}

        /* Tab styling */
        button[data-baseweb="tab"] {{
            color: {COLOR_DARK_NAVY} !important;
            font-weight: 600 !important;
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
            border-bottom-color: {COLOR_PRIMARY_BLUE} !important;
            color: {COLOR_PRIMARY_BLUE} !important;
        }}

        /* Table styling */
        div[data-testid="stDataFrame"] {{
            background-color: {COLOR_CARD};
            border-radius: 10px;
            border: 1px solid {COLOR_BORDER};
            padding: 4px;
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def render_metric_card(title: str, value: str, subtitle: str = "", badge: str = None):
    """Render a KPI metric card with consistent styling."""
    badge_html = f'<span class="badge badge-purple" style="float: right;">{badge}</span>' if badge else ''
    html = f"""
    <div class="metric-card">
        {badge_html}
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
        {f'<div class="metric-subtitle">{subtitle}</div>' if subtitle else ''}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_hero_banner(title: str, subtitle: str, data_source: str = "SNOWFLAKE_SAMPLE_DATA.TPCDS_SF10TCL", connected: bool = False):
    """Render a modern top hero banner with connection status and data-source label."""
    status_class = "badge-success" if connected else "badge-danger"
    status_icon = "🟢 Connected" if connected else "🔴 Disconnected"
    
    html = f"""
    <div style="background: linear-gradient(135deg, {COLOR_CARD} 0%, #F8FAFC 100%);
                border: 1px solid {COLOR_BORDER};
                border-radius: 14px;
                padding: 1.5rem 1.75rem;
                margin-bottom: 1.5rem;
                box-shadow: 0 2px 8px rgba(23, 37, 84, 0.05);
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                gap: 1rem;">
        <div>
            <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.25rem;">
                <h1 style="margin: 0; font-size: 1.85rem; color: {COLOR_DARK_NAVY};">🔍 {title}</h1>
                <span class="badge badge-purple">DataLens Live</span>
            </div>
            <p style="margin: 0; color: #475569; font-size: 0.95rem;">{subtitle}</p>
        </div>
        <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 0.35rem;">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span style="font-size: 0.75rem; color: #64748B; font-weight: 500;">Status:</span>
                <span class="badge {status_class}">{status_icon}</span>
            </div>
            <div style="font-size: 0.78rem; color: #64748B;">
                Source: <strong style="color: {COLOR_PRIMARY_BLUE}; font-family: monospace;">{data_source}</strong>
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def apply_plotly_theme(fig: go.Figure, title: str = None, height: int = 400) -> go.Figure:
    """Format Plotly charts to match DataLens color palette."""
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor=COLOR_CARD,
        plot_bgcolor="#FAFAFD",
        title=dict(
            text=f"<b>{title}</b>" if title else None,
            font=dict(color=COLOR_DARK_NAVY, size=15),
            x=0.01,
            y=0.96,
        ),
        font=dict(
            family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif",
            color=COLOR_DARK_NAVY,
            size=12
        ),
        colorway=CHART_COLOR_SEQUENCE,
        margin=dict(l=40, r=30, t=50 if title else 25, b=40),
        height=height,
        xaxis=dict(
            gridcolor=COLOR_BORDER,
            linecolor=COLOR_BORDER,
            zerolinecolor=COLOR_BORDER,
        ),
        yaxis=dict(
            gridcolor=COLOR_BORDER,
            linecolor=COLOR_BORDER,
            zerolinecolor=COLOR_BORDER,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11)
        ),
    )
    return fig
