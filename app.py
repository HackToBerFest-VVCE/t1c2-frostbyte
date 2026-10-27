"""DataLens Live — Real-Time Snowflake Analytics Prototype.

Executive Dashboard featuring real-time metrics, interactive Plotly visuals,
live Snowflake connection status, and zero synthetic data fallbacks.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from services.ui_theme import (
    apply_theme,
    render_hero_banner,
    render_metric_card,
    apply_plotly_theme,
    COLOR_PRIMARY_BLUE,
    COLOR_PURPLE,
    COLOR_LIGHT_BLUE,
    COLOR_DARK_NAVY,
    COLOR_CARD,
    COLOR_BORDER,
)
from services.snowflake_service import (
    test_connection,
    get_snowflake_config,
    DEFAULT_DATABASE,
    DEFAULT_SCHEMA,
)
from services.analytics_service import (
    get_sales_kpi_summary,
    get_sales_trend_by_date,
    get_top_products,
    get_omnichannel_comparison,
)
from services.qwen_service import check_ollama_status

# Configure page
st.set_page_config(
    page_title="DataLens Live — Snowflake Analytics",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply custom Hackathon theme
apply_theme()

# Sidebar: System Health & Configuration
with st.sidebar:
    st.markdown("### ⚡ System Status")
    
    # 1. Ollama status check
    ollama_ok, ollama_msg, models = check_ollama_status()
    if ollama_ok:
        st.markdown(
            '<div style="background: #DEF7EC; padding: 0.5rem 0.75rem; border-radius: 8px; border: 1px solid #BCF0DA; font-size: 0.85rem; margin-bottom: 0.75rem;">'
            '<strong>🟢 Ollama Qwen3-4B</strong><br><span style="color: #03543F;">Ready & Responding</span></div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div style="background: #FDE8E8; padding: 0.5rem 0.75rem; border-radius: 8px; border: 1px solid #FBD5D5; font-size: 0.82rem; margin-bottom: 0.75rem;">'
            f'<strong>🔴 Ollama Service</strong><br><span style="color: #9B1C1C;">{ollama_msg}</span></div>',
            unsafe_allow_html=True
        )

    # 2. Snowflake configuration check
    is_connected, conn_info, conn_err = test_connection()
    cfg = get_snowflake_config()

    if is_connected:
        st.markdown(
            f'<div style="background: #DEF7EC; padding: 0.5rem 0.75rem; border-radius: 8px; border: 1px solid #BCF0DA; font-size: 0.82rem; margin-bottom: 0.75rem;">'
            f'<strong>🟢 Snowflake Connected</strong><br>'
            f'<span style="color: #03543F;">Wh: {conn_info.get("warehouse")}<br>Ping: {conn_info.get("latency_ms")}ms</span></div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div style="background: #FDE8E8; padding: 0.5rem 0.75rem; border-radius: 8px; border: 1px solid #FBD5D5; font-size: 0.82rem; margin-bottom: 0.75rem;">'
            f'<strong>🔴 Snowflake Disconnected</strong><br><span style="color: #9B1C1C;">{conn_err}</span></div>',
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.markdown("### 📊 Active Data Source")
    active_db = cfg.get("database", DEFAULT_DATABASE) if cfg else DEFAULT_DATABASE
    active_sch = cfg.get("schema", DEFAULT_SCHEMA) if cfg else DEFAULT_SCHEMA
    st.code(f"{active_db}\n.{active_sch}", language="sql")

    selected_year = st.selectbox(
        "📅 Analysis Year (Partition Filter)",
        options=[2000, 1999, 1998, 2001, 2002],
        index=0,
        help="Filters queries on date_dim.d_year to prevent unrestricted full-table scans on SF10TCL (10TB)."
    )

    st.markdown("---")
    st.caption("DataLens Live Prototype • Snowflake + Qwen3-4B")

# Top Banner
data_source_label = f"{active_db}.{active_sch}"
render_hero_banner(
    title="Executive Sales Dashboard",
    subtitle="Real-time Snowflake telemetry & live business intelligence on TPC-DS sample data",
    data_source=data_source_label,
    connected=is_connected
)

# If credentials are not configured or connection failed, display setup guide
if not is_connected:
    st.warning("⚠️ **Live Snowflake Connection Required**")
    
    st.markdown(
        f"""
        <div class="datalens-card">
            <h3 style="margin-top: 0; color: {COLOR_DARK_NAVY};">Snowflake Connection Setup Guide</h3>
            <p style="color: #475569;">
                DataLens Live connects directly to your live Snowflake instance to execute authenticated queries.
                Synthetic or simulated data is strictly disabled.
            </p>
            <hr style="border: 0; border-top: 1px solid {COLOR_BORDER}; margin: 1rem 0;">
            <p><strong>Step 1:</strong> Copy the template configuration file in the project directory:</p>
            <pre style="background: #F8FAFC; padding: 0.75rem; border-radius: 6px; border: 1px solid {COLOR_BORDER};">cp .streamlit/secrets.toml.example .streamlit/secrets.toml</pre>
            <p><strong>Step 2:</strong> Open <code>.streamlit/secrets.toml</code> and insert your actual Snowflake credentials:</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    example_code = """[snowflake]
account = "your_account_identifier"  # e.g. xy12345.us-east-1 or orgname-account
user = "your_username"
password = "your_password"
warehouse = "COMPUTE_WH"
database = "SNOWFLAKE_SAMPLE_DATA"
schema = "TPCDS_SF10TCL"
role = "ACCOUNTADMIN" # optional"""
    st.code(example_code, language="toml")
    
    if conn_err:
        st.error(f"**Connection Diagnostic Details:** {conn_err}")
    st.stop()

