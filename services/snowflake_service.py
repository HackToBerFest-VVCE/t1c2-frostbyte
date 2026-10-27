"""Snowflake Database Service for DataLens Live.

Handles secure authentication, query execution, schema inspection,
and connection health checks using snowflake-connector-python.
Credentials are read strictly from .streamlit/secrets.toml.
"""

import time
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
import streamlit as st
import snowflake.connector
from snowflake.connector.errors import DatabaseError, ProgrammingError, OperationalError

# Try importing tomllib for direct secrets parsing
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

# Default target schema details
DEFAULT_DATABASE = "SNOWFLAKE_SAMPLE_DATA"
DEFAULT_SCHEMA = "TPCDS_SF10TCL"
QUERY_TIMEOUT_SECONDS = 45
SECRETS_PATH = Path(".streamlit/secrets.toml")
EXAMPLE_SECRETS_PATH = Path(".streamlit/secrets.toml.example")


def clean_account_identifier(raw_account: str) -> str:
    """Strip protocol, port, slashes, or snowflakecomputing.com domain if present in account string."""
    if not raw_account:
        return ""
    acc = str(raw_account).strip().rstrip("/")
    if acc.startswith("https://"):
        acc = acc[len("https://"):]
    elif acc.startswith("http://"):
        acc = acc[len("http://"):]
    if ".snowflakecomputing.com" in acc:
        acc = acc.split(".snowflakecomputing.com")[0]
    return acc.strip().rstrip("/")


def parse_toml_file(path: Path) -> Optional[Dict[str, Any]]:
    """Read a TOML file from disk safely."""
    if not path.exists():
        return None
    if tomllib is None:
        return None
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
            if "snowflake" in data and isinstance(data["snowflake"], dict):
                return dict(data["snowflake"])
            elif "account" in data:
                return dict(data)
    except Exception:
        pass
    return None


def get_snowflake_config_diagnostics() -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    """
    Inspect the credentials configuration and return diagnostic status.
    NEVER logs or returns plaintext passwords.

    Returns:
        (config_or_none, diagnostic_info)
    """
    file_exists = SECRETS_PATH.exists()
    diag: Dict[str, Any] = {
        "file_exists": file_exists,
        "file_path": str(SECRETS_PATH.resolve()),
        "readable": False,
        "missing_keys": [],
        "placeholder_keys": [],
        "configured_keys": [],
        "error_reason": "",
        "raw_fields": {},
        "loaded_from_example": False,
    }

    sec = None

    # 1. First, check .streamlit/secrets.toml directly from disk
    if file_exists:
        raw_sec = parse_toml_file(SECRETS_PATH)
        if raw_sec:
            diag["readable"] = True
            sec = raw_sec

    # 2. If not found or if .streamlit/secrets.toml only has placeholder keys, check .example
    sec_has_placeholders = (
        sec is not None and any(str(sec.get(k, "")).startswith("YOUR_") for k in ["account", "user", "password"])
    )

    if (sec is None or sec_has_placeholders) and EXAMPLE_SECRETS_PATH.exists():
        example_sec = parse_toml_file(EXAMPLE_SECRETS_PATH)
        if example_sec and not any(str(example_sec.get(k, "")).startswith("YOUR_") for k in ["account", "user", "password"]):
            # Real credentials found in .example file!
            sec = example_sec
            diag["file_path"] = str(EXAMPLE_SECRETS_PATH.resolve())
            diag["readable"] = True
            diag["loaded_from_example"] = True

    # 3. Streamlit secrets fallback if running inside Streamlit
    if not sec:
        try:
            if "snowflake" in st.secrets:
                sec = dict(st.secrets["snowflake"])
                diag["readable"] = True
            elif hasattr(st, "secrets") and "account" in st.secrets:
                sec = dict(st.secrets)
                diag["readable"] = True
        except Exception:
            pass

    if not file_exists and not diag["loaded_from_example"]:
        diag["error_reason"] = (
            "Configuration file '.streamlit/secrets.toml' does not exist. "
            "Please copy '.streamlit/secrets.toml.example' to '.streamlit/secrets.toml' and enter credentials."
        )
        return None, diag

    if not sec:
        diag["error_reason"] = "Could not parse '[snowflake]' table from secrets.toml. Verify valid TOML syntax."
        return None, diag

    # Populate raw_fields with password masked
    diag["raw_fields"] = {
        k: ("*" * len(str(v)) if k == "password" else str(v))
        for k, v in sec.items()
    }

    # Determine authentication method (defaults to standard 'snowflake' password auth)
    auth_method = str(sec.get("authenticator", "snowflake")).strip().lower()

    # Validate required fields: password is required for 'snowflake' auth, optional for 'externalbrowser'
    required_keys = ["account", "user", "warehouse"]
    if auth_method in ("snowflake", ""):
        required_keys.append("password")

    optional_keys = ["database", "schema", "role", "authenticator"]

    for k in required_keys:
        val = sec.get(k)
        if val is None or str(val).strip() == "":
            diag["missing_keys"].append(k)
        elif str(val).startswith("YOUR_"):
            diag["placeholder_keys"].append(k)
        else:
            diag["configured_keys"].append(k)

    for k in optional_keys:
        val = sec.get(k)
        if val is not None and str(val).strip() != "" and not str(val).startswith("YOUR_"):
            diag["configured_keys"].append(k)

    if diag["missing_keys"] or diag["placeholder_keys"]:
        reasons = []
        if diag["missing_keys"]:
            reasons.append(f"Missing required fields: {', '.join(diag['missing_keys'])}")
        if diag["placeholder_keys"]:
            reasons.append(f"Fields still set to placeholder values: {', '.join(diag['placeholder_keys'])}")
        diag["error_reason"] = " | ".join(reasons)
        return None, diag

    # Clean account identifier
    raw_acc = str(sec.get("account")).strip()
    cleaned_acc = clean_account_identifier(raw_acc)

    cfg = {
        "account": cleaned_acc,
        "user": str(sec.get("user")).strip(),
        "password": str(sec.get("password", "")),
        "warehouse": str(sec.get("warehouse")).strip(),
        "database": str(sec.get("database", DEFAULT_DATABASE)).strip(),
        "schema": str(sec.get("schema", DEFAULT_SCHEMA)).strip(),
        "role": str(sec.get("role", "")).strip() or None,
        "authenticator": auth_method,
    }

    return cfg, diag


