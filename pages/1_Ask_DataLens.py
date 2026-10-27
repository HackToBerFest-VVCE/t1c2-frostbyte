"""Ask DataLens — Natural-Language Analytics Powered by Ollama Qwen3-4B.

Pipeline:
Question -> Qwen3-4B -> SQL Generation -> SQL Validation -> Snowflake Execution -> Results Table -> Plotly Visual -> Plain-English Explanation
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from services.ui_theme import (
    apply_theme,
    render_hero_banner,
    apply_plotly_theme,
    COLOR_PRIMARY_BLUE,
    COLOR_PURPLE,
    COLOR_DARK_NAVY,
    COLOR_CARD,
    COLOR_BORDER,
)
from services.snowflake_service import (
    test_connection,
    execute_snowflake_query,
    get_snowflake_config,
    DEFAULT_DATABASE,
    DEFAULT_SCHEMA,
)
from services.sql_validator import validate_and_sanitize_sql
from services.qwen_service import (
    check_ollama_status,
    generate_sql_query,
    explain_query_results,
    DEFAULT_MODEL,
)

st.set_page_config(
    page_title="Ask DataLens — Natural Language Analytics",
    page_icon="💬",
    layout="wide",
)
apply_theme()

# Connection check
cfg = get_snowflake_config()
is_connected = False
if cfg:
    is_connected, _, _ = test_connection()

active_db = cfg.get("database", DEFAULT_DATABASE) if cfg else DEFAULT_DATABASE
active_sch = cfg.get("schema", DEFAULT_SCHEMA) if cfg else DEFAULT_SCHEMA

render_hero_banner(
    title="Ask DataLens",
    subtitle="AI-driven Natural Language to Snowflake Analytics powered by local Qwen3-4B",
    data_source=f"{active_db}.{active_sch}",
    connected=is_connected
)

# Check Ollama status
ollama_ok, ollama_msg, available_models = check_ollama_status()
if not ollama_ok:
    st.error(f"⚠️ **Ollama Service Unavailable**: {ollama_msg}")
    st.info("Make sure the Ollama application is running and `qwen3:4b` is installed.")

# Quick sample question buttons
st.markdown("##### 💡 Suggested Questions")
sample_questions = [
    "What are the total sales?",
    "Which products generate the highest sales?",
    "What is the total quantity sold?",
    "Compare store and web sales.",
    "Show sales trends by date.",
]

cols = st.columns(len(sample_questions))
selected_sample = None
for i, sq in enumerate(sample_questions):
    with cols[i]:
        if st.button(sq, key=f"sq_{i}", use_container_width=True):
            selected_sample = sq

# Question input form
user_input = st.text_input(
    "Ask a question in plain English:",
    value=selected_sample if selected_sample else "",
    placeholder="e.g. Which products generate the highest sales in store_sales?",
    help="Type any business question regarding sales, products, categories, or trends."
)

run_button = st.button("🚀 Analyze Question", type="primary")

if run_button or selected_sample:
    if not user_input.strip():
        st.warning("Please enter or select a question to analyze.")
        st.stop()

    if not ollama_ok:
        st.error("Cannot proceed: Qwen3-4B model on Ollama is not available.")
        st.stop()

    st.markdown("---")
    st.markdown(f"### 🔍 Analysis for: *\"{user_input.strip()}\"*")

    # Step 1: SQL Generation via Qwen3-4B
    with st.status("🧠 Step 1: Generating Snowflake SQL with Qwen3-4B...", expanded=True) as status:
        sql_query, thinking, gen_err = generate_sql_query(user_input)
        if gen_err:
            status.update(label="❌ SQL Generation Failed", state="error")
            st.error(gen_err)
            st.stop()
        
        status.update(label="✅ SQL Query Generated Successfully", state="complete")

    if thinking:
        with st.expander("💭 View Qwen3-4B Chain-of-Thought Reasoning", expanded=False):
            st.markdown(f"```\n{thinking}\n```")

    st.markdown("##### 📝 Generated SQL Query")
    st.code(sql_query, language="sql")

    # Step 2: SQL Validation and Safety Enforcement
    with st.status("🛡️ Step 2: Validating SQL Security & Permissions...", expanded=True) as status:
        is_valid, sanitized_sql, val_err = validate_and_sanitize_sql(sql_query, default_limit=100)
        if not is_valid:
            status.update(label="❌ SQL Validation Rejected Query", state="error")
            st.error(f"**Safety Violation:** {val_err}")
            st.stop()
        
        status.update(label="✅ SQL Security Checks Passed (Read-only, allowlist verified, LIMIT applied)", state="complete")

    # Display sanitized SQL if it changed
    if sanitized_sql.strip() != sql_query.strip():
        with st.expander("🛡️ View Sanitized & Formatted SQL", expanded=False):
            st.code(sanitized_sql, language="sql")

    # Step 3: Snowflake Execution
    if not is_connected:
        st.warning(
            "⚠️ **Snowflake connection is not configured or offline.**\n\n"
            "The SQL query was generated and validated, but cannot be executed against live Snowflake data. "
            "Please configure `.streamlit/secrets.toml` to view live query results."
        )
        st.stop()

    with st.status("⚡ Step 3: Executing Query against Snowflake...", expanded=True) as status:
        df, exec_time, exec_err = execute_snowflake_query(sanitized_sql, max_rows=100)
        if exec_err:
            status.update(label="❌ Snowflake Execution Failed", state="error")
            st.error(exec_err)
            st.stop()
        
        status.update(label=f"✅ Snowflake Query Executed in {exec_time}s ({len(df) if df is not None else 0} rows)", state="complete")

    if df is None or df.empty:
        st.info("The query returned 0 rows from Snowflake.")
        st.stop()

    # Step 4: Results Table
    st.markdown("##### 📊 Query Results Table")
    st.dataframe(df, use_container_width=True)

    # Step 5: Dynamic Plotly Visualization
    st.markdown("##### 📈 Interactive Visualization")
    try:
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        non_numeric_cols = [c for c in df.columns if c not in numeric_cols]

        if len(df) == 1 and len(numeric_cols) >= 1:
            # Single KPI metric card
            val = df[numeric_cols[0]].iloc[0]
            col_name = numeric_cols[0].replace("_", " ").title()
            val_str = f"${val:,.2f}" if "sales" in numeric_cols[0].lower() or "price" in numeric_cols[0].lower() else f"{val:,}"
            st.metric(label=col_name, value=val_str)
        
        elif len(non_numeric_cols) >= 1 and len(numeric_cols) >= 1:
            cat_col = non_numeric_cols[0]
            val_col = numeric_cols[0]

            # Detect if category is a date
            is_date = "date" in cat_col.lower() or "day" in cat_col.lower()
            if is_date:
                fig = px.line(
                    df,
                    x=cat_col,
                    y=val_col,
                    title=f"{val_col.replace('_', ' ').title()} over {cat_col.replace('_', ' ').title()}",
                    color_discrete_sequence=[COLOR_PRIMARY_BLUE]
                )
                fig.update_traces(mode="lines+markers")
            else:
                # Bar chart
                fig = px.bar(
                    df.head(20),
                    x=cat_col,
                    y=val_col,
                    title=f"{val_col.replace('_', ' ').title()} by {cat_col.replace('_', ' ').title()}",
                    color_discrete_sequence=[COLOR_PRIMARY_BLUE, COLOR_PURPLE]
                )
            apply_plotly_theme(fig, height=380)
            st.plotly_chart(fig, use_container_width=True)
            
        elif len(numeric_cols) >= 2:
            fig = px.bar(
                df.head(20),
                x=numeric_cols[0],
                y=numeric_cols[1],
                color_discrete_sequence=[COLOR_PRIMARY_BLUE]
            )
            apply_plotly_theme(fig, height=380)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.caption("Results rendered in tabular format.")
    except Exception as viz_err:
        st.caption(f"Note: Standard chart could not be generated ({str(viz_err)}). Data displayed in table above.")

    # Step 6: Plain-English Business Explanation by Qwen3-4B
    st.markdown("##### 🗣️ Plain-English Business Summary")
    with st.spinner("Generating AI executive explanation..."):
        # Create a compact summary string of the results
        summary_rows = df.head(5).to_dict(orient="records")
        summary_text = f"Total rows: {len(df)}. Top rows: {summary_rows}"
        explanation, exp_err = explain_query_results(user_input, sanitized_sql, summary_text)
    
    if exp_err:
        st.warning(f"Could not generate AI explanation: {exp_err}")
    elif explanation:
        st.markdown(
            f"""
            <div class="datalens-card" style="border-left: 4px solid {COLOR_PURPLE}; background: #FAF5FF;">
                <div style="font-weight: 600; color: #6B21A8; margin-bottom: 0.35rem;">💡 Business Analyst Takeaway:</div>
                <div style="color: {COLOR_DARK_NAVY}; font-size: 0.98rem; line-height: 1.5;">{explanation}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
