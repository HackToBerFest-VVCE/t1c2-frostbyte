"""
Sidebar Component for DataLens.
Displays branding, navigation guidance, connection status, and mode indicators.
"""

import streamlit as st
from services.snowflake_service import snowflake_service
from utils.config import COLORS, DEMO_WARNING_TEXT


def render_sidebar(active_page: str = "Dashboard"):
    """Renders the standard DataLens sidebar across all pages."""
    with st.sidebar:
        # 1. Logo & App Title
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 12px; padding: 10px 0 20px 0; border-bottom: 1px solid #E2E8F0; margin-bottom: 20px;">
                <div style="background: linear-gradient(135deg, {COLORS['primary']}, {COLORS['highlight']}); width: 44px; height: 44px; border-radius: 10px; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 10px rgba(65, 105, 225, 0.3);">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="11" cy="11" r="7" stroke="white" stroke-width="2.5"/>
                        <path d="M20 20L16 16" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
                        <circle cx="11" cy="11" r="2.5" fill="#BAE6FD"/>
                    </svg>
                </div>
                <div>
                    <h2 style="margin: 0; font-size: 1.4rem; font-weight: 800; color: {COLORS['text']}; line-height: 1.1;">DataLens</h2>
                    <span style="font-size: 0.72rem; color: #64748B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">AI Retail Analytics</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 2. Connection Status Card
        status = snowflake_service.get_connection_status()
        is_live = status["is_live"]

        status_bg = "#DCFCE7" if is_live else "#FEF3C7"
        status_color = "#166534" if is_live else "#92400E"
        status_dot = "#22C55E" if is_live else "#F59E0B"
        status_text = "Live Snowflake" if is_live else "Demo Mode"

        st.markdown(
            f"""
            <div style="background-color: {COLORS['card_bg']}; border: 1px solid {COLORS['border']}; border-radius: 10px; padding: 12px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <span style="font-size: 0.75rem; font-weight: 700; color: #64748B; text-transform: uppercase;">Connection</span>
                    <span style="background-color: {status_bg}; color: {status_color}; padding: 2px 8px; border-radius: 9999px; font-size: 0.7rem; font-weight: 700; display: inline-flex; align-items: center; gap: 4px;">
                        <span style="width: 6px; height: 6px; border-radius: 50%; background-color: {status_dot};"></span>
                        {status_text}
                    </span>
                </div>
                <div style="font-size: 0.78rem; color: {COLORS['text']}; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                    DB: <code style="font-size: 0.75rem; color: {COLORS['primary']};">{status['database']}</code>
                </div>
                <div style="font-size: 0.75rem; color: #64748B; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                    Schema: <code>{status['schema']}</code>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 3. Navigation Links Guide
        st.markdown(
            f"""
            <div style="font-size: 0.75rem; font-weight: 700; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; padding-left: 4px;">
                Navigation
            </div>
            """,
            unsafe_allow_html=True,
        )

        nav_items = [
            ("🏠 Dashboard", "Dashboard", "app.py"),
            ("💬 Ask DataLens", "Ask DataLens", "pages/1_Ask_DataLens.py"),
            ("📊 Sales Analytics", "Sales Analytics", "pages/2_Sales_Analytics.py"),
            ("🏷️ Product Analysis", "Product Analysis", "pages/3_Product_Analysis.py"),
            ("🔍 Data Explorer", "Data Explorer", "pages/4_Data_Explorer.py"),
            ("📜 Query History", "Query History", "pages/5_Query_History.py"),
            ("⚙️ Settings", "Settings", "pages/6_Settings.py"),
        ]

        for label, name, path in nav_items:
            is_selected = (name == active_page)
            active_style = f"background-color: #EEF2FF; color: {COLORS['primary']}; font-weight: 700; border-left: 3px solid {COLORS['primary']};" if is_selected else f"color: {COLORS['text']};"
            st.markdown(
                f"""
                <div style="{active_style} padding: 8px 12px; border-radius: 6px; margin-bottom: 4px; font-size: 0.88rem; display: flex; align-items: center; gap: 8px; transition: all 0.15s ease;">
                    <span>{label}</span>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("---")

        # 4. Quick Snowflake CoCo & AI Architecture Note
        st.markdown(
            f"""
            <div style="background-color: #F8FAFC; border-radius: 8px; padding: 12px; border: 1px dashed #CBD5E1; font-size: 0.75rem; color: #475569;">
                <div style="font-weight: 700; color: {COLORS['highlight']}; margin-bottom: 4px; display: flex; align-items: center; gap: 4px;">
                    ❄️ Architecture
                </div>
                <div>Runtime AI: <b>Qwen3-4B</b></div>
                <div>Dev Assistant: <b>Snowflake CoCo</b></div>
                <div style="margin-top: 6px; font-size: 0.7rem; color: #94A3B8;">
                    Separate runtime SQL generation from developer workspace tooling.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
