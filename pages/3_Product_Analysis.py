"""Product Analysis Page — Deep Dive into Product Leaderboards and Category Performance.
"""

import streamlit as st
import plotly.express as px
import pandas as pd

from services.ui_theme import (
    apply_theme,
    render_hero_banner,
    render_metric_card,
    apply_plotly_theme,
    COLOR_PRIMARY_BLUE,
    COLOR_PURPLE,
    COLOR_CARD,
    COLOR_BORDER,
    COLOR_DARK_NAVY,
)
from services.snowflake_service import (
    test_connection,
    get_snowflake_config,
    DEFAULT_DATABASE,
    DEFAULT_SCHEMA,
)
from services.analytics_service import (
    get_top_products,
    get_category_performance,
)

st.set_page_config(
    page_title="Product Analysis — DataLens Live",
    page_icon="📦",
    layout="wide",
)
apply_theme()

cfg = get_snowflake_config()
is_connected = False
if cfg:
    is_connected, _, _ = test_connection()

active_db = cfg.get("database", DEFAULT_DATABASE) if cfg else DEFAULT_DATABASE
active_sch = cfg.get("schema", DEFAULT_SCHEMA) if cfg else DEFAULT_SCHEMA

render_hero_banner(
    title="Product & Category Analytics",
    subtitle="Identify high-velocity items, top-grossing categories, and margin performance",
    data_source=f"{active_db}.{active_sch}",
    connected=is_connected
)

if not is_connected:
    st.warning("⚠️ **Live Snowflake Connection Required**")
    st.info("Configure your credentials in `.streamlit/secrets.toml` to access live Snowflake product analytics.")
    st.stop()

# Controls
c1, c2 = st.columns([1, 1])
with c1:
    selected_year = st.selectbox("Select Year", options=[2000, 1999, 1998, 2001, 2002], index=0)
with c2:
    top_n = st.slider("Number of Top Products", min_value=5, max_value=25, value=10, step=5)

# Section 1: Top Products
st.markdown(f"### 🏆 Top {top_n} Revenue Generating Products")
with st.spinner("Fetching top products from Snowflake..."):
    prod_df, prod_time, prod_err = get_top_products(limit=top_n, year=selected_year)

if prod_err:
    st.error(f"Error querying top products: {prod_err}")
elif prod_df is not None and not prod_df.empty:
    fig_top = px.bar(
        prod_df.sort_values("TOTAL_SALES", ascending=True),
        x="TOTAL_SALES",
        y="PRODUCT_NAME",
        orientation="h",
        color="CATEGORY",
        text_auto="$,.2s",
        title=f"Top {top_n} Products by Sales ({selected_year})",
        labels={"TOTAL_SALES": "Sales ($)", "PRODUCT_NAME": "Product Name"},
        color_discrete_sequence=[COLOR_PRIMARY_BLUE, COLOR_PURPLE, "#0284C7", "#38BDF8"]
    )
    apply_plotly_theme(fig_top, height=450)
    st.plotly_chart(fig_top, use_container_width=True)

    with st.expander("📋 View Product Details Table", expanded=False):
        t_df = prod_df.copy()
        t_df["TOTAL_SALES"] = t_df["TOTAL_SALES"].map("${:,.2f}".format)
        t_df["TOTAL_QUANTITY_SOLD"] = t_df["TOTAL_QUANTITY_SOLD"].map("{:,}".format)
        st.dataframe(t_df, use_container_width=True, hide_index=True)

# Section 2: Category Breakdown
st.markdown("### 🏷️ Category Performance & Profitability")
with st.spinner("Querying category breakdown..."):
    cat_df, cat_time, cat_err = get_category_performance(year=selected_year)

if cat_err:
    st.error(f"Error querying category performance: {cat_err}")
elif cat_df is not None and not cat_df.empty:
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        fig_cat_sales = px.bar(
            cat_df,
            x="CATEGORY",
            y="TOTAL_SALES",
            color="TOTAL_SALES",
            title=f"Total Sales by Category ({selected_year})",
            color_continuous_scale=[[0, "#BAE6FD"], [1, COLOR_PRIMARY_BLUE]],
        )
        apply_plotly_theme(fig_cat_sales, height=380)
        st.plotly_chart(fig_cat_sales, use_container_width=True)

    with col_c2:
        fig_cat_profit = px.bar(
            cat_df,
            x="CATEGORY",
            y="NET_PROFIT",
            color="NET_PROFIT",
            title=f"Net Profit by Category ({selected_year})",
            color_continuous_scale=[[0, "#E0E7FF"], [1, COLOR_PURPLE]],
        )
        apply_plotly_theme(fig_cat_profit, height=380)
        st.plotly_chart(fig_cat_profit, use_container_width=True)