def get_snowflake_config() -> Optional[Dict[str, Any]]:
    """
    Retrieve Snowflake credentials if properly configured.
    Never hardcodes credentials or creates synthetic connections.
    """
    cfg, _ = get_snowflake_config_diagnostics()
    return cfg


def get_connection(config: Dict[str, Any] = None):
    """
    Create a new Snowflake connection with strict timeouts.
    """
    cfg = config or get_snowflake_config()
    if not cfg:
        raise ValueError("Snowflake credentials are not configured in .streamlit/secrets.toml")

    conn_kwargs = {
        "user": cfg["user"],
        "account": cfg["account"],
        "warehouse": cfg["warehouse"],
        "database": cfg.get("database", DEFAULT_DATABASE),
        "schema": cfg.get("schema", DEFAULT_SCHEMA),
        "login_timeout": 20,
        "network_timeout": 30,
        "client_session_keep_alive": False,
        "enable_server_session_keep_alive_auto_detection": False,
        "session_parameters": {
            "STATEMENT_TIMEOUT_IN_SECONDS": QUERY_TIMEOUT_SECONDS,
            "QUERY_TAG": "DataLens_Live_Streamlit",
        }
    }
    if cfg.get("password"):
        conn_kwargs["password"] = cfg["password"]
    if cfg.get("authenticator") and cfg["authenticator"] != "snowflake":
        conn_kwargs["authenticator"] = cfg["authenticator"]
    if cfg.get("role"):
        conn_kwargs["role"] = cfg["role"]

    return snowflake.connector.connect(**conn_kwargs)


def classify_snowflake_error(e: Exception) -> Tuple[str, str, str]:
    """
    Safely categorize Snowflake connector errors without exposing credentials.
    Returns:
        (category: str, code: str, recommendation: str)
    """
    err_text = e.msg if hasattr(e, 'msg') else str(e)
    errno = str(getattr(e, 'errno', 'UNKNOWN'))

    if "390102" in err_text or errno == "390102" or "temporarily locked" in err_text:
        return (
            "ACCOUNT_TEMPORARILY_LOCKED",
            "390102",
            (
                "Your Snowflake user account has been temporarily locked by Snowflake's security policy "
                "due to multiple consecutive failed password attempts.\n"
                "  1. [Automatic Unlock]: Snowflake accounts automatically unlock after 15 minutes.\n"
                "  2. [Immediate Snowsight Unlock]: If you are logged in to the Snowflake Web UI (Snowsight), "
                "open a Worksheet and run:\n"
                "       ALTER USER CURRENT_USER() SET MINS_TO_UNLOCK = 0;\n"
                "  3. [Browser-based SSO]: If you use Google or SSO to log in, add 'authenticator = \"externalbrowser\"' "
                "in .streamlit/secrets.toml."
            )
        )
    elif "390100" in err_text or errno == "390100" or "Incorrect username or password" in err_text:
        return (
            "AUTHENTICATION_CREDENTIAL_OR_MFA_MISMATCH",
            "390100",
            (
                "Snowflake rejected the username or password. Key diagnostic possibilities:\n"
                "  1. [Login Name vs User Name]: In Snowflake, your LOGIN_NAME might be your email address. "
                "Check by logging into Snowsight and inspecting 'DESC USER CURRENT_USER();'.\n"
                "  2. [SSO / Google Sign-In]: If your account uses 'Sign in with Google' or Microsoft SSO, native password "
                "auth is disabled. Set 'authenticator = \"externalbrowser\"' in .streamlit/secrets.toml.\n"
                "  3. [MFA Enforced]: If Multi-Factor Authentication is enrolled for your user, password-only "
                "connector login is blocked. Set 'authenticator = \"externalbrowser\"' to log in via browser."
            )
        )
    elif "250001" in err_text or "404 Not Found" in err_text:
        return (
            "ACCOUNT_ENDPOINT_NOT_FOUND",
            "250001",
            "The account identifier host does not exist or returned 404. Verify account identifier in Snowsight."
        )
    elif "warehouse" in err_text.lower():
        return (
            "WAREHOUSE_CONFIGURATION_ERROR",
            errno,
            "Warehouse is inactive, not found, or user lacks USAGE privilege."
        )
    return (
        "GENERAL_DATABASE_ERROR",
        errno,
        f"Database error ({errno}): {err_text}"
    )


