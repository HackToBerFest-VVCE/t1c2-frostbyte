"""
Data Explorer Page for DataLens.
Allows safe inspection of Snowflake database schema, retail tables, column definitions,
and limited row previews without running unrestricted queries.
"""

import streamlit as st
import pandas as pd
from utils.config import get_custom_css, COLORS, APP_NAME, APPROVED_TABLES
from components.sidebar import render_sidebar
from components.metric_cards import render_demo_banner
from services.snowflake_service import snowflake_service

# Page Setup
st.set_page_config(
    page_title=f"Data Explorer — {APP_NAME}",
    page_icon="🔍",
    layout="wide",
)
st.markdown(get_custom_css(), unsafe_allow_html=True)
render_sidebar(active_page="Data Explorer")

# Header
st.markdown(
    f"""
    <div>
        <h1 style="font-size: 2rem; font-weight: 800; color: {COLORS['text']}; margin: 0;">
            🔍 Snowflake Retail Data Explorer
        </h1>
        <p style="font-size: 0.95rem; color: #64748B; margin-top: 4px; margin-bottom: 20px;">
            Inspect tables, explore column metadata, understand data types, and preview sample rows safely.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

status = snowflake_service.get_connection_status()
render_demo_banner(status["is_demo"])

# Schema Context Card
col_meta1, col_meta2, col_meta3 = st.columns(3)
with col_meta1:
    st.markdown(
        f"""
        <div class="kpi-card" style="border-top-color: {COLORS['primary']};">
            <div class="kpi-label">Active Database</div>
            <div class="kpi-value" style="font-size: 1.25rem;">{status['database']}</div>
            <div class="kpi-subtext">Snowflake Retail Warehouse</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_meta2:
    st.markdown(
        f"""
        <div class="kpi-card" style="border-top-color: {COLORS['highlight']};">
            <div class="kpi-label">Active Schema</div>
            <div class="kpi-value" style="font-size: 1.25rem;">{status['schema']}</div>
            <div class="kpi-subtext">TPC-DS Benchmark Model</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_meta3:
    st.markdown(
        f"""
        <div class="kpi-card" style="border-top-color: #0284C7;">
            <div class="kpi-label">Whitelisted Tables</div>
            <div class="kpi-value" style="font-size: 1.25rem;">{len(APPROVED_TABLES)} Approved</div>
            <div class="kpi-subtext">Protected by SQLValidator</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

# Table Selector & Inspection
col_sel, col_lim = st.columns([3, 1])
with col_sel:
    selected_table = st.selectbox(
        "Select Table to Inspect:",
        options=APPROVED_TABLES,
        index=0,
        help="Select any approved retail table to view column schema and row previews.",
    )
with col_lim:
    preview_limit = st.selectbox("Preview Limit:", options=[10, 25, 50], index=0)

# Schema Definition & Data Preview Tabs
tab_schema, tab_preview, tab_erd = st.tabs(["📋 Columns & Data Types", "👁️ Safe Row Preview", "📐 Schema Relationship Graph"])

with tab_schema:
    st.markdown(f"#### Column Definitions for `{selected_table}`")
    df_schema = snowflake_service.get_table_schema(selected_table)
    if not df_schema.empty:
        st.dataframe(df_schema, use_container_width=True)
    else:
        st.info("Schema details could not be retrieved.")

with tab_preview:
    st.markdown(f"#### Sample Data for `{selected_table}` (Limited to top {preview_limit} rows)")
    with st.spinner(f"Fetching {preview_limit} rows from {selected_table}..."):
        df_prev, is_demo_prev, err_prev = snowflake_service.preview_table(selected_table, limit=preview_limit)
        
        if err_prev and df_prev.empty:
            st.error(f"Error fetching preview: {err_prev}")
        elif df_prev.empty:
            st.warning("Table returned zero preview rows.")
        else:
            st.dataframe(df_prev, use_container_width=True)
            st.caption(f"🛡️ Guardrail active: row limit enforced to {preview_limit} to protect warehouse compute resources.")

with tab_erd:
    st.markdown("#### Entity Relationship Overview (Snowflake TPC-DS Retail Model)")
    st.markdown(
        """
```mermaid
erDiagram
    STORE_SALES ||--o{ ITEM : "ss_item_sk = i_item_sk"
    STORE_SALES ||--o{ DATE_DIM : "ss_sold_date_sk = d_date_sk"
    STORE_SALES ||--o{ CUSTOMER : "ss_customer_sk = c_customer_sk"
    WEB_SALES ||--o{ ITEM : "ws_item_sk = i_item_sk"
    WEB_SALES ||--o{ DATE_DIM : "ws_sold_date_sk = d_date_sk"
    CATALOG_SALES ||--o{ ITEM : "cs_item_sk = i_item_sk"
    CATALOG_SALES ||--o{ DATE_DIM : "cs_sold_date_sk = d_date_sk"

    STORE_SALES {
        int ss_sold_date_sk FK
        int ss_item_sk FK
        int ss_customer_sk FK
        int ss_quantity
        decimal ss_sales_price
        decimal ss_ext_sales_price
    }
    ITEM {
        int i_item_sk PK
        string i_item_id
        string i_product_name
        string i_category
        string i_brand
        decimal i_current_price
    }
    DATE_DIM {
        int d_date_sk PK
        date d_date
        int d_year
        int d_moy
        string d_month_name
    }
    CUSTOMER {
        int c_customer_sk PK
        string c_customer_id
        string c_first_name
        string c_last_name
    }
```
        """
    )