# --- LIVE METRICS SECTION ---
st.markdown("### 📈 Core Business KPIs")

with st.spinner("Executing live Snowflake aggregation query..."):
    kpi_df, kpi_time, kpi_err = get_sales_kpi_summary(year=selected_year)

if kpi_err:
    st.error(f"Failed to query KPIs from Snowflake: {kpi_err}")
elif kpi_df is not None and not kpi_df.empty:
    row = kpi_df.iloc[0]
    total_sales = float(row.get("TOTAL_SALES") or 0.0)
    total_qty = int(row.get("TOTAL_QUANTITY") or 0)
    total_profit = float(row.get("TOTAL_PROFIT") or 0.0)
    avg_price = float(row.get("AVG_SALES_PRICE") or 0.0)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card(
            title="Total Store Sales",
            value=f"${total_sales:,.2f}",
            subtitle=f"Year {selected_year} • Query: {kpi_time}s",
            badge="Snowflake Live"
        )
    with col2:
        render_metric_card(
            title="Total Quantity Sold",
            value=f"{total_qty:,} units",
            subtitle=f"Across store transactions",
            badge="Units"
        )
    with col3:
        render_metric_card(
            title="Net Profit",
            value=f"${total_profit:,.2f}",
            subtitle=f"Calculated from ss_net_profit",
            badge="Profit"
        )
    with col4:
        render_metric_card(
            title="Avg Item Price",
            value=f"${avg_price:,.2f}",
            subtitle=f"Per unit sales average",
            badge="Avg"
        )

st.markdown("<br>", unsafe_allow_html=True)

# --- VISUALIZATIONS SECTION ---
col_left, col_right = st.columns([3, 2])

