"""
Settings & System Diagnostics Page for DataLens.
Displays Snowflake connectivity status, Qwen3-4B AI inference configuration,
active environment metadata, and configuration guidelines without exposing credentials.
"""

import streamlit as st
from utils.config import get_custom_css, COLORS, APP_NAME, DEFAULT_DATABASE, DEFAULT_SCHEMA
from components.sidebar import render_sidebar
from components.metric_cards import render_demo_banner
from services.snowflake_service import snowflake_service
from services.qwen_service import qwen_service
from utils.formatting import get_status_badge

# Page Setup
st.set_page_config(
    page_title=f"Settings & Status — {APP_NAME}",
    page_icon="⚙️",
    layout="wide",
)
st.markdown(get_custom_css(), unsafe_allow_html=True)
render_sidebar(active_page="Settings")

# Header
st.markdown(
    f"""
    <div>
        <h1 style="font-size: 2rem; font-weight: 800; color: {COLORS['text']}; margin: 0;">
            ⚙️ Settings & System Configuration
        </h1>
        <p style="font-size: 0.95rem; color: #64748B; margin-top: 4px; margin-bottom: 20px;">
            Manage Snowflake credentials, configure the Qwen3-4B inference endpoint, and inspect runtime health.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

status = snowflake_service.get_connection_status()
render_demo_banner(status["is_demo"])

# Tabs: Connections, AI Model, Setup Guide
tab_conn, tab_ai, tab_guide = st.tabs(["❄️ Snowflake Connection", "🤖 Qwen3-4B Model Setup", "📖 Configuration Guide"])

with tab_conn:
    st.markdown("### Snowflake Connection Diagnostics")
    
    col_c1, col_c2 = st.columns([2, 1])
    with col_c1:
        st.markdown(
            f"""
            <div class="datalens-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <span style="font-weight: 700; color: {COLORS['text']};">Connection Mode</span>
                    <span>{get_status_badge(status['mode'])}</span>
                </div>
                <table style="width: 100%; font-size: 0.9rem; line-height: 1.8;">
                    <tr><td style="color: #64748B;">Database:</td><td><b>{status['database']}</b></td></tr>
                    <tr><td style="color: #64748B;">Schema:</td><td><b>{status['schema']}</b></td></tr>
                    <tr><td style="color: #64748B;">Account:</td><td><b>{status.get('account', 'Local')}</b></td></tr>
                    <tr><td style="color: #64748B;">Warehouse:</td><td><b>{status.get('warehouse', 'DEMO_WH')}</b></td></tr>
                    <tr><td style="color: #64748B;">Security:</td><td><span style="color: #10B981; font-weight: 600;">🔒 Read-Only Enforcement</span></td></tr>
                </table>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_c2:
        st.markdown(
            f"""
            <div class="datalens-card">
                <div class="section-title" style="font-size: 1.1rem; margin-top: 0;">Connection Test</div>
                <p style="font-size: 0.8rem; color: #64748B;">Verify direct handshake with your Snowflake instance.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("🔌 Test Snowflake Handshake", use_container_width=True):
            with st.spinner("Testing connection to Snowflake..."):
                is_ok, msg = snowflake_service.test_connection()
                if is_ok:
                    st.success(f"✅ {msg}")
                else:
                    st.warning(f"⚠️ {msg}")
                    st.info("Operating in Demo Mode using local synthetic TPC-DS retail datasets.")

with tab_ai:
    st.markdown("### Qwen3-4B AI Inference Service")
    qwen_cfg = qwen_service.get_config()
    health = qwen_service.check_health()

    col_ai1, col_ai2 = st.columns([2, 1])
    with col_ai1:
        st.markdown(
            f"""
            <div class="datalens-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <span style="font-weight: 700; color: {COLORS['text']};">Model Endpoint Status</span>
                    <span>{get_status_badge(health['status'])}</span>
                </div>
                <table style="width: 100%; font-size: 0.9rem; line-height: 1.8;">
                    <tr><td style="color: #64748B;">Target Model:</td><td><b>{qwen_cfg['model']}</b></td></tr>
                    <tr><td style="color: #64748B;">Configured Endpoint:</td><td><code>{qwen_cfg['endpoint']}</code></td></tr>
                    <tr><td style="color: #64748B;">Health Details:</td><td>{health['details']}</td></tr>
                    <tr><td style="color: #64748B;">Offline Strategy:</td><td>High-fidelity semantic simulation</td></tr>
                </table>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Dynamic Endpoint Configuration
        with st.expander("⚙️ Override AI Endpoint Settings (Current Session)"):
            new_endpoint = st.text_input("Endpoint URL:", value=qwen_cfg["endpoint"])
            new_model = st.text_input("Model Identifier:", value=qwen_cfg["model"])
            new_key = st.text_input("API Key (Optional / Bearer Token):", value="", type="password")
            if st.button("Save AI Settings"):
                st.session_state["qwen_endpoint"] = new_endpoint
                st.session_state["qwen_model"] = new_model
                if new_key:
                    st.session_state["qwen_api_key"] = new_key
                st.success("AI configuration saved for this session!")
                st.rerun()

    with col_ai2:
        st.markdown(
            f"""
            <div class="datalens-card">
                <div class="section-title" style="font-size: 1.1rem; margin-top: 0;">AI Ping Check</div>
                <p style="font-size: 0.8rem; color: #64748B;">Test reachability of Qwen3-4B inference server.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("📡 Ping Qwen3-4B Endpoint", use_container_width=True):
            with st.spinner("Pinging inference endpoint..."):
                h = qwen_service.check_health()
                if h["available"]:
                    st.success(f"✅ {h['status']}: {h['details']}")
                else:
                    st.warning(f"⚠️ {h['status']}: {h['details']}")
                    st.caption("When offline, DataLens uses deterministic simulation. Start Ollama with `ollama run qwen3:4b` to enable live model inference.")

with tab_guide:
    st.markdown("### How to Configure DataLens for Live Production")

    st.markdown(
        """
#### 1. Snowflake Credentials Setup
Create a file named `.streamlit/secrets.toml` in your repository root:

```toml
[snowflake]
account = "your_snowflake_account_identifier"
user = "your_username"
password = "your_strong_password"
warehouse = "COMPUTE_WH"
database = "SNOWFLAKE_SAMPLE_DATA"
schema = "TPCDS_SF10TCL"
role = "ACCOUNTADMIN"
```
> **Security Notice:** `.streamlit/secrets.toml` is included in `.gitignore` and must never be committed to git.

---

#### 2. Running Qwen3-4B Locally via Ollama
To serve the runtime Qwen3-4B model locally:

```bash
# 1. Install Ollama (https://ollama.com)
# 2. Pull and start Qwen3-4B (or Qwen 2.5 3B / 7B)
ollama pull qwen3:4b
ollama run qwen3:4b

# Ollama will automatically serve the model at http://localhost:11434/api/generate
```

In `.streamlit/secrets.toml`:
```toml
[qwen]
endpoint_url = "http://localhost:11434/api/generate"
model_name = "qwen3:4b"
```

---

#### 3. Snowflake CoCo / Cortex Code Development Workflow
During system development, **Snowflake CoCo** is utilized as the developer-facing workbench:
- Explore TPC-DS sample datasets and verify schema definitions (`STORE_SALES`, `ITEM`, `DATE_DIM`).
- Test and benchmark analytical queries before encoding them into application services.
- Keep developer assistant workflows separate from the runtime **Qwen3-4B** inference pipeline.
        """
    )
