"""Sales Analytics Page — Deep Dive into Omnichannel Performance & Sales Trends.
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
    get_sales_trend_by_date,
    get_omnichannel_comparison,
    run_safe_query,
)

st.set_page_config(
    page_title="Sales Analytics — DataLens Live",
    page_icon="📊",
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
    title="Sales & Channel Analytics",
    subtitle="Comparative breakdown of Store, Web, and Catalog sales with granular time-series analysis",
    data_source=f"{active_db}.{active_sch}",
    connected=is_connected
)

if not is_connected:
    st.warning("⚠️ **Live Snowflake Connection Required**")
    st.info("Configure your credentials in `.streamlit/secrets.toml` to access live Snowflake analytics.")
    st.stop()

# Controls
col_ctrl1, col_ctrl2 = st.columns([1, 3])
with col_ctrl1:
    selected_year = st.selectbox("Select Year", options=[2000, 1999, 1998, 2001, 2002], index=0)

# Section 1: Omnichannel Comparison
st.markdown("### 🌐 Omnichannel Sales Comparison")
with st.spinner("Executing channel aggregation query across Store, Web, and Catalog..."):
    chan_df, chan_time, chan_err = get_omnichannel_comparison(year=selected_year)

if chan_err:
    st.error(f"Error querying channels: {chan_err}")
elif chan_df is not None and not chan_df.empty:
    total_omni_sales = chan_df["SALES"].sum()
    total_omni_qty = chan_df["QUANTITY"].sum()

    mcol1, mcol2, mcol3 = st.columns(3)
    with mcol1:
        render_metric_card("Total Combined Sales", f"${total_omni_sales:,.2f}", f"Year {selected_year} All Channels")
    with mcol2:
        render_metric_card("Total Units Moved", f"{total_omni_qty:,} units", "Store + Web + Catalog")
    with mcol3:
        leader = chan_df.loc[chan_df["SALES"].idxmax()]["CHANNEL"]
        render_metric_card("Leading Channel", f"{leader}", "By total revenue")

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns([3, 2])
    with c1:
        fig_bar = px.bar(
            chan_df,
            x="CHANNEL",
            y="SALES",
            color="CHANNEL",
            text_auto="$,.2s",
            title=f"Total Revenue by Sales Channel ({selected_year})",
            color_discrete_map={
                "Store Sales": COLOR_PRIMARY_BLUE,
                "Web Sales": COLOR_PURPLE,
                "Catalog Sales": "#0284C7"
            }
        )
        apply_plotly_theme(fig_bar, height=350)
        fig_bar.update_layout(showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

    with c2:
        fig_pie = px.pie(
            chan_df,
            names="CHANNEL",
            values="SALES",
            title=f"Channel Market Share ({selected_year})",
            color="CHANNEL",
            hole=0.45,
            color_discrete_map={
                "Store Sales": COLOR_PRIMARY_BLUE,
                "Web Sales": COLOR_PURPLE,
                "Catalog Sales": "#0284C7"
            }
        )
        apply_plotly_theme(fig_pie, height=350)
        st.plotly_chart(fig_pie, use_container_width=True)

# Section 2: Daily Sales Trends
st.markdown("### 📈 Daily Sales Trend & Moving Average")
with st.spinner("Fetching daily sales time-series from Snowflake..."):
    trend_df, trend_time, trend_err = get_sales_trend_by_date(year=selected_year)

if trend_err:
    st.error(f"Error loading sales trend: {trend_err}")
elif trend_df is not None and not trend_df.empty:
    trend_df["SALE_DATE"] = pd.to_datetime(trend_df["SALE_DATE"])
    trend_df = trend_df.sort_values("SALE_DATE")
    trend_df["7_DAY_MA"] = trend_df["DAILY_SALES"].rolling(window=7, min_periods=1).mean()

    fig_ma = go.Figure()
    fig_ma.add_trace(go.Scatter(
        x=trend_df["SALE_DATE"],
        y=trend_df["DAILY_SALES"],
        mode="lines",
        name="Daily Sales ($)",
        line=dict(color="#BAE6FD", width=1.5),
    ))
    fig_ma.add_trace(go.Scatter(
        x=trend_df["SALE_DATE"],
        y=trend_df["7_DAY_MA"],
        mode="lines",
        name="7-Day Moving Avg ($)",
        line=dict(color=COLOR_PRIMARY_BLUE, width=3),
    ))
    apply_plotly_theme(fig_ma, title=f"Daily Revenue & 7-Day Moving Average ({selected_year})", height=400)
    st.plotly_chart(fig_ma, use_container_width=True)

    with st.expander("📄 View Daily Sales Raw Data", expanded=False):
        st.dataframe(trend_df, use_container_width=True)
