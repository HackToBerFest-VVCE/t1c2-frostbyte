"""
Snowflake Integration & Execution Service for DataLens.

Supports:
- Live Snowflake connectivity using snowflake-connector-python.
- Safe query execution against SNOWFLAKE_SAMPLE_DATA.TPCDS_SF10TCL.
- Automatic, seamless fallback to local DuckDB demo engine when credentials are absent or connection fails.
- Never hardcodes credentials or exposes secrets.
"""

import os
import time
from typing import Dict, Any, Tuple, Optional, List
import pandas as pd
import duckdb
from utils.config import (
    DEFAULT_DATABASE,
    DEFAULT_SCHEMA,
    APPROVED_TABLES,
    DEMO_WARNING_TEXT,
)

try:
    import streamlit as st
except ImportError:
    st = None

try:
    import snowflake.connector
    SNOWFLAKE_AVAILABLE = True
except ImportError:
    SNOWFLAKE_AVAILABLE = False


class SnowflakeService:
    """Manages database connectivity, metadata exploration, and query execution."""

    def __init__(self):
        self._demo_conn: Optional[duckdb.DuckDBPyConnection] = None
        self._init_demo_engine()

    def _init_demo_engine(self):
        """Initializes in-memory DuckDB populated with the retail demo datasets."""
        try:
            self._demo_conn = duckdb.connect(database=":memory:")
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, "data")

            # Load consolidated table
            retail_csv = os.path.join(data_dir, "demo_retail_data.csv")
            if os.path.exists(retail_csv):
                retail_csv_clean = retail_csv.replace('\\', '/')
                self._demo_conn.execute(
                    f"CREATE OR REPLACE TABLE demo_retail_data AS SELECT * FROM read_csv_auto('{retail_csv_clean}')"
                )

            # Load TPC-DS format tables
            table_mappings = {
                "store_sales": "demo_store_sales.csv",
                "web_sales": "demo_web_sales.csv",
                "catalog_sales": "demo_catalog_sales.csv",
                "item": "demo_item.csv",
                "customer": "demo_customer.csv",
                "date_dim": "demo_date_dim.csv",
            }
            for tbl, fname in table_mappings.items():
                fpath = os.path.join(data_dir, fname)
                if os.path.exists(fpath):
                    fpath_clean = fpath.replace("\\", "/")
                    self._demo_conn.execute(
                        f"CREATE OR REPLACE TABLE {tbl} AS SELECT * FROM read_csv_auto('{fpath_clean}')"
                    )
        except Exception as e:
            print(f"Error initializing demo DuckDB engine: {e}")

    def get_credentials(self) -> Dict[str, str]:
        """Safely extracts Snowflake credentials from Streamlit secrets or environment."""
        creds = {}

        # 1. Try Streamlit secrets safely
        try:
            if st and hasattr(st, "secrets") and "snowflake" in st.secrets:
                sec = st.secrets["snowflake"]
                creds["account"] = sec.get("account", "")
                creds["user"] = sec.get("user", "")
                creds["password"] = sec.get("password", "")
                creds["warehouse"] = sec.get("warehouse", "COMPUTE_WH")
                creds["database"] = sec.get("database", DEFAULT_DATABASE)
                creds["schema"] = sec.get("schema", DEFAULT_SCHEMA)
                creds["role"] = sec.get("role", "ACCOUNTADMIN")
        except Exception:
            pass

        # 2. Override with Environment Variables if set
        creds["account"] = os.getenv("SNOWFLAKE_ACCOUNT", creds.get("account", ""))
        creds["user"] = os.getenv("SNOWFLAKE_USER", creds.get("user", ""))
        creds["password"] = os.getenv("SNOWFLAKE_PASSWORD", creds.get("password", ""))
        creds["warehouse"] = os.getenv("SNOWFLAKE_WAREHOUSE", creds.get("warehouse", "COMPUTE_WH"))
        creds["database"] = os.getenv("SNOWFLAKE_DATABASE", creds.get("database", DEFAULT_DATABASE))
        creds["schema"] = os.getenv("SNOWFLAKE_SCHEMA", creds.get("schema", DEFAULT_SCHEMA))
        creds["role"] = os.getenv("SNOWFLAKE_ROLE", creds.get("role", "ACCOUNTADMIN"))

        return creds

    def has_valid_credentials(self) -> bool:
        """Checks if Snowflake credentials are configured."""
        creds = self.get_credentials()
        return bool(
            creds.get("account")
            and creds.get("user")
            and creds.get("password")
            and creds.get("account") != "your_snowflake_account_id"
        )

    def test_connection(self) -> Tuple[bool, str]:
        """Tests live connection to Snowflake."""
        if not SNOWFLAKE_AVAILABLE:
            return False, "snowflake-connector-python package is not installed."

        if not self.has_valid_credentials():
            return False, "Snowflake credentials are not configured in .streamlit/secrets.toml or environment variables."

        creds = self.get_credentials()
        try:
            ctx = snowflake.connector.connect(
                account=creds["account"],
                user=creds["user"],
                password=creds["password"],
                warehouse=creds.get("warehouse"),
                database=creds.get("database", DEFAULT_DATABASE),
                schema=creds.get("schema", DEFAULT_SCHEMA),
                role=creds.get("role"),
                login_timeout=10,
            )
            cur = ctx.cursor()
            cur.execute("SELECT CURRENT_VERSION()")
            ver = cur.fetchone()[0]
            cur.close()
            ctx.close()
            return True, f"Successfully connected to Snowflake (Version: {ver})."
        except Exception as e:
            return False, f"Snowflake connection failed: {str(e)}"

    def get_connection_status(self) -> Dict[str, Any]:
        """Returns structured connection status dictionary."""
        is_live = False
        message = ""
        creds = self.get_credentials()

        if self.has_valid_credentials():
            is_live, message = self.test_connection()

        if is_live:
            return {
                "mode": "Live Snowflake",
                "is_live": True,
                "is_demo": False,
                "database": creds.get("database", DEFAULT_DATABASE),
                "schema": creds.get("schema", DEFAULT_SCHEMA),
                "account": creds.get("account", "Configured"),
                "warehouse": creds.get("warehouse", "COMPUTE_WH"),
                "status_label": "Connected (Snowflake)",
                "banner_needed": False,
                "message": message,
            }
        else:
            return {
                "mode": "Demo Mode",
                "is_live": False,
                "is_demo": True,
                "database": "DEMO_SNOWFLAKE_SAMPLE_DATA",
                "schema": "TPCDS_SF10TCL_DEMO",
                "account": "Local Synthetic Engine",
                "warehouse": "DEMO_WH",
                "status_label": "Demo Mode (Local Data)",
                "banner_needed": True,
                "message": message if message else "No live credentials provided. Running in high-fidelity Demo Mode.",
            }

    def execute_query(self, sql: str, timeout_seconds: int = 30) -> Tuple[pd.DataFrame, float, bool, Optional[str]]:
        """
        Executes an approved SQL query against Snowflake or fallback Demo engine.

        Returns:
            Tuple[pd.DataFrame, float, bool, Optional[str]]:
                (results_dataframe, duration_seconds, is_demo_data, error_message)
        """
        start_time = time.time()
        conn_status = self.get_connection_status()

        if conn_status["is_live"]:
            creds = self.get_credentials()
            try:
                ctx = snowflake.connector.connect(
                    account=creds["account"],
                    user=creds["user"],
                    password=creds["password"],
                    warehouse=creds.get("warehouse"),
                    database=creds.get("database", DEFAULT_DATABASE),
                    schema=creds.get("schema", DEFAULT_SCHEMA),
                    role=creds.get("role"),
                    network_timeout=timeout_seconds,
                )
                cur = ctx.cursor()
                cur.execute(sql)
                col_names = [desc[0] for desc in cur.description] if cur.description else []
                rows = cur.fetchall()
                df = pd.DataFrame(rows, columns=col_names)
                cur.close()
                ctx.close()

                duration = time.time() - start_time
                return df, duration, False, None
            except Exception as e:
                # Live failed - fallback to demo engine with error notice
                err = str(e)
                print(f"Snowflake query execution error: {err}. Falling back to demo mode.")
                df, dur, _, _ = self._execute_demo_query(sql)
                return df, dur, True, f"Live query failed ({err}). Showing Demo results."

        # Demo mode execution
        df, duration, is_demo, err = self._execute_demo_query(sql)
        return df, duration, is_demo, err

    def _execute_demo_query(self, sql: str) -> Tuple[pd.DataFrame, float, bool, Optional[str]]:
        """Executes query in the local DuckDB demo engine with translation for TPC-DS schema."""
        start_time = time.time()
        if self._demo_conn is None:
            self._init_demo_engine()

        # Sanitize snowflake-specific prefixes: remove 'SNOWFLAKE_SAMPLE_DATA.TPCDS_SF10TCL.'
        translated_sql = sql.replace("SNOWFLAKE_SAMPLE_DATA.TPCDS_SF10TCL.", "")
        translated_sql = translated_sql.replace("snowflake_sample_data.tpcds_sf10tcl.", "")

        try:
            df = self._demo_conn.execute(translated_sql).fetchdf()
            duration = time.time() - start_time
            return df, duration, True, None
        except Exception as e:
            # If standard query failed, attempt query against consolidated demo_retail_data
            try:
                # Fallback to consolidated query if complex join failed in demo
                simple_fallback = "SELECT date, channel, item_name, category, quantity, unit_price, sales_amount, net_profit FROM demo_retail_data LIMIT 50"
                df = self._demo_conn.execute(simple_fallback).fetchdf()
                duration = time.time() - start_time
                return df, duration, True, f"Direct query note: {str(e)}. Displayed demo retail records."
            except Exception as e2:
                duration = time.time() - start_time
                return pd.DataFrame(), duration, True, f"Demo engine execution error: {str(e)}"

    def get_available_tables(self) -> List[str]:
        """Returns approved tables list."""
        return APPROVED_TABLES

    def get_table_schema(self, table_name: str) -> pd.DataFrame:
        """Returns columns and types for a given table."""
        tbl = table_name.upper()
        if tbl not in APPROVED_TABLES:
            return pd.DataFrame()

        # Check if live
        status = self.get_connection_status()
        if status["is_live"]:
            try:
                sql = f"DESCRIBE TABLE {tbl}"
                df, _, _, err = self.execute_query(sql)
                if not err and not df.empty:
                    return df[["name", "type", "null?", "default", "comment"]]
            except Exception:
                pass

        # Demo schema definitions
        schemas = {
            "STORE_SALES": [
                {"Column": "ss_sold_date_sk", "Type": "INTEGER", "Description": "Date foreign key (DATE_DIM.d_date_sk)"},
                {"Column": "ss_item_sk", "Type": "INTEGER", "Description": "Item foreign key (ITEM.i_item_sk)"},
                {"Column": "ss_customer_sk", "Type": "INTEGER", "Description": "Customer key (CUSTOMER.c_customer_sk)"},
                {"Column": "ss_quantity", "Type": "INTEGER", "Description": "Number of units sold"},
                {"Column": "ss_wholesale_cost", "Type": "DECIMAL(7,2)", "Description": "Wholesale acquisition cost per unit"},
                {"Column": "ss_list_price", "Type": "DECIMAL(7,2)", "Description": "Catalog / MSRP list price"},
                {"Column": "ss_sales_price", "Type": "DECIMAL(7,2)", "Description": "Actual sales price charged"},
                {"Column": "ss_ext_sales_price", "Type": "DECIMAL(7,2)", "Description": "Extended sales amount (total revenue)"},
                {"Column": "ss_net_profit", "Type": "DECIMAL(7,2)", "Description": "Net profit margin"},
            ],
            "WEB_SALES": [
                {"Column": "ws_sold_date_sk", "Type": "INTEGER", "Description": "Date foreign key (DATE_DIM.d_date_sk)"},
                {"Column": "ws_item_sk", "Type": "INTEGER", "Description": "Item foreign key (ITEM.i_item_sk)"},
                {"Column": "ws_bill_customer_sk", "Type": "INTEGER", "Description": "Billing customer key"},
                {"Column": "ws_quantity", "Type": "INTEGER", "Description": "Number of units sold online"},
                {"Column": "ws_wholesale_cost", "Type": "DECIMAL(7,2)", "Description": "Wholesale acquisition cost"},
                {"Column": "ws_list_price", "Type": "DECIMAL(7,2)", "Description": "Online list price"},
                {"Column": "ws_sales_price", "Type": "DECIMAL(7,2)", "Description": "Actual online selling price"},
                {"Column": "ws_ext_sales_price", "Type": "DECIMAL(7,2)", "Description": "Extended web sales amount"},
                {"Column": "ws_net_profit", "Type": "DECIMAL(7,2)", "Description": "Net profit margin"},
            ],
            "CATALOG_SALES": [
                {"Column": "cs_sold_date_sk", "Type": "INTEGER", "Description": "Date foreign key (DATE_DIM.d_date_sk)"},
                {"Column": "cs_item_sk", "Type": "INTEGER", "Description": "Item foreign key (ITEM.i_item_sk)"},
                {"Column": "cs_bill_customer_sk", "Type": "INTEGER", "Description": "Customer identifier"},
                {"Column": "cs_quantity", "Type": "INTEGER", "Description": "Number of units ordered via catalog"},
                {"Column": "cs_wholesale_cost", "Type": "DECIMAL(7,2)", "Description": "Wholesale unit cost"},
                {"Column": "cs_list_price", "Type": "DECIMAL(7,2)", "Description": "Catalog list price"},
                {"Column": "cs_sales_price", "Type": "DECIMAL(7,2)", "Description": "Final catalog sales price"},
                {"Column": "cs_ext_sales_price", "Type": "DECIMAL(7,2)", "Description": "Extended catalog revenue"},
                {"Column": "cs_net_profit", "Type": "DECIMAL(7,2)", "Description": "Catalog net profit"},
            ],
            "ITEM": [
                {"Column": "i_item_sk", "Type": "INTEGER", "Description": "Unique item surrogate key"},
                {"Column": "i_item_id", "Type": "VARCHAR(16)", "Description": "Item product code / SKU"},
                {"Column": "i_product_name", "Type": "VARCHAR(128)", "Description": "Full product title"},
                {"Column": "i_item_desc", "Type": "VARCHAR(256)", "Description": "Product details description"},
                {"Column": "i_category", "Type": "VARCHAR(50)", "Description": "Merchandise category"},
                {"Column": "i_brand", "Type": "VARCHAR(50)", "Description": "Manufacturer brand"},
                {"Column": "i_class", "Type": "VARCHAR(50)", "Description": "Merchandise classification"},
                {"Column": "i_current_price", "Type": "DECIMAL(7,2)", "Description": "Current selling price"},
                {"Column": "i_wholesale_cost", "Type": "DECIMAL(7,2)", "Description": "Wholesale cost"},
            ],
            "CUSTOMER": [
                {"Column": "c_customer_sk", "Type": "INTEGER", "Description": "Unique customer surrogate key"},
                {"Column": "c_customer_id", "Type": "VARCHAR(16)", "Description": "Customer account ID"},
                {"Column": "c_first_name", "Type": "VARCHAR(64)", "Description": "Given name"},
                {"Column": "c_last_name", "Type": "VARCHAR(64)", "Description": "Family name"},
                {"Column": "c_email_address", "Type": "VARCHAR(128)", "Description": "Contact email address"},
            ],
            "DATE_DIM": [
                {"Column": "d_date_sk", "Type": "INTEGER", "Description": "Date surrogate key (YYYYMMDD)"},
                {"Column": "d_date_id", "Type": "VARCHAR(16)", "Description": "Date string"},
                {"Column": "d_date", "Type": "DATE", "Description": "Calendar date"},
                {"Column": "d_year", "Type": "INTEGER", "Description": "Calendar year"},
                {"Column": "d_moy", "Type": "INTEGER", "Description": "Month of year (1-12)"},
                {"Column": "d_dom", "Type": "INTEGER", "Description": "Day of month (1-31)"},
                {"Column": "d_qoy", "Type": "INTEGER", "Description": "Quarter of year (1-4)"},
                {"Column": "d_month_name", "Type": "VARCHAR(16)", "Description": "Full month name (e.g. October)"},
                {"Column": "d_holiday", "Type": "CHAR(1)", "Description": "Holiday indicator (Y/N)"},
                {"Column": "d_weekend", "Type": "CHAR(1)", "Description": "Weekend indicator (Y/N)"},
            ],
        }

        if tbl in schemas:
            return pd.DataFrame(schemas[tbl])
        return pd.DataFrame()

    def preview_table(self, table_name: str, limit: int = 10) -> Tuple[pd.DataFrame, bool, Optional[str]]:
        """Safely fetches top N rows of an approved table with LIMIT enforcement."""
        tbl = table_name.upper()
        if tbl not in APPROVED_TABLES:
            return pd.DataFrame(), True, f"Table '{table_name}' is not an approved retail table."

        sql = f"SELECT * FROM {tbl} LIMIT {min(limit, 50)}"
        df, _, is_demo, err = self.execute_query(sql)
        return df, is_demo, err


# Global singleton instance
snowflake_service = SnowflakeService()
