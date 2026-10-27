"""
DataLens — Main Entrypoint & Dashboard Home.
An AI-powered retail analytics and intelligence platform.
"""

import streamlit as st
from utils.config import get_custom_css, COLORS, APP_NAME, APP_TAGLINE
from components.sidebar import render_sidebar
from components.metric_cards import render_kpi_cards, render_demo_banner
from components.charts import (
    render_category_bar_chart,
    render_sales_trend_chart,
    render_top_products_chart,
    render_channel_comparison_chart,
)
from services.analytics_service import analytics_service

# 1. Page Configuration
st.set_page_config(
    page_title=f"{APP_NAME} — Retail Intelligence Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Inject Custom Theme CSS
st.markdown(get_custom_css(), unsafe_allow_html=True)

# 3. Sidebar Navigation
render_sidebar(active_page="Dashboard")

# 4. Initialize Session State for Query History if not present
if "query_history" not in st.session_state:
    st.session_state["query_history"] = [
        {
            "timestamp": "2026-10-27 10:15:22",
            "question": "Which products generated the highest sales?",
            "status": "Success",
            "duration": 0.042,
            "sql": "SELECT i.i_product_name, SUM(s.ss_ext_sales_price) AS total_sales FROM store_sales s JOIN item i ON s.ss_item_sk = i.i_item_sk GROUP BY i.i_product_name ORDER BY total_sales DESC LIMIT 10",
            "rows": 10,
            "is_demo": True,
        },
        {
            "timestamp": "2026-10-27 09:40:11",
            "question": "How do store, web, and catalog sales compare?",
            "status": "Success",
            "duration": 0.038,
            "sql": "SELECT 'Store' AS channel, SUM(ss_ext_sales_price) AS sales FROM store_sales UNION ALL SELECT 'Web', SUM(ws_ext_sales_price) FROM web_sales UNION ALL SELECT 'Catalog', SUM(cs_ext_sales_price) FROM catalog_sales",
            "rows": 3,
            "is_demo": True,
        },
    ]

# 5. Header Section
st.markdown(
    f"""
    <div style="margin-bottom: 24px;">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
            <div>
                <h1 style="font-size: 2.2rem; font-weight: 800; color: {COLORS['text']}; margin: 0; line-height: 1.2;">
                    Retail Sales Intelligence
                </h1>
                <p style="font-size: 0.95rem; color: #64748B; margin-top: 4px; margin-bottom: 0;">
                    {APP_TAGLINE} powered by <b>Qwen3-4B</b> & <b>Snowflake</b>
                </p>
            </div>
            <div>
                <a href="/Ask_DataLens" target="_self" style="text-decoration: none;">
                    <button style="background: linear-gradient(135deg, {COLORS['primary']}, {COLORS['highlight']}); color: white; border: none; border-radius: 8px; padding: 10px 20px; font-weight: 700; font-size: 0.9rem; cursor: pointer; box-shadow: 0 4px 10px rgba(65, 105, 225, 0.25);">
                        ✨ Ask DataLens AI
                    </button>
                </a>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# 6. Fetch Dashboard Aggregates
with st.spinner("Loading retail analytics metrics..."):
    summary = analytics_service.get_dashboard_summary()

# 7. Exact Mandatory Demo Banner
render_demo_banner(summary["is_demo"])

# 8. Render 4 Core KPI Cards
render_kpi_cards(
    total_sales=summary["total_sales"],
    total_items=summary["total_items"],
    total_records=summary["total_records"],
    top_product_name=summary["top_product_name"],
    top_product_sales=summary["top_product_sales"],
)

st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

# 9. Interactive Visualisations Grid - Row 1
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.markdown(
        f"""
        <div class="datalens-card">
            <div class="section-title">📦 Category Performance</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    fig_cat = render_category_bar_chart(summary["df_category"])
    st.plotly_chart(fig_cat, use_container_width=True)

with col_chart2:
    st.markdown(
        f"""
        <div class="datalens-card">
            <div class="section-title">📈 Sales Trends Over Time</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    fig_trend = render_sales_trend_chart(summary["df_trends"])
    st.plotly_chart(fig_trend, use_container_width=True)

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# 10. Interactive Visualisations Grid - Row 2
col_chart3, col_chart4 = st.columns(2)

with col_chart3:
    st.markdown(
        f"""
        <div class="datalens-card">
            <div class="section-title">🏆 Top 10 Products by Sales</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    fig_top10 = render_top_products_chart(summary["df_top10"])
    st.plotly_chart(fig_top10, use_container_width=True)

with col_chart4:
    st.markdown(
        f"""
        <div class="datalens-card">
            <div class="section-title">🌐 Multi-Channel Sales Share</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    fig_channel = render_channel_comparison_chart(summary["df_channels"])
    st.plotly_chart(fig_channel, use_container_width=True)

st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

# 11. Quick Feature Links & Recent Queries Section
col_quick, col_rec = st.columns([1, 2])

with col_quick:
    st.markdown(
        f"""
        <div class="datalens-card" style="height: 100%;">
            <div class="section-title">⚡ Quick Navigation</div>
            <p style="font-size: 0.85rem; color: #64748B;">Explore deep analytical insights with prebuilt modules:</p>
            <div style="display: flex; flex-direction: column; gap: 10px; margin-top: 14px;">
                <a href="/Sales_Analytics" target="_self" style="text-decoration: none;">
                    <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 10px 14px; border-radius: 8px; font-weight: 600; font-size: 0.85rem; color: {COLORS['text']}; display: flex; align-items: center; justify-content: space-between;">
                        <span>📊 Sales Analytics</span>
                        <span style="color: {COLORS['primary']};">→</span>
                    </div>
                </a>
                <a href="/Product_Analysis" target="_self" style="text-decoration: none;">
                    <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 10px 14px; border-radius: 8px; font-weight: 600; font-size: 0.85rem; color: {COLORS['text']}; display: flex; align-items: center; justify-content: space-between;">
                        <span>🏷️ Product Analysis</span>
                        <span style="color: {COLORS['primary']};">→</span>
                    </div>
                </a>
                <a href="/Data_Explorer" target="_self" style="text-decoration: none;">
                    <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 10px 14px; border-radius: 8px; font-weight: 600; font-size: 0.85rem; color: {COLORS['text']}; display: flex; align-items: center; justify-content: space-between;">
                        <span>🔍 Data Explorer</span>
                        <span style="color: {COLORS['primary']};">→</span>
                    </div>
                </a>
                <a href="/Settings" target="_self" style="text-decoration: none;">
                    <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 10px 14px; border-radius: 8px; font-weight: 600; font-size: 0.85rem; color: {COLORS['text']}; display: flex; align-items: center; justify-content: space-between;">
                        <span>⚙️ Snowflake & AI Settings</span>
                        <span style="color: {COLORS['primary']};">→</span>
                    </div>
                </a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_rec:
    st.markdown(
        f"""
        <div class="datalens-card" style="height: 100%;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div class="section-title" style="margin: 0;">📜 Recent Queries</div>
                <a href="/Query_History" target="_self" style="font-size: 0.8rem; color: {COLORS['primary']}; font-weight: 600; text-decoration: none;">View all →</a>
            </div>
        """,
        unsafe_allow_html=True,
    )

    history = st.session_state.get("query_history", [])[:4]
    if history:
        for item in history:
            st.markdown(
                f"""
                <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px; margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 700; font-size: 0.88rem; color: {COLORS['text']};">{item['question']}</span>
                        <span style="background-color: #DCFCE7; color: #166534; font-size: 0.7rem; padding: 2px 8px; border-radius: 9999px; font-weight: 600;">{item['status']}</span>
                    </div>
                    <div style="font-size: 0.75rem; color: #94A3B8; margin-top: 4px; display: flex; gap: 14px;">
                        <span>🕒 {item['timestamp']}</span>
                        <span>⚡ {item['duration'] * 1000:.0f} ms</span>
                        <span>📄 {item.get('rows', 0)} rows</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("No queries executed yet. Head to 'Ask DataLens' to submit a question!")

    st.markdown("</div>", unsafe_allow_html=True)
