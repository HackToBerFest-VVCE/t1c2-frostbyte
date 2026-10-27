"""
KPI Metric Cards & Banner Components for DataLens.
Styled strictly with white cards (#FFFFFF), soft borders (#E5E7EB), and subtle shadows.
"""

import streamlit as st
from typing import Optional
from utils.config import COLORS, DEMO_WARNING_TEXT
from utils.formatting import format_currency, format_number


def render_demo_banner(is_demo: bool):
    """Displays the exact mandatory warning banner when demo data is active."""
    if is_demo:
        st.markdown(
            f"""
            <div class="demo-banner">
                ⚠️ <b>{DEMO_WARNING_TEXT}</b>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_kpi_cards(
    total_sales: float,
    total_items: int,
    total_records: int,
    top_product_name: str,
    top_product_sales: Optional[float] = None,
):
    """
    Renders the four core dashboard KPI cards:
    - Total Sales
    - Total Items Sold
    - Total Sales Records
    - Top-Selling Product
    """
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div class="kpi-card" style="border-top-color: {COLORS['primary']};">
                <div class="kpi-label">Total Sales</div>
                <div class="kpi-value">{format_currency(total_sales)}</div>
                <div class="kpi-subtext">Across all sales channels</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="kpi-card" style="border-top-color: {COLORS['highlight']};">
                <div class="kpi-label">Total Items Sold</div>
                <div class="kpi-value">{format_number(total_items)}</div>
                <div class="kpi-subtext">Physical units moved</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div class="kpi-card" style="border-top-color: #0284C7;">
                <div class="kpi-label">Total Sales Records</div>
                <div class="kpi-value">{format_number(total_records)}</div>
                <div class="kpi-subtext">Transaction line items</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col4:
        sub = f"Revenue: {format_currency(top_product_sales)}" if top_product_sales else "Highest grossing SKU"
        st.markdown(
            f"""
            <div class="kpi-card" style="border-top-color: #38BDF8;">
                <div class="kpi-label">Top-Selling Product</div>
                <div class="kpi-value" style="font-size: 1.15rem; font-weight: 700; line-height: 1.3; min-height: 2.3rem; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;" title="{top_product_name}">
                    {top_product_name}
                </div>
                <div class="kpi-subtext">{sub}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
