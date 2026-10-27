"""
Analytics Service for DataLens.
Performs data aggregation, KPI computations, multi-channel comparisons,
and query history management.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd
from services.snowflake_service import snowflake_service


class AnalyticsService:
    """Provides high-level analytical metrics and history tracking."""

    @staticmethod
    def get_dashboard_summary() -> Dict[str, Any]:
        """Calculates four key dashboard metrics and charts datasets from actual data."""
        # 1. Total KPI aggregation across store, web, catalog
        kpi_sql = """
        SELECT 
            SUM(sales) AS total_sales,
            SUM(qty) AS total_items,
            SUM(records) AS total_records
        FROM (
            SELECT SUM(ss_ext_sales_price) AS sales, SUM(ss_quantity) AS qty, COUNT(*) AS records FROM store_sales
            UNION ALL
            SELECT SUM(ws_ext_sales_price) AS sales, SUM(ws_quantity) AS qty, COUNT(*) AS records FROM web_sales
            UNION ALL
            SELECT SUM(cs_ext_sales_price) AS sales, SUM(cs_quantity) AS qty, COUNT(*) AS records FROM catalog_sales
        )
        """
        df_kpi, _, is_demo, _ = snowflake_service.execute_query(kpi_sql)

        total_sales = 0.0
        total_items = 0
        total_records = 0
        if not df_kpi.empty:
            total_sales = float(df_kpi.iloc[0]["total_sales"] or 0)
            total_items = int(df_kpi.iloc[0]["total_items"] or 0)
            total_records = int(df_kpi.iloc[0]["total_records"] or 0)

        # 2. Top-selling product
        top_prod_sql = """
        SELECT i.i_product_name, SUM(s.ss_ext_sales_price) AS sales
        FROM store_sales s
        JOIN item i ON s.ss_item_sk = i.i_item_sk
        GROUP BY i.i_product_name
        ORDER BY sales DESC
        LIMIT 1
        """
        df_top, _, _, _ = snowflake_service.execute_query(top_prod_sql)
        top_product_name = df_top.iloc[0]["i_product_name"] if not df_top.empty else "N/A"
        top_product_sales = float(df_top.iloc[0]["sales"] or 0) if not df_top.empty else 0.0

        # 3. Sales by product category
        category_sql = """
        SELECT i.i_category AS category, SUM(s.ss_ext_sales_price) AS total_sales
        FROM store_sales s
        JOIN item i ON s.ss_item_sk = i.i_item_sk
        GROUP BY i.i_category
        ORDER BY total_sales DESC
        """
        df_category, _, _, _ = snowflake_service.execute_query(category_sql)

        # 4. Sales trends over time (by month)
        trend_sql = """
        SELECT 
            d.d_year AS year,
            d.d_moy AS month_num,
            d.d_month_name AS month,
            SUM(s.ss_ext_sales_price) AS total_sales
        FROM store_sales s
        JOIN date_dim d ON s.ss_sold_date_sk = d.d_date_sk
        GROUP BY d.d_year, d.d_moy, d.d_month_name
        ORDER BY d.d_year ASC, d.d_moy ASC
        LIMIT 24
        """
        df_trends, _, _, _ = snowflake_service.execute_query(trend_sql)

        # 5. Top 10 products
        top10_sql = """
        SELECT 
            i.i_product_name AS product_name,
            i.i_category AS category,
            SUM(s.ss_ext_sales_price) AS sales,
            SUM(s.ss_quantity) AS units
        FROM store_sales s
        JOIN item i ON s.ss_item_sk = i.i_item_sk
        GROUP BY i.i_product_name, i.i_category
        ORDER BY sales DESC
        LIMIT 10
        """
        df_top10, _, _, _ = snowflake_service.execute_query(top10_sql)

        # 6. Channels comparison
        channels_sql = """
        SELECT 'Store' AS channel, SUM(ss_ext_sales_price) AS sales, SUM(ss_quantity) AS units FROM store_sales
        UNION ALL
        SELECT 'Web' AS channel, SUM(ws_ext_sales_price) AS sales, SUM(ws_quantity) AS units FROM web_sales
        UNION ALL
        SELECT 'Catalog' AS channel, SUM(cs_ext_sales_price) AS sales, SUM(cs_quantity) AS units FROM catalog_sales
        ORDER BY sales DESC
        """
        df_channels, _, _, _ = snowflake_service.execute_query(channels_sql)

        return {
            "total_sales": total_sales,
            "total_items": total_items,
            "total_records": total_records,
            "top_product_name": top_product_name,
            "top_product_sales": top_product_sales,
            "df_category": df_category,
            "df_trends": df_trends,
            "df_top10": df_top10,
            "df_channels": df_channels,
            "is_demo": is_demo,
        }

    @staticmethod
    def get_sales_analytics(selected_category: str = "All", year_filter: Optional[int] = None) -> Dict[str, Any]:
        """Fetches sales analytics with category and date filtering."""
        where_clauses = []
        if selected_category and selected_category != "All":
            where_clauses.append(f"i.i_category = '{selected_category}'")
        if year_filter:
            where_clauses.append(f"d.d_year = {year_filter}")

        where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        # Summary KPIs
        summary_sql = f"""
        SELECT 
            SUM(s.ss_ext_sales_price) AS total_sales,
            SUM(s.ss_quantity) AS total_quantity,
            COUNT(*) AS total_transactions,
            ROUND(AVG(s.ss_ext_sales_price), 2) AS avg_order_value
        FROM store_sales s
        JOIN item i ON s.ss_item_sk = i.i_item_sk
        JOIN date_dim d ON s.ss_sold_date_sk = d.d_date_sk
        {where_str}
        """
        df_summary, _, is_demo, _ = snowflake_service.execute_query(summary_sql)

        # Monthly time series
        monthly_sql = f"""
        SELECT 
            d.d_year AS year,
            d.d_moy AS month_num,
            d.d_month_name AS month,
            SUM(s.ss_ext_sales_price) AS sales,
            SUM(s.ss_quantity) AS quantity
        FROM store_sales s
        JOIN item i ON s.ss_item_sk = i.i_item_sk
        JOIN date_dim d ON s.ss_sold_date_sk = d.d_date_sk
        {where_str}
        GROUP BY d.d_year, d.d_moy, d.d_month_name
        ORDER BY d.d_year ASC, d.d_moy ASC
        """
        df_monthly, _, _, _ = snowflake_service.execute_query(monthly_sql)

        # Product breakdown
        product_sql = f"""
        SELECT 
            i.i_product_name AS product_name,
            i.i_category AS category,
            SUM(s.ss_ext_sales_price) AS revenue,
            SUM(s.ss_quantity) AS units_sold,
            ROUND(AVG(s.ss_sales_price), 2) AS avg_unit_price
        FROM store_sales s
        JOIN item i ON s.ss_item_sk = i.i_item_sk
        JOIN date_dim d ON s.ss_sold_date_sk = d.d_date_sk
        {where_str}
        GROUP BY i.i_product_name, i.i_category
        ORDER BY revenue DESC
        LIMIT 25
        """
        df_products, _, _, _ = snowflake_service.execute_query(product_sql)

        # Channel comparison
        channel_sql = """
        SELECT 'Store' AS channel, SUM(ss_ext_sales_price) AS sales, SUM(ss_quantity) AS units FROM store_sales
        UNION ALL
        SELECT 'Web' AS channel, SUM(ws_ext_sales_price) AS sales, SUM(ws_quantity) AS units FROM web_sales
        UNION ALL
        SELECT 'Catalog' AS channel, SUM(cs_ext_sales_price) AS sales, SUM(cs_quantity) AS units FROM catalog_sales
        """
        df_channels, _, _, _ = snowflake_service.execute_query(channel_sql)

        return {
            "summary": df_summary,
            "monthly": df_monthly,
            "products": df_products,
            "channels": df_channels,
            "is_demo": is_demo,
        }

    @staticmethod
    def get_product_analytics(search_term: str = "", category_filter: str = "All") -> Dict[str, Any]:
        """Fetches product-specific metrics, rankings, and search results."""
        where_conds = []
        if category_filter and category_filter != "All":
            where_conds.append(f"i.i_category = '{category_filter}'")
        if search_term:
            clean_term = search_term.replace("'", "''")
            where_conds.append(f"(LOWER(i.i_product_name) LIKE '%{clean_term.lower()}%' OR LOWER(i.i_brand) LIKE '%{clean_term.lower()}%')")

        where_clause = f"WHERE {' AND '.join(where_conds)}" if where_conds else ""

        # Top 10 by sales
        top_sales_sql = f"""
        SELECT 
            i.i_item_id AS item_code,
            i.i_product_name AS product_name,
            i.i_category AS category,
            i.i_brand AS brand,
            SUM(s.ss_ext_sales_price) AS total_sales,
            SUM(s.ss_quantity) AS units_sold
        FROM store_sales s
        JOIN item i ON s.ss_item_sk = i.i_item_sk
        {where_clause}
        GROUP BY i.i_item_id, i.i_product_name, i.i_category, i.i_brand
        ORDER BY total_sales DESC
        LIMIT 10
        """
        df_top_sales, _, is_demo, _ = snowflake_service.execute_query(top_sales_sql)

        # Top 10 by quantity
        top_qty_sql = f"""
        SELECT 
            i.i_item_id AS item_code,
            i.i_product_name AS product_name,
            i.i_category AS category,
            i.i_brand AS brand,
            SUM(s.ss_quantity) AS units_sold,
            SUM(s.ss_ext_sales_price) AS total_sales
        FROM store_sales s
        JOIN item i ON s.ss_item_sk = i.i_item_sk
        {where_clause}
        GROUP BY i.i_item_id, i.i_product_name, i.i_category, i.i_brand
        ORDER BY units_sold DESC
        LIMIT 10
        """
        df_top_qty, _, _, _ = snowflake_service.execute_query(top_qty_sql)

        # Catalog listing
        catalog_sql = f"""
        SELECT 
            i.i_item_id AS item_code,
            i.i_product_name AS product_name,
            i.i_category AS category,
            i.i_brand AS brand,
            i.i_current_price AS unit_price,
            COALESCE(SUM(s.ss_quantity), 0) AS units_sold,
            COALESCE(SUM(s.ss_ext_sales_price), 0.0) AS lifetime_revenue
        FROM item i
        LEFT JOIN store_sales s ON i.i_item_sk = s.ss_item_sk
        {where_clause}
        GROUP BY i.i_item_id, i.i_product_name, i.i_category, i.i_brand, i.i_current_price
        ORDER BY lifetime_revenue DESC
        """
        df_catalog, _, _, _ = snowflake_service.execute_query(catalog_sql)

        return {
            "top_sales": df_top_sales,
            "top_qty": df_top_qty,
            "catalog": df_catalog,
            "is_demo": is_demo,
        }

    @staticmethod
    def get_categories() -> List[str]:
        """Returns list of distinct product categories."""
        sql = "SELECT DISTINCT i_category FROM item WHERE i_category IS NOT NULL ORDER BY i_category"
        df, _, _, _ = snowflake_service.execute_query(sql)
        if not df.empty and "i_category" in df.columns:
            return ["All"] + df["i_category"].dropna().tolist()
        return ["All", "Electronics", "Apparel", "Home & Kitchen", "Books", "Sports"]


analytics_service = AnalyticsService()
