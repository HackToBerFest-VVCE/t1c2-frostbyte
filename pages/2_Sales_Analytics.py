"""
Sales Analytics Page for DataLens.
Provides deep-dive sales reporting, multi-channel breakdowns, category filters,
and interactive visualisations.
"""

import streamlit as st
import pandas as pd
from utils.config import get_custom_css, COLORS, APP_NAME
from components.sidebar import render_sidebar
from components.metric_cards import render_demo_banner
from components.charts import (
    render_sales_trend_chart,
    render_category_bar_chart,
    render_channel_comparison_chart,
)
from services.analytics_service import analytics_service
from utils.formatting import format_currency, format_number

# Page Config
st.set_page_config(
    page_title=f"Sales Analytics — {APP_NAME}",
    page_icon="📊",
    layout="wide",
)
st.markdown(get_custom_css(), unsafe_allow_html=True)
render_sidebar(active_page="Sales Analytics")

# Header
st.markdown(
    f"""
    <div>
        <h1 style="font-size: 2rem; font-weight: 800; color: {COLORS['text']}; margin: 0;">
            📊 Sales Analytics & Multi-Channel Performance
        </h1>
        <p style="font-size: 0.95rem; color: #64748B; margin-top: 4px; margin-bottom: 20px;">
            Analyze revenue generation across physical stores, digital web, and mail-order catalog channels.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Filter Bar (White Card)
categories = analytics_service.get_categories()

st.markdown(
    f"""
    <div class="datalens-card" style="padding: 16px 20px; margin-bottom: 20px;">
        <span style="font-size: 0.8rem; font-weight: 700; color: #64748B; text-transform: uppercase;">
            🔍 Filters & Slicers
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)

col_f1, col_f2 = st.columns(2)
with col_f1:
    selected_cat = st.selectbox("Product Category Filter", options=categories, index=0)
with col_f2:
    selected_year = st.selectbox("Calendar Year", options=["All Years", 2024, 2025], index=0)

year_val = None if selected_year == "All Years" else int(selected_year)

# Fetch data with filters
with st.spinner("Calculating sales analytics..."):
    data = analytics_service.get_sales_analytics(
        selected_category=selected_cat, year_filter=year_val
    )

# Mandatory Demo Warning Banner
render_demo_banner(data["is_demo"])

# KPI Metrics Summary Row
df_summary = data["summary"]
if not df_summary.empty:
    row = df_summary.iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""
            <div class="kpi-card" style="border-top-color: {COLORS['primary']};">
                <div class="kpi-label">Filtered Sales</div>
                <div class="kpi-value">{format_currency(row.get('total_sales', 0))}</div>
                <div class="kpi-subtext">Category: {selected_cat}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="kpi-card" style="border-top-color: {COLORS['highlight']};">
                <div class="kpi-label">Units Sold</div>
                <div class="kpi-value">{format_number(row.get('total_quantity', 0))}</div>
                <div class="kpi-subtext">Volume moved</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
            <div class="kpi-card" style="border-top-color: #0284C7;">
                <div class="kpi-label">Transactions</div>
                <div class="kpi-value">{format_number(row.get('total_transactions', 0))}</div>
                <div class="kpi-subtext">Order line items</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f"""
            <div class="kpi-card" style="border-top-color: #38BDF8;">
                <div class="kpi-label">Average Order Value</div>
                <div class="kpi-value">{format_currency(row.get('avg_order_value', 0))}</div>
                <div class="kpi-subtext">Revenue per transaction</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

# Visualisations Row
col_c1, col_c2 = st.columns([3, 2])

with col_c1:
    st.markdown(
        f"""
        <div class="datalens-card">
            <div class="section-title">📈 Sales Over Time (Monthly Trend)</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    fig_monthly = render_sales_trend_chart(data["monthly"])
    st.plotly_chart(fig_monthly, use_container_width=True)

with col_c2:
    st.markdown(
        f"""
        <div class="datalens-card">
            <div class="section-title">🌐 Multi-Channel Revenue Comparison</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    fig_chan = render_channel_comparison_chart(data["channels"])
    st.plotly_chart(fig_chan, use_container_width=True)

st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

# Product-Level Breakdown Table
st.markdown(
    f"""
    <div class="datalens-card">
        <div class="section-title">📋 Product-Level Performance Details</div>
        <p style="font-size: 0.85rem; color: #64748B; margin-bottom: 14px;">
            Detailed sales metrics, revenue contributions, and unit pricing per merchandise SKU.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

df_prod = data["products"]
if not df_prod.empty:
    st.dataframe(df_prod, use_container_width=True)
    csv = df_prod.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Export Sales Breakdown CSV",
        data=csv,
        file_name="sales_analytics_breakdown.csv",
        mime="text/csv",
    )
else:
    st.info("No records found for the selected category filter.")
