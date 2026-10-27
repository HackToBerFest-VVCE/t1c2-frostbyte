"""Analytics Service for DataLens Live.

Provides optimized, safe Snowflake queries for TPC-DS SF10TCL.
Includes pre-tested queries for sales trends, channel comparisons,
and product leaderboards that use proper partitioning filters
to prevent full scans on the multi-terabyte dataset.
"""

from typing import Tuple, Optional
import pandas as pd
from services.snowflake_service import execute_snowflake_query
from services.sql_validator import validate_and_sanitize_sql

# Standard Year filter to keep scans bounded and lightning-fast on SF10TCL
DEFAULT_ANALYTICS_YEAR = 2000


def run_safe_query(sql: str, max_rows: int = 100) -> Tuple[Optional[pd.DataFrame], float, str]:
    """Validate query with SQL validator before executing against Snowflake."""
    is_valid, sanitized_sql, err = validate_and_sanitize_sql(sql, default_limit=max_rows)
    if not is_valid:
        return None, 0.0, f"SQL Validation Failed: {err}"
    
    return execute_snowflake_query(sanitized_sql, max_rows=max_rows)


def get_sales_kpi_summary(year: int = DEFAULT_ANALYTICS_YEAR) -> Tuple[Optional[pd.DataFrame], float, str]:
    """
    Fetch high-level KPI metrics:
    - Total Store Sales
    - Total Quantity Sold
    - Total Profit
    - Average Ticket Value
    """
    sql = f"""
    SELECT
        ROUND(SUM(ss_ext_sales_price), 2) AS total_sales,
        SUM(ss_quantity) AS total_quantity,
        ROUND(SUM(ss_net_profit), 2) AS total_profit,
        ROUND(AVG(ss_sales_price), 2) AS avg_sales_price,
        COUNT(DISTINCT ss_ticket_number) AS total_orders
    FROM store_sales
    JOIN date_dim ON ss_sold_date_sk = d_date_sk
    WHERE d_year = {year}
    """
    return run_safe_query(sql, max_rows=1)


def get_sales_trend_by_date(year: int = DEFAULT_ANALYTICS_YEAR) -> Tuple[Optional[pd.DataFrame], float, str]:
    """
    Fetch daily sales trend for the selected year.
    """
    sql = f"""
    SELECT
        d_date AS sale_date,
        ROUND(SUM(ss_ext_sales_price), 2) AS daily_sales,
        SUM(ss_quantity) AS units_sold
    FROM store_sales
    JOIN date_dim ON ss_sold_date_sk = d_date_sk
    WHERE d_year = {year}
    GROUP BY d_date
    ORDER BY d_date ASC
    LIMIT 100
    """
    return run_safe_query(sql, max_rows=100)


def get_top_products(limit: int = 10, year: int = DEFAULT_ANALYTICS_YEAR) -> Tuple[Optional[pd.DataFrame], float, str]:
    """
    Fetch top products by total sales.
    """
    sql = f"""
    SELECT
        COALESCE(i_product_name, i_item_desc, 'Item #' || i_item_sk) AS product_name,
        COALESCE(i_category, 'Uncategorized') AS category,
        ROUND(SUM(ss_ext_sales_price), 2) AS total_sales,
        SUM(ss_quantity) AS total_quantity_sold
    FROM store_sales
    JOIN item ON ss_item_sk = i_item_sk
    JOIN date_dim ON ss_sold_date_sk = d_date_sk
    WHERE d_year = {year}
    GROUP BY 1, 2
    ORDER BY total_sales DESC
    LIMIT {limit}
    """
    return run_safe_query(sql, max_rows=limit)


def get_omnichannel_comparison(year: int = DEFAULT_ANALYTICS_YEAR) -> Tuple[Optional[pd.DataFrame], float, str]:
    """
    Compare Store, Web, and Catalog Sales channels.
    """
    sql = f"""
    WITH store AS (
        SELECT 'Store Sales' AS channel,
               ROUND(SUM(ss_ext_sales_price), 2) AS sales,
               SUM(ss_quantity) AS quantity
        FROM store_sales
        JOIN date_dim ON ss_sold_date_sk = d_date_sk
        WHERE d_year = {year}
    ),
    web AS (
        SELECT 'Web Sales' AS channel,
               ROUND(SUM(ws_ext_sales_price), 2) AS sales,
               SUM(ws_quantity) AS quantity
        FROM web_sales
        JOIN date_dim ON ws_sold_date_sk = d_date_sk
        WHERE d_year = {year}
    ),
    catalog AS (
        SELECT 'Catalog Sales' AS channel,
               ROUND(SUM(cs_ext_sales_price), 2) AS sales,
               SUM(cs_quantity) AS quantity
        FROM catalog_sales
        JOIN date_dim ON cs_sold_date_sk = d_date_sk
        WHERE d_year = {year}
    )
    SELECT * FROM store
    UNION ALL
    SELECT * FROM web
    UNION ALL
    SELECT * FROM catalog
    """
    return run_safe_query(sql, max_rows=10)


def get_category_performance(year: int = DEFAULT_ANALYTICS_YEAR) -> Tuple[Optional[pd.DataFrame], float, str]:
    """
    Sales performance grouped by product category.
    """
    sql = f"""
    SELECT
        COALESCE(i_category, 'Other') AS category,
        ROUND(SUM(ss_ext_sales_price), 2) AS total_sales,
        SUM(ss_quantity) AS total_quantity,
        ROUND(SUM(ss_net_profit), 2) AS net_profit
    FROM store_sales
    JOIN item ON ss_item_sk = i_item_sk
    JOIN date_dim ON ss_sold_date_sk = d_date_sk
    WHERE d_year = {year}
    GROUP BY 1
    ORDER BY total_sales DESC
    LIMIT 20
    """
    return run_safe_query(sql, max_rows=20)
