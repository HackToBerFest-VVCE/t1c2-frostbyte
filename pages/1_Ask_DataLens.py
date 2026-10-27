"""
Ask DataLens — Natural-Language Analytics Powered by Qwen3-4B & Snowflake.
Translates user questions into validated SQL, executes against Snowflake/Demo,
and displays interactive visualisations and plain-English explanations.
"""

from datetime import datetime
import streamlit as st
import pandas as pd
from utils.config import get_custom_css, COLORS, APP_NAME
from components.sidebar import render_sidebar
from components.metric_cards import render_demo_banner
from components.charts import render_generic_chart
from services.qwen_service import qwen_service
from services.sql_validator import SQLValidator
from services.snowflake_service import snowflake_service
from utils.formatting import format_duration

# Page Setup
st.set_page_config(
    page_title=f"Ask DataLens — {APP_NAME}",
    page_icon="💬",
    layout="wide",
)
st.markdown(get_custom_css(), unsafe_allow_html=True)
render_sidebar(active_page="Ask DataLens")

# Initialize Session State
if "query_history" not in st.session_state:
    st.session_state["query_history"] = []

if "active_question" not in st.session_state:
    st.session_state["active_question"] = ""

# Header
st.markdown(
    f"""
    <div>
        <h1 style="font-size: 2rem; font-weight: 800; color: {COLORS['text']}; margin: 0;">
            💬 Ask DataLens
        </h1>
        <p style="font-size: 0.95rem; color: #64748B; margin-top: 4px; margin-bottom: 20px;">
            Ask questions in plain English. <b>Qwen3-4B</b> converts your inquiry into secure SQL, runs it through Snowflake, and visualises the answers.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Example questions list
EXAMPLES = [
    "Which products generated the highest sales?",
    "What are the top 10 best-selling products?",
    "Which month had the highest sales?",
    "Which product categories perform best?",
    "How do store, web, and catalog sales compare?",
    "What is the average quantity sold per product?",
]

# Quick Example Chips
st.markdown("<p style='font-size: 0.82rem; font-weight: 700; color: #64748B; text-transform: uppercase; margin-bottom: 6px;'>💡 Example Questions (click to load)</p>", unsafe_allow_html=True)

cols = st.columns(3)
for idx, ex in enumerate(EXAMPLES):
    col = cols[idx % 3]
    if col.button(f"🔍 {ex}", key=f"ex_{idx}", use_container_width=True):
        st.session_state["active_question"] = ex
        st.rerun()

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# Question Input Form
with st.form(key="ask_form", clear_on_submit=False):
    user_question = st.text_input(
        label="Natural-Language Analytics Query:",
        value=st.session_state.get("active_question", ""),
        placeholder="Ask anything about your retail sales data...",
        help="Type any analytical retail question about sales, products, categories, or channels.",
    )
    col_submit, col_clear = st.columns([1, 5])
    with col_submit:
        submitted = st.form_submit_button("⚡ Run Analytics", use_container_width=True)

if submitted and user_question.strip():
    q_text = user_question.strip()
    st.session_state["active_question"] = q_text

    st.markdown("---")
    
    # 1. Step: Generate SQL with Qwen3-4B
    with st.status(f"Analyzing question with Qwen3-4B...", expanded=True) as status_box:
        st.write("1. 🧠 Submitting question & schema context to Qwen3-4B...")
        ai_resp = qwen_service.generate_sql(q_text)
        raw_sql = ai_resp.get("sql", "")
        explanation = ai_resp.get("explanation", "")
        is_simulated = ai_resp.get("is_simulated", False)
        model_name = ai_resp.get("model_name", "Qwen3-4B")

        if is_simulated:
            st.info(f"ℹ️ {ai_resp.get('error', 'Using deterministic Qwen3-4B engine')}")

        st.write("2. 🛡️ Running security validation layer...")
        is_valid, validation_err, sanitized_sql = SQLValidator.validate(raw_sql)

        if not is_valid:
            status_box.update(label="Query Rejected by SQL Security Validator", state="error", expanded=True)
            st.error(f"❌ Security Policy Rejection: {validation_err}")
            
            # Log failed validation into history
            st.session_state["query_history"].insert(
                0,
                {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "question": q_text,
                    "status": "Rejected",
                    "duration": 0.0,
                    "sql": raw_sql,
                    "rows": 0,
                    "is_demo": True,
                },
            )
            st.stop()

        st.write("3. ❄️ Executing approved SQL query...")
        df_results, exec_time, is_demo, exec_err = snowflake_service.execute_query(sanitized_sql)

        if exec_err and df_results.empty:
            status_box.update(label="Query Execution Failed", state="error", expanded=True)
            st.error(f"Database Error: {exec_err}")
            st.session_state["query_history"].insert(
                0,
                {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "question": q_text,
                    "status": "Error",
                    "duration": exec_time,
                    "sql": sanitized_sql,
                    "rows": 0,
                    "is_demo": is_demo,
                },
            )
            st.stop()

        status_box.update(label=f"Analysis Complete! ({format_duration(exec_time)})", state="complete", expanded=False)

    # Log successful execution into history
    st.session_state["query_history"].insert(
        0,
        {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "question": q_text,
            "status": "Success",
            "duration": exec_time,
            "sql": sanitized_sql,
            "rows": len(df_results),
            "is_demo": is_demo,
        },
    )

    # Mandatory Demo Banner if demo engine was utilized
    render_demo_banner(is_demo)

    # Explanation Card
    st.markdown(
        f"""
        <div class="datalens-card" style="border-left: 4px solid {COLORS['highlight']}; margin-bottom: 20px;">
            <div style="font-size: 0.8rem; font-weight: 700; color: {COLORS['highlight']}; text-transform: uppercase; margin-bottom: 4px;">
                💡 Plain-English Summary ({model_name})
            </div>
            <div style="font-size: 1.05rem; color: {COLORS['text']}; line-height: 1.5; font-weight: 500;">
                {explanation}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Results Visualisation & Data Table Tabs
    tab_chart, tab_data, tab_sql = st.tabs(["📊 Interactive Visualisation", "📋 Query Results Table", "🔍 Generated SQL"])

    with tab_chart:
        if not df_results.empty and len(df_results.columns) >= 2:
            fig = render_generic_chart(df_results, question_hint=q_text)
            st.plotly_chart(fig, use_container_width=True)
        elif df_results.empty:
            st.warning("Query returned zero rows matching your criteria.")
        else:
            # Single scalar metric
            val = df_results.iloc[0, 0]
            st.metric(label=df_results.columns[0].replace("_", " ").title(), value=f"{val}")

    with tab_data:
        st.markdown(f"**Rows returned:** {len(df_results)} | **Execution duration:** {format_duration(exec_time)}")
        # Format currency & numbers in preview table
        formatted_df = df_results.copy()
        st.dataframe(formatted_df, use_container_width=True)

        # Download CSV button
        csv_bytes = df_results.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Results as CSV",
            data=csv_bytes,
            file_name=f"datalens_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )

    with tab_sql:
        st.markdown(
            f"""
            <div style="font-size: 0.85rem; color: #64748B; margin-bottom: 8px;">
                <b>Validated SQL</b> generated by <code>{model_name}</code>:
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.code(sanitized_sql, language="sql")
        st.caption("All queries pass through SQLValidator to ensure read-only safety, schema enforcement, and row limit clamping.")

elif not user_question.strip():
    # Empty State Guidance
    st.markdown(
        f"""
        <div class="datalens-card" style="text-align: center; padding: 48px 24px; margin-top: 20px;">
            <div style="font-size: 2.5rem; margin-bottom: 12px;">🔍</div>
            <h3 style="font-weight: 700; color: {COLORS['text']}; margin-bottom: 8px;">Ready for your inquiry</h3>
            <p style="font-size: 0.95rem; color: #64748B; max-width: 550px; margin: 0 auto 18px auto;">
                Select one of the suggested example queries above, or formulate your own question about revenue, customer habits, products, or channels.
            </p>
            <div style="font-size: 0.8rem; color: #94A3B8;">
                Powered by <b>Qwen3-4B</b> Natural Language to SQL
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
