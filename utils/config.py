"""
Configuration and UI styling constants for DataLens.
Adheres strictly to the defined color palette:
- Background: #EEF2FF (very light blue/lavender)
- Main cards: #FFFFFF (white)
- Primary buttons: #4169E1 (royal blue)
- Highlights: #8B5CF6 (purple)
- Secondary accents: #BAE6FD (light blue)
- Text: #172554 (dark navy)
- Borders: #E5E7EB (soft light grey)
- Shadows: subtle, soft grey
"""

APP_NAME = "DataLens"
APP_TAGLINE = "AI-Powered Retail Sales Intelligence & Analytics"
DEMO_WARNING_TEXT = "DEMO DATA — NOT LIVE SNOWFLAKE RESULTS"

# Exact Color Palette
COLORS = {
    "background": "#EEF2FF",
    "card_bg": "#FFFFFF",
    "primary": "#4169E1",
    "highlight": "#8B5CF6",
    "secondary": "#BAE6FD",
    "text": "#172554",
    "border": "#E5E7EB",
    "success": "#10B981",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "chart_palette": ["#4169E1", "#8B5CF6", "#0284C7", "#38BDF8", "#A78BFA", "#6366F1"],
}

# Approved Snowflake Sample Tables
APPROVED_TABLES = [
    "STORE_SALES",
    "WEB_SALES",
    "CATALOG_SALES",
    "ITEM",
    "CUSTOMER",
    "DATE_DIM",
]

DEFAULT_DATABASE = "SNOWFLAKE_SAMPLE_DATA"
DEFAULT_SCHEMA = "TPCDS_SF10TCL"

# Schema Metadata for Qwen3-4B Context
SCHEMA_CONTEXT = """
Database: SNOWFLAKE_SAMPLE_DATA
Schema: TPCDS_SF10TCL

Available Tables & Key Columns:
1. STORE_SALES (ss_sold_date_sk, ss_item_sk, ss_customer_sk, ss_quantity, ss_wholesale_cost, ss_list_price, ss_sales_price, ss_ext_sales_price, ss_net_paid, ss_net_profit)
   - Fact table for in-store retail transactions.
   - ss_ext_sales_price represents extended sales amount (total price).
   - ss_quantity represents number of units sold.

2. WEB_SALES (ws_sold_date_sk, ws_item_sk, ws_bill_customer_sk, ws_quantity, ws_wholesale_cost, ws_list_price, ws_sales_price, ws_ext_sales_price, ws_net_paid, ws_net_profit)
   - Fact table for online e-commerce transactions.
   - ws_ext_sales_price represents extended online sales amount.
   - ws_quantity represents units sold.

3. CATALOG_SALES (cs_sold_date_sk, cs_item_sk, cs_bill_customer_sk, cs_quantity, cs_wholesale_cost, cs_list_price, cs_sales_price, cs_ext_sales_price, cs_net_paid, cs_net_profit)
   - Fact table for mail-order / catalog sales.
   - cs_ext_sales_price represents extended catalog sales amount.
   - cs_quantity represents units sold.

4. ITEM (i_item_sk, i_item_id, i_item_desc, i_current_price, i_wholesale_cost, i_brand, i_class, i_category, i_product_name)
   - Dimension table for retail inventory products.
   - Join key: ITEM.i_item_sk = STORE_SALES.ss_item_sk (or ws_item_sk / cs_item_sk)
   - i_category represents product category (e.g., Electronics, Apparel, Home, Books).
   - i_product_name or i_item_desc represents product description.

5. CUSTOMER (c_customer_sk, c_customer_id, c_current_cdemo_sk, c_current_hdemo_sk, c_first_name, c_last_name, c_preferred_cust_flag, c_birth_country, c_email_address)
   - Dimension table for retail customers.
   - Join key: CUSTOMER.c_customer_sk = STORE_SALES.ss_customer_sk

6. DATE_DIM (d_date_sk, d_date_id, d_date, d_month_seq, d_year, d_moy, d_dom, d_qoy, d_holiday, d_weekend)
   - Date dimension table.
   - Join key: DATE_DIM.d_date_sk = STORE_SALES.ss_sold_date_sk (or ws_sold_date_sk / cs_sold_date_sk)
   - d_year represents year, d_moy represents month of year (1-12), d_date represents calendar date.
"""

def get_custom_css() -> str:
    """Returns CSS injection string for consistent styling across all pages."""
    return f"""
    <style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        color: {COLORS['text']};
    }}

    /* Global Background */
    .stApp {{
        background-color: {COLORS['background']};
    }}

    /* Card Containers */
    .datalens-card {{
        background-color: {COLORS['card_bg']};
        border-radius: 12px;
        padding: 24px;
        border: 1px solid {COLORS['border']};
        box-shadow: 0 4px 12px rgba(23, 37, 84, 0.05);
        margin-bottom: 20px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}
    .datalens-card:hover {{
        box-shadow: 0 6px 16px rgba(65, 105, 225, 0.08);
    }}

    /* KPI Cards */
    .kpi-card {{
        background: {COLORS['card_bg']};
        border-radius: 12px;
        padding: 20px;
        border: 1px solid {COLORS['border']};
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        border-top: 4px solid {COLORS['primary']};
        text-align: left;
    }}
    .kpi-label {{
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748B;
        margin-bottom: 6px;
    }}
    .kpi-value {{
        font-size: 1.85rem;
        font-weight: 800;
        color: {COLORS['text']};
        margin: 0;
        line-height: 1.2;
    }}
    .kpi-subtext {{
        font-size: 0.8rem;
        color: #94A3B8;
        margin-top: 4px;
    }}

    /* Demo Badge */
    .demo-banner {{
        background: linear-gradient(90deg, #FEF3C7 0%, #FDE68A 100%);
        border: 1px solid #F59E0B;
        color: #92400E;
        padding: 10px 16px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 0.85rem;
        letter-spacing: 0.03em;
        text-align: center;
        margin-bottom: 18px;
        box-shadow: 0 2px 4px rgba(245, 158, 11, 0.1);
    }}

    /* Live Badge */
    .live-banner {{
        background: #DCFCE7;
        border: 1px solid #10B981;
        color: #065F46;
        padding: 10px 16px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 0.85rem;
        text-align: center;
        margin-bottom: 18px;
    }}

    /* Primary Buttons */
    div.stButton > button {{
        background-color: {COLORS['primary']};
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 8px 18px;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(65, 105, 225, 0.2);
    }}
    div.stButton > button:hover {{
        background-color: #3154C4;
        color: white;
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(65, 105, 225, 0.3);
    }}
    div.stButton > button:active {{
        transform: translateY(0);
    }}

    /* Code & SQL Blocks */
    code, pre {{
        font-family: 'JetBrains Mono', monospace !important;
        background-color: #F8FAFC !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 6px !important;
    }}

    /* Section Headers */
    .section-title {{
        font-size: 1.35rem;
        font-weight: 700;
        color: {COLORS['text']};
        margin-top: 10px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }}

    /* Quick Action Chips */
    .example-chip {{
        display: inline-block;
        background-color: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-radius: 20px;
        padding: 6px 14px;
        font-size: 0.85rem;
        color: {COLORS['primary']};
        margin: 4px 4px;
        font-weight: 500;
    }}

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {{
        background-color: #FFFFFF;
        border-right: 1px solid {COLORS['border']};
    }}
    
    /* Metrics override */
    div[data-testid="stMetricValue"] {{
        color: {COLORS['text']};
        font-weight: 700;
    }}
    </style>
    """