def test_connection() -> Tuple[bool, Dict[str, Any], str]:
    """
    Test Snowflake connectivity with a small, inexpensive query:
    SELECT CURRENT_VERSION(), CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_SCHEMA(), CURRENT_ROLE()
    Returns:
        (is_connected: bool, info_dict: dict, error_message: str)
    """
    cfg, diag = get_snowflake_config_diagnostics()
    if not cfg:
        reason = diag.get("error_reason", "Credentials missing.")
        return (
            False,
            {},
            f"{reason}"
        )

    start_time = time.time()
    try:
        with get_connection(cfg) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT CURRENT_VERSION(), CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_SCHEMA(), CURRENT_ROLE()"
                )
                row = cur.fetchone()
                latency_ms = round((time.time() - start_time) * 1000, 1)
                
                info = {
                    "version": row[0] if row else "Unknown",
                    "warehouse": row[1] if row else cfg.get("warehouse"),
                    "database": row[2] if row else cfg.get("database"),
                    "schema": row[3] if row else cfg.get("schema"),
                    "role": row[4] if row else cfg.get("role", "N/A"),
                    "latency_ms": latency_ms,
                    "account": cfg.get("account"),
                    "user": cfg.get("user"),
                    "authenticator": cfg.get("authenticator", "snowflake"),
                }
                return True, info, ""
    except (DatabaseError, ProgrammingError, OperationalError) as e:
        category, code, recommendation = classify_snowflake_error(e)
        err_msg = (
            f"Snowflake Connector Error [{code}] ({category}): "
            f"{e.msg if hasattr(e, 'msg') else str(e)}\n\n"
            f"Recommendations:\n{recommendation}"
        )
        return False, {"error_category": category, "error_code": code}, err_msg
    except Exception as e:
        return False, {"error_category": "UNEXPECTED_ERROR"}, f"Snowflake Connection Failed: {str(e)}"


def execute_snowflake_query(sql: str, max_rows: int = 100) -> Tuple[Optional[pd.DataFrame], float, str]:
    """
    Execute a validated SELECT query against Snowflake and return a Pandas DataFrame.

    Returns:
        (df: pd.DataFrame or None, execution_time_sec: float, error_message: str)
    """
    cfg = get_snowflake_config()
    if not cfg:
        return None, 0.0, "Credentials missing. Configure .streamlit/secrets.toml first."

    start_time = time.time()
    try:
        with get_connection(cfg) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                # Fetch results up to max_rows
                rows = cur.fetchmany(max_rows)
                columns = [col[0] for col in cur.description] if cur.description else []
                df = pd.DataFrame(rows, columns=columns)
                elapsed = round(time.time() - start_time, 2)
                return df, elapsed, ""
    except (DatabaseError, ProgrammingError, OperationalError) as e:
        elapsed = round(time.time() - start_time, 2)
        error_msg = e.msg if hasattr(e, 'msg') else str(e)
        return None, elapsed, f"Snowflake execution error: {error_msg}"
    except Exception as e:
        elapsed = round(time.time() - start_time, 2)
        return None, elapsed, f"Unexpected error during query execution: {str(e)}"


def inspect_schema(database: str = DEFAULT_DATABASE, schema: str = DEFAULT_SCHEMA) -> Dict[str, List[str]]:
    """
    Inspect the actual available tables and column names in Snowflake.
    Does not assume tables or columns exist.
    """
    cfg = get_snowflake_config()
    if not cfg:
        return {}

    db = database or cfg.get("database", DEFAULT_DATABASE)
    sch = schema or cfg.get("schema", DEFAULT_SCHEMA)

    query = f"""
    SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
    FROM {db}.INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = '{sch.upper()}'
    ORDER BY TABLE_NAME, ORDINAL_POSITION
    """

    df, _, err = execute_snowflake_query(query, max_rows=1000)
    if df is None or df.empty:
        # Fallback to SHOW TABLES if INFORMATION_SCHEMA access is restricted
        tables_query = f"SHOW TABLES IN SCHEMA {db}.{sch}"
        tdf, _, terr = execute_snowflake_query(tables_query, max_rows=100)
        if tdf is not None and not tdf.empty:
            tbl_col = "name" if "name" in tdf.columns else tdf.columns[1]
            return {tbl: [] for tbl in tdf[tbl_col].tolist()}
        return {}

    schema_map: Dict[str, List[str]] = {}
    for _, row in df.iterrows():
        tname = str(row["TABLE_NAME"]).upper()
        cname = str(row["COLUMN_NAME"]).upper()
        if tname not in schema_map:
            schema_map[tname] = []
        schema_map[tname].append(cname)

    return schema_map
