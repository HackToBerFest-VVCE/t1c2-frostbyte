"""
Product Analysis Page for DataLens.
Provides SKU-level analysis, top 10 rankings by sales and volume, product search,
and catalog inventory comparisons.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from utils.config import get_custom_css, COLORS, APP_NAME
from components.sidebar import render_sidebar
from components.metric_cards import render_demo_banner
from components.charts import render_top_products_chart, BASE_LAYOUT
from services.analytics_service import analytics_service
from utils.formatting import format_currency, format_number

# Page Setup
st.set_page_config(
    page_title=f"Product Analysis — {APP_NAME}",
    page_icon="🏷️",
    layout="wide",
)
st.markdown(get_custom_css(), unsafe_allow_html=True)
render_sidebar(active_page="Product Analysis")

# Header
st.markdown(
    f"""
    <div>
        <h1 style="font-size: 2rem; font-weight: 800; color: {COLORS['text']}; margin: 0;">
            🏷️ Product & Inventory Analysis
        </h1>
        <p style="font-size: 0.95rem; color: #64748B; margin-top: 4px; margin-bottom: 20px;">
            Inspect SKU performance, compare sales revenue against units sold, and search catalog items.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Search and Filters Card
col_search, col_cat = st.columns([3, 2])
with col_search:
    search_keyword = st.text_input("Search Product or Brand:", placeholder="e.g. OLED, ApexTech, Parka, Espresso...")
with col_cat:
    categories = analytics_service.get_categories()
    chosen_cat = st.selectbox("Filter Category:", options=categories, index=0)

# Fetch Product Data
with st.spinner("Analyzing product performance..."):
    prod_data = analytics_service.get_product_analytics(
        search_term=search_keyword, category_filter=chosen_cat
    )

# Mandatory Demo Warning Banner
render_demo_banner(prod_data["is_demo"])

# Two Top 10 Comparison Charts
col_chart_sales, col_chart_qty = st.columns(2)

with col_chart_sales:
    st.markdown(
        f"""
        <div class="datalens-card">
            <div class="section-title">🏆 Top 10 Products by Revenue</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    df_sales = prod_data["top_sales"]
    if not df_sales.empty:
        fig_s = px.bar(
            df_sales.sort_values(by="total_sales", ascending=True),
            x="total_sales",
            y="product_name",
            orientation="h",
            color="total_sales",
            color_continuous_scale=[[0.0, "#A78BFA"], [1.0, COLORS["primary"]]],
            labels={"total_sales": "Total Sales (USD)", "product_name": "Product"},
        )
        fig_s.update_layout(**BASE_LAYOUT, coloraxis_showscale=False)
        fig_s.update_traces(
            hovertemplate="<b>%{y}</b><br>Sales: $%{x:,.2f}<extra></extra>",
            marker=dict(cornerradius=4),
        )
        st.plotly_chart(fig_s, use_container_width=True)
    else:
        st.info("No matching products found.")

with col_chart_qty:
    st.markdown(
        f"""
        <div class="datalens-card">
            <div class="section-title">📦 Top 10 Products by Volume (Units Sold)</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    df_qty = prod_data["top_qty"]
    if not df_qty.empty:
        fig_q = px.bar(
            df_qty.sort_values(by="units_sold", ascending=True),
            x="units_sold",
            y="product_name",
            orientation="h",
            color="units_sold",
            color_continuous_scale=[[0.0, "#BAE6FD"], [1.0, COLORS["highlight"]]],
            labels={"units_sold": "Units Sold", "product_name": "Product"},
        )
        fig_q.update_layout(**BASE_LAYOUT, coloraxis_showscale=False)
        fig_q.update_traces(
            hovertemplate="<b>%{y}</b><br>Units Sold: %{x:,}<extra></extra>",
            marker=dict(cornerradius=4),
        )
        st.plotly_chart(fig_q, use_container_width=True)
    else:
        st.info("No matching products found.")

st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

# Product Catalog & Performance Comparison Table
st.markdown(
    f"""
    <div class="datalens-card">
        <div class="section-title">📋 Product Catalog Performance Matrix</div>
        <p style="font-size: 0.85rem; color: #64748B; margin-bottom: 12px;">
            Complete list of retail inventory SKUs with unit pricing, lifetime unit sales, and gross revenue generated.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

df_catalog = prod_data["catalog"]
if not df_catalog.empty:
    st.dataframe(df_catalog, use_container_width=True)
    csv_cat = df_catalog.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download Product Matrix CSV",
        data=csv_cat,
        file_name="product_analysis_matrix.csv",
        mime="text/csv",
    )
else:
    st.info("No products match the filter criteria.")