with col_left:
    st.markdown("### 📅 Daily Sales Trend")
    with st.spinner("Fetching daily sales time-series..."):
        trend_df, trend_time, trend_err = get_sales_trend_by_date(year=selected_year)
    
    if trend_err:
        st.error(f"Error fetching sales trend: {trend_err}")
    elif trend_df is not None and not trend_df.empty:
        fig_trend = px.line(
            trend_df,
            x="SALE_DATE",
            y="DAILY_SALES",
            title=f"Daily Store Sales Volume ({selected_year})",
            labels={"SALE_DATE": "Date", "DAILY_SALES": "Sales Amount ($)"},
            color_discrete_sequence=[COLOR_PRIMARY_BLUE],
        )
        fig_trend.update_traces(line=dict(width=2.5), mode="lines+markers", marker=dict(size=4))
        apply_plotly_theme(fig_trend, height=360)
        st.plotly_chart(fig_trend, use_container_width=True)
        st.caption(f"⚡ Query executed in {trend_time}s • {len(trend_df)} data points returned")
    else:
        st.info("No sales trend data found for the selected period.")

with col_right:
    st.markdown("### 🌐 Omnichannel Comparison")
    with st.spinner("Executing Store, Web & Catalog comparative aggregation..."):
        channel_df, chan_time, chan_err = get_omnichannel_comparison(year=selected_year)
    
    if chan_err:
        st.error(f"Error comparing sales channels: {chan_err}")
    elif channel_df is not None and not channel_df.empty:
        fig_chan = px.bar(
            channel_df,
            x="CHANNEL",
            y="SALES",
            color="CHANNEL",
            text_auto="$,.2s",
            title=f"Sales by Channel ({selected_year})",
            color_discrete_map={
                "Store Sales": COLOR_PRIMARY_BLUE,
                "Web Sales": COLOR_PURPLE,
                "Catalog Sales": "#0284C7"
            }
        )
        apply_plotly_theme(fig_chan, height=360)
        fig_chan.update_layout(showlegend=False)
        st.plotly_chart(fig_chan, use_container_width=True)
        st.caption(f"⚡ Query executed in {chan_time}s")
    else:
        st.info("No omnichannel comparison data available.")

st.markdown("<br>", unsafe_allow_html=True)

# --- TOP PRODUCTS LEADERBOARD ---
st.markdown("### 🏆 Top 10 Products by Sales")
with st.spinner("Querying top product leaderboard..."):
    prod_df, prod_time, prod_err = get_top_products(limit=10, year=selected_year)

if prod_err:
    st.error(f"Error fetching top products: {prod_err}")
elif prod_df is not None and not prod_df.empty:
    col_pchart, col_ptable = st.columns([3, 2])
    
    with col_pchart:
        fig_prod = px.bar(
            prod_df.sort_values("TOTAL_SALES", ascending=True),
            x="TOTAL_SALES",
            y="PRODUCT_NAME",
            orientation="h",
            color="CATEGORY",
            title=f"Top 10 Products Revenue ({selected_year})",
            labels={"TOTAL_SALES": "Total Revenue ($)", "PRODUCT_NAME": "Product"},
            color_discrete_sequence=[COLOR_PRIMARY_BLUE, COLOR_PURPLE, "#0284C7", "#38BDF8"]
        )
        apply_plotly_theme(fig_prod, height=380)
        st.plotly_chart(fig_prod, use_container_width=True)
    
    with col_ptable:
        st.markdown(f"**Leaderboard Table** (Snowflake Latency: `{prod_time}s`)")
        display_df = prod_df.copy()
        display_df["TOTAL_SALES"] = display_df["TOTAL_SALES"].map("${:,.2f}".format)
        display_df["TOTAL_QUANTITY_SOLD"] = display_df["TOTAL_QUANTITY_SOLD"].map("{:,}".format)
        st.dataframe(display_df, use_container_width=True, hide_index=True)

st.markdown("---")
st.markdown(
    '<div style="text-align: center; color: #64748B; font-size: 0.85rem;">'
    'DataLens Live • Real-Time Snowflake Analytics Prototype • Built with Streamlit, Snowflake Connector, & Ollama Qwen3-4B'
    '</div>',
    unsafe_allow_html=True
)
