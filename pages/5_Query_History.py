"""
Query History Page for DataLens.
Tracks all natural language queries, generated SQL, execution durations, and statuses.
Local session state implementation without creating external database objects.
"""

import streamlit as st
import pandas as pd
from utils.config import get_custom_css, COLORS, APP_NAME
from components.sidebar import render_sidebar
from components.metric_cards import render_demo_banner
from services.snowflake_service import snowflake_service
from utils.formatting import format_duration, get_status_badge

# Page Setup
st.set_page_config(
    page_title=f"Query History — {APP_NAME}",
    page_icon="📜",
    layout="wide",
)
st.markdown(get_custom_css(), unsafe_allow_html=True)
render_sidebar(active_page="Query History")

# Header
st.markdown(
    f"""
    <div>
        <h1 style="font-size: 2rem; font-weight: 800; color: {COLORS['text']}; margin: 0;">
            📜 Query Audit & Execution History
        </h1>
        <p style="font-size: 0.95rem; color: #64748B; margin-top: 4px; margin-bottom: 20px;">
            Review previously asked questions, generated SQL, validation outcomes, and execution latency.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

status = snowflake_service.get_connection_status()
render_demo_banner(status["is_demo"])

# Session history state
history = st.session_state.get("query_history", [])

col_btn1, col_btn2 = st.columns([1, 5])
with col_btn1:
    if st.button("🗑️ Clear History"):
        st.session_state["query_history"] = []
        st.rerun()

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

if not history:
    st.info("No query history recorded yet in this session. Head to 'Ask DataLens' to submit a question!")
else:
    # Summary Metrics
    total_q = len(history)
    success_q = sum(1 for q in history if q.get("status") == "Success")
    rejected_q = sum(1 for q in history if q.get("status") == "Rejected")
    avg_dur = sum(q.get("duration", 0) for q in history) / max(total_q, 1)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""
            <div class="kpi-card" style="border-top-color: {COLORS['primary']};">
                <div class="kpi-label">Total Inquiries</div>
                <div class="kpi-value">{total_q}</div>
                <div class="kpi-subtext">Session queries logged</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="kpi-card" style="border-top-color: #10B981;">
                <div class="kpi-label">Successful Queries</div>
                <div class="kpi-value">{success_q}</div>
                <div class="kpi-subtext">Executed without issue</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
            <div class="kpi-card" style="border-top-color: #EF4444;">
                <div class="kpi-label">Security Blocks</div>
                <div class="kpi-value">{rejected_q}</div>
                <div class="kpi-subtext">Prevented by SQLValidator</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f"""
            <div class="kpi-card" style="border-top-color: {COLORS['highlight']};">
                <div class="kpi-label">Average Latency</div>
                <div class="kpi-value">{format_duration(avg_dur)}</div>
                <div class="kpi-subtext">Query roundtrip time</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # History List View
    st.markdown("### Execution Log")
    for idx, item in enumerate(history):
        status_html = get_status_badge(item.get("status", "Unknown"))
        with st.expander(f"#{len(history) - idx} • {item.get('question')} ({item.get('timestamp')})"):
            c_meta1, c_meta2, c_meta3 = st.columns(3)
            with c_meta1:
                st.markdown(f"**Status:** {status_html}", unsafe_allow_html=True)
            with c_meta2:
                st.markdown(f"**Latency:** {format_duration(item.get('duration', 0))}")
            with c_meta3:
                st.markdown(f"**Rows:** {item.get('rows', 0)} ({'Demo Data' if item.get('is_demo') else 'Live Snowflake'})")

            st.markdown("**Generated SQL:**")
            st.code(item.get("sql", ""), language="sql")
