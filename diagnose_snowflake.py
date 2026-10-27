"""Snowflake Connection Diagnostic Tool for DataLens Live.

Run this script to test and diagnose Snowflake connectivity:
    python diagnose_snowflake.py

Strict Security Guarantee:
Never displays, logs, or transmits plain-text passwords.
"""

import sys
import snowflake.connector
from services.snowflake_service import (
    get_snowflake_config_diagnostics,
    test_connection,
    SECRETS_PATH,
    clean_account_identifier,
)

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def run_diagnostics():
    print("=" * 65)
    print(" 🔍 DataLens Live — Snowflake Connection Diagnostic")
    print("=" * 65)
    print(f"📦 snowflake-connector-python version: {snowflake.connector.__version__}")

    cfg, diag = get_snowflake_config_diagnostics()
    cfg_safe = cfg or {}
    raw_fields = diag.get("raw_fields", {})

    print(f"1. Configuration File Check:")
    print(f"   Target path: {diag['file_path']}")
    if not diag["file_exists"]:
        print("   Status: ❌ NOT FOUND")
        print("\n   [ACTION REQUIRED]")
        print("   Please create '.streamlit/secrets.toml' by copying the example:")
        print("   PowerShell command:")
        print("       Copy-Item .streamlit\\secrets.toml.example .streamlit\\secrets.toml")
        print("\n   Then open '.streamlit/secrets.toml' and enter your credentials.")
        print("=" * 65)
        return

    print("   Status: ✅ Found")
    print(f"   Readable TOML: {'✅ Yes' if diag['readable'] else '❌ Parsing Error'}")

    # Check if credentials were found in .example file
    if diag.get("loaded_from_example"):
        print("   ⚠️ Notice: Credentials were read from '.streamlit/secrets.toml.example'.")
        print("   To secure your credentials from git, save them in '.streamlit/secrets.toml'.")

    print("\n2. Field Validation & Authentication Configuration:")
    required_fields = ["account", "user", "warehouse"]
    auth_method = cfg_safe.get("authenticator", raw_fields.get("authenticator", "snowflake"))
    if auth_method in ("snowflake", ""):
        required_fields.append("password")

    optional_fields = ["database", "schema", "role", "authenticator"]

    for field in required_fields:
        if field in diag["missing_keys"]:
            print(f"   - {field}: ❌ MISSING")
        elif field in diag["placeholder_keys"]:
            val_preview = raw_fields.get(field, "")
            print(f"   - {field}: ⚠️ PLACEHOLDER DETECTED ('{val_preview}') — Please update in .streamlit/secrets.toml")
        else:
            if field == "password":
                pwd_len = len(raw_fields.get("password", "")) or (len(cfg_safe["password"]) if "password" in cfg_safe else 0)
                print(f"   - password: ✅ Configured ({pwd_len} chars, masked)")
            elif field == "account":
                acc_val = cfg_safe.get("account", raw_fields.get("account", ""))
                print(f"   - account: ✅ '{acc_val}'")
            else:
                f_val = cfg_safe.get(field, raw_fields.get(field, ""))
                print(f"   - {field}: ✅ '{f_val}'")

    for field in optional_fields:
        if field in diag["configured_keys"]:
            opt_val = cfg_safe.get(field, raw_fields.get(field, ""))
            print(f"   - {field}: ✅ '{opt_val}'")
        else:
            default_val = "snowflake (native password)" if field == "authenticator" else "default"
            print(f"   - {field}: (Using {default_val})")

    if not cfg:
        print("\n   [ACTION REQUIRED]")
        print(f"   Configuration incomplete: {diag['error_reason']}")
        print("=" * 65)
        return

    print("\n3. Testing Live Snowflake Connection...")
    print(f"   Active Authenticator Method: '{cfg.get('authenticator', 'snowflake')}'")
    print("   Executing test query: SELECT CURRENT_VERSION(), CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_SCHEMA()")
    connected, info, err = test_connection()

    if connected:
        print("\n   🟢 SUCCESS: Connected to Snowflake!")
        print(f"   - Snowflake Version: {info.get('version')}")
        print(f"   - Active Warehouse:  {info.get('warehouse')}")
        print(f"   - Active Database:   {info.get('database')}")
        print(f"   - Active Schema:     {info.get('schema')}")
        print(f"   - User Role:         {info.get('role')}")
        print(f"   - Authenticator:     {info.get('authenticator', 'snowflake')}")
        print(f"   - Network Ping:      {info.get('latency_ms')} ms")
        print("\n   Your DataLens Live dashboard is ready to query real Snowflake data.")
    else:
        err_cat = info.get("error_category", "UNKNOWN_CATEGORY")
        print(f"\n   🔴 AUTHENTICATION FAILED")
        print(f"   - Error Category: {err_cat}")
        print(f"\n{err}")
    print("=" * 65)


if __name__ == "__main__":
    run_diagnostics()
