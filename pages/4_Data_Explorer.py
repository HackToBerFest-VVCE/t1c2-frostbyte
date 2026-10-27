"""Data Explorer Page — Live Schema Inspection & Safe SQL Execution Console.
"""

import streamlit as st
import pandas as pd

from services.ui_theme import (
    apply_theme,
    render_hero_banner,
    COLOR_PRIMARY_BLUE,
    COLOR_PURPLE,
    COLOR_CARD,
    COLOR_BORDER,
    COLOR_DARK_NAVY,
)
from services.snowflake_service import (
    test_connection,
    get_snowflake_config,
    execute_snowflake_query,
    inspect_schema,
    DEFAULT_DATABASE,
    DEFAULT_SCHEMA,
)
from services.sql_validator import validate_and_sanitize_sql, ALLOWED_TABLES

st.set_page_config(
    page_title="Data Explorer — DataLens Live",
    page_icon="🔎",
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
    title="Snowflake Data Explorer",
    subtitle="Inspect live schema structure, browse table metadata, and execute validated ad-hoc queries",
    data_source=f"{active_db}.{active_sch}",
    connected=is_connected
)

if not is_connected:
    st.warning("⚠️ **Live Snowflake Connection Required**")
    st.info("Configure your credentials in `.streamlit/secrets.toml` to inspect live tables and schemas.")
    st.stop()

tab_schema, tab_console = st.tabs(["📋 Schema & Table Inspector", "💻 Safe SQL Console"])

with tab_schema:
    st.markdown("### 🗄️ Database Schema Inspector")
    st.markdown(
        f"Inspecting active schema: **`{active_db}.{active_sch}`**. "
        "Dynamic discovery verifies actual available tables without assumptions."
    )

    with st.spinner("Inspecting Snowflake INFORMATION_SCHEMA..."):
        schema_map = inspect_schema(active_db, active_sch)

    if not schema_map:
        st.info(
            f"No accessible tables discovered in `{active_db}.{active_sch}`. "
            "Please check warehouse privileges or select another schema."
        )
    else:
        tables_list = sorted(list(schema_map.keys()))
        selected_tbl = st.selectbox("Select Table to Inspect:", options=tables_list)

        if selected_tbl:
            cols = schema_map.get(selected_tbl, [])
            st.markdown(f"**Table:** `{selected_tbl}` ({len(cols)} columns detected)")
            
            c_left, c_right = st.columns([1, 2])
            with c_left:
                st.markdown("##### 📑 Column List")
                if cols:
                    st.dataframe(pd.DataFrame({"Column Name": cols}), use_container_width=True, height=350)
                else:
                    st.caption("Column metadata unavailable.")

            with c_right:
                st.markdown("##### 👁️ Live Data Sample (First 10 Rows)")
                preview_sql = f"SELECT * FROM {selected_tbl} LIMIT 10"
                with st.spinner("Fetching sample rows..."):
                    df_sample, sample_time, sample_err = execute_snowflake_query(preview_sql, max_rows=10)
                
                if sample_err:
                    st.error(f"Sample query failed: {sample_err}")
                elif df_sample is not None and not df_sample.empty:
                    st.dataframe(df_sample, use_container_width=True, height=350)
                    st.caption(f"⚡ Fetched in {sample_time}s")
                else:
                    st.info("Table is empty or returned 0 rows.")

with tab_console:
    st.markdown("### 💻 Safe Snowflake SQL Console")
    st.markdown(
        "Execute custom read-only SQL queries with built-in safety guards. "
        "Queries are strictly validated against data-altering statements and restricted to allowlisted tables."
    )

    st.markdown(f"**Permitted Tables:** `{', '.join(sorted(ALLOWED_TABLES))}`")

    default_query = """SELECT 
    d_year,
    COUNT(ss_ticket_number) AS total_orders,
    ROUND(SUM(ss_ext_sales_price), 2) AS total_sales
FROM store_sales
JOIN date_dim ON ss_sold_date_sk = d_date_sk
WHERE d_year IN (1999, 2000)
GROUP BY d_year
ORDER BY d_year ASC
LIMIT 10;"""

    custom_sql = st.text_area(
        "Enter SQL Query (Read-Only SELECT):",
        value=default_query,
        height=180,
    )

    if st.button("▶️ Execute Safe Query", type="primary"):
        if not custom_sql.strip():
            st.warning("Please enter a SQL query.")
        else:
            with st.status("Validating SQL query safety...", expanded=True) as status:
                is_valid, sanitized_sql, err = validate_and_sanitize_sql(custom_sql, default_limit=100)
                if not is_valid:
                    status.update(label="❌ Query Blocked by Safety Policy", state="error")
                    st.error(f"**Safety Rule Violation:** {err}")
                    st.stop()
                status.update(label="✅ Query Validated & Sanitized", state="complete")

            st.code(sanitized_sql, language="sql")

            with st.spinner("Executing query on Snowflake..."):
                res_df, q_time, q_err = execute_snowflake_query(sanitized_sql, max_rows=100)
            
            if q_err:
                st.error(f"Execution Error: {q_err}")
            elif res_df is not None:
                st.success(f"Query completed in {q_time} seconds! Retrieved {len(res_df)} rows.")
                st.dataframe(res_df, use_container_width=True)
                
                # Download button
                csv = res_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Download Results as CSV",
                    data=csv,
                    file_name="snowflake_query_results.csv",
                    mime="text/csv",
                )
