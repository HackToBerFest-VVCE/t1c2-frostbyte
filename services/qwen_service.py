"""
Qwen3-4B AI Service for Natural-Language Understanding and SQL Generation.

Features:
- Configurable inference endpoint (Ollama, vLLM, OpenAI-compatible, HuggingFace).
- Schema-conditioned prompting with Snowflake TPC-DS retail entities.
- Returns generated SQL and plain English explanation.
- Handles connection errors and offline endpoints gracefully.
- Explicitly identifies whether inference was performed by live Qwen3-4B or deterministic simulation.
- Never silently substitutes an alternate model.
"""

import os
import re
import json
import requests
from typing import Dict, Any, Optional
from utils.config import SCHEMA_CONTEXT

try:
    import streamlit as st
except ImportError:
    st = None


class QwenService:
    """Service communicating with Qwen3-4B model for SQL translation and analysis."""

    def __init__(self):
        self.default_model = "qwen3:4b"
        self.default_endpoint = "http://localhost:11434/api/generate"

    def get_config(self) -> Dict[str, Any]:
        """Loads Qwen3-4B settings from Streamlit secrets, session state, or environment."""
        endpoint = self.default_endpoint
        model = self.default_model
        api_key = ""
        temperature = 0.1

        # Check Streamlit secrets safely
        try:
            if st and hasattr(st, "secrets") and "qwen" in st.secrets:
                sec = st.secrets["qwen"]
                endpoint = sec.get("endpoint_url", endpoint)
                model = sec.get("model_name", model)
                api_key = sec.get("api_key", api_key)
                temperature = float(sec.get("temperature", temperature))
        except Exception:
            pass

        # Check Streamlit session state overrides
        if st and hasattr(st, "session_state"):
            endpoint = st.session_state.get("qwen_endpoint", endpoint)
            model = st.session_state.get("qwen_model", model)
            api_key = st.session_state.get("qwen_api_key", api_key)

        # Environment variables override
        endpoint = os.getenv("QWEN_ENDPOINT_URL", endpoint)
        model = os.getenv("QWEN_MODEL_NAME", model)
        api_key = os.getenv("QWEN_API_KEY", api_key)

        return {
            "endpoint": endpoint,
            "model": model,
            "api_key": api_key,
            "temperature": temperature,
        }

    def check_health(self) -> Dict[str, Any]:
        """Pings the Qwen3-4B endpoint to check if the model is reachable."""
        cfg = self.get_config()
        endpoint = cfg["endpoint"]
        try:
            # If Ollama endpoint
            if "/api/generate" in endpoint:
                base = endpoint.replace("/api/generate", "/api/tags")
                res = requests.get(base, timeout=3)
                if res.status_code == 200:
                    models = [m.get("name", "") for m in res.json().get("models", [])]
                    is_loaded = any("qwen" in m.lower() for m in models)
                    return {
                        "available": True,
                        "status": "Online (Ollama)",
                        "details": f"Ollama is running. Available models: {', '.join(models) if models else 'None'}",
                        "is_qwen_present": is_loaded,
                    }
            elif "/v1" in endpoint:
                base = endpoint.split("/v1")[0] + "/v1/models"
                headers = {"Authorization": f"Bearer {cfg['api_key']}"} if cfg["api_key"] else {}
                res = requests.get(base, headers=headers, timeout=3)
                if res.status_code == 200:
                    return {
                        "available": True,
                        "status": "Online (vLLM / OpenAI compatible)",
                        "details": "Model server responded successfully.",
                        "is_qwen_present": True,
                    }
            # Generic ping
            res = requests.get(endpoint, timeout=2)
            return {
                "available": res.status_code < 500,
                "status": f"HTTP {res.status_code}",
                "details": "Server endpoint is reachable.",
                "is_qwen_present": False,
            }
        except Exception as e:
            return {
                "available": False,
                "status": "Offline / Unreachable",
                "details": f"Could not connect to {endpoint}: {str(e)}",
                "is_qwen_present": False,
            }

    def generate_sql(self, question: str) -> Dict[str, Any]:
        """
        Submits user prompt and schema context to Qwen3-4B.
        Falls back cleanly to labelled simulation if model endpoint is unreachable.
        """
        cfg = self.get_config()
        system_prompt = f"""You are Qwen3-4B, an expert SQL data analytics assistant specializing in Snowflake TPC-DS retail schema.
Your job is to translate the user's natural language question into an accurate, read-only SQL SELECT query.

Schema Reference:
{SCHEMA_CONTEXT}

Rules:
1. ONLY produce a single read-only SELECT query.
2. Calculate total sales revenue using:
   - STORE_SALES: ss_ext_sales_price
   - WEB_SALES: ws_ext_sales_price
   - CATALOG_SALES: cs_ext_sales_price
3. Use proper JOIN conditions:
   - STORE_SALES.ss_item_sk = ITEM.i_item_sk
   - STORE_SALES.ss_sold_date_sk = DATE_DIM.d_date_sk
   - STORE_SALES.ss_customer_sk = CUSTOMER.c_customer_sk
4. Always include meaningful column aliases and an ORDER BY clause when ranking.
5. Limit results appropriately (e.g. LIMIT 10 for top rankings).
6. Format output strictly as JSON with keys:
   - "sql": the raw SQL query without markdown
   - "explanation": a concise 1-2 sentence explanation of what the query calculates and how the data was grouped or filtered.
"""

        user_content = f"Question: {question.strip()}"

        # Attempt live Qwen3-4B query
        live_result = self._call_inference_endpoint(cfg, system_prompt, user_content)
        if live_result:
            return live_result

        # Endpoint offline / unreachable: provide clearly labelled fallback simulation
        return self._simulate_qwen_response(question, cfg)

    def _call_inference_endpoint(
        self, cfg: Dict[str, Any], system_prompt: str, user_content: str
    ) -> Optional[Dict[str, Any]]:
        """Makes HTTP request to configured inference endpoint."""
        endpoint = cfg["endpoint"]
        model = cfg["model"]
        api_key = cfg.get("api_key", "")
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            # 1. Ollama API Format
            if "/api/generate" in endpoint:
                payload = {
                    "model": model,
                    "prompt": f"{system_prompt}\n\n{user_content}",
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": cfg["temperature"]},
                }
                res = requests.post(endpoint, json=payload, headers=headers, timeout=12)
                if res.status_code == 200:
                    raw_text = res.json().get("response", "")
                    parsed = self._extract_json_response(raw_text)
                    if parsed:
                        return {
                            "sql": parsed.get("sql", "").strip(),
                            "explanation": parsed.get("explanation", "").strip(),
                            "is_simulated": False,
                            "model_name": f"{model} (Live Ollama)",
                            "endpoint": endpoint,
                            "error": None,
                        }

            # 2. OpenAI / vLLM Chat Completions Format
            elif "/v1" in endpoint:
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    "temperature": cfg["temperature"],
                    "response_format": {"type": "json_object"},
                }
                res = requests.post(endpoint, json=payload, headers=headers, timeout=12)
                if res.status_code == 200:
                    data = res.json()
                    raw_text = data["choices"][0]["message"]["content"]
                    parsed = self._extract_json_response(raw_text)
                    if parsed:
                        return {
                            "sql": parsed.get("sql", "").strip(),
                            "explanation": parsed.get("explanation", "").strip(),
                            "is_simulated": False,
                            "model_name": f"{model} (Live vLLM/API)",
                            "endpoint": endpoint,
                            "error": None,
                        }
        except Exception as e:
            # Network failure or timeout
            print(f"Qwen3-4B live call exception: {e}")

        return None

    def _extract_json_response(self, text: str) -> Optional[Dict[str, str]]:
        """Parses JSON safely from model response."""
        try:
            return json.loads(text)
        except Exception:
            # Look for json fenced block
            match = re.search(r"\{[\s\S]*\}", text)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    pass
        return None

    def _simulate_qwen_response(self, question: str, cfg: Dict[str, Any]) -> Dict[str, Any]:
        """
        High-fidelity deterministic natural language SQL generator for retail analytics.
        Clearly labelled as simulation when live Qwen3-4B is offline.
        """
        q = question.lower().strip()

        # 1. Top products by sales
        if "top" in q and ("product" in q or "best" in q or "selling" in q) and "quantity" not in q:
            sql = """SELECT 
    i.i_product_name AS product_name,
    i.i_category AS category,
    SUM(s.ss_ext_sales_price) AS total_sales,
    SUM(s.ss_quantity) AS total_quantity_sold
FROM store_sales s
JOIN item i ON s.ss_item_sk = i.i_item_sk
GROUP BY i.i_product_name, i.i_category
ORDER BY total_sales DESC
LIMIT 10"""
            explanation = "Aggregates total extended sales revenue and units sold per item from store sales, joined with the product item dimension, sorted in descending order to identify the top 10 revenue-generating products."

        # 2. Top products by quantity sold
        elif "quantity" in q and ("top" in q or "best" in q or "most" in q):
            sql = """SELECT 
    i.i_product_name AS product_name,
    i.i_category AS category,
    SUM(s.ss_quantity) AS total_units_sold,
    SUM(s.ss_ext_sales_price) AS total_sales
FROM store_sales s
JOIN item i ON s.ss_item_sk = i.i_item_sk
GROUP BY i.i_product_name, i.i_category
ORDER BY total_units_sold DESC
LIMIT 10"""
            explanation = "Sums the total physical units sold per item across store transactions and ranks products in descending order by sales volume."

        # 3. Monthly / Month highest sales
        elif "month" in q or "trend" in q or "time" in q:
            sql = """SELECT 
    d.d_year AS sales_year,
    d.d_moy AS month_number,
    d.d_month_name AS month_name,
    SUM(s.ss_ext_sales_price) AS total_monthly_sales,
    SUM(s.ss_quantity) AS total_items_sold
FROM store_sales s
JOIN date_dim d ON s.ss_sold_date_sk = d.d_date_sk
GROUP BY d.d_year, d.d_moy, d.d_month_name
ORDER BY d.d_year ASC, d.d_moy ASC
LIMIT 24"""
            explanation = "Joins store transactions with the date dimension to group sales by calendar year and month, displaying revenue trends over time."

        # 4. Product categories performance
        elif "categor" in q:
            sql = """SELECT 
    i.i_category AS category,
    COUNT(DISTINCT i.i_item_sk) AS distinct_products,
    SUM(s.ss_quantity) AS total_units_sold,
    SUM(s.ss_ext_sales_price) AS category_revenue,
    ROUND(AVG(s.ss_sales_price), 2) AS avg_selling_price
FROM store_sales s
JOIN item i ON s.ss_item_sk = i.i_item_sk
GROUP BY i.i_category
ORDER BY category_revenue DESC
LIMIT 10"""
            explanation = "Computes aggregated revenue, total volume sold, and average transaction price grouped by product merchandise category."

        # 5. Channel comparison (store, web, catalog)
        elif "channel" in q or ("store" in q and "web" in q) or "catalog" in q:
            sql = """SELECT 'Store' AS channel, SUM(ss_ext_sales_price) AS total_sales, SUM(ss_quantity) AS units_sold FROM store_sales
UNION ALL
SELECT 'Web' AS channel, SUM(ws_ext_sales_price) AS total_sales, SUM(ws_quantity) AS units_sold FROM web_sales
UNION ALL
SELECT 'Catalog' AS channel, SUM(cs_ext_sales_price) AS total_sales, SUM(cs_quantity) AS units_sold FROM catalog_sales
ORDER BY total_sales DESC"""
            explanation = "Unions aggregated sales figures across physical stores, web e-commerce, and mail-order catalog channels to compare multi-channel retail performance."

        # 6. Average quantity sold per product
        elif "average quantity" in q or "avg quantity" in q:
            sql = """SELECT 
    i.i_category AS category,
    i.i_product_name AS product_name,
    ROUND(AVG(s.ss_quantity), 2) AS avg_units_per_order,
    COUNT(*) AS total_orders
FROM store_sales s
JOIN item i ON s.ss_item_sk = i.i_item_sk
GROUP BY i.i_category, i.i_product_name
HAVING COUNT(*) > 5
ORDER BY avg_units_per_order DESC
LIMIT 15"""
            explanation = "Calculates the average unit order size and total order count per product from store transactions with at least 5 sales orders."

        # 7. Customer analytics
        elif "customer" in q or "buyer" in q or "shopper" in q:
            sql = """SELECT 
    c.c_customer_id AS customer_id,
    c.c_first_name || ' ' || c.c_last_name AS customer_name,
    c.c_email_address AS email,
    COUNT(s.ss_item_sk) AS items_purchased,
    SUM(s.ss_ext_sales_price) AS total_spent
FROM store_sales s
JOIN customer c ON s.ss_customer_sk = c.c_customer_sk
GROUP BY c.c_customer_id, customer_name, c.c_email_address
ORDER BY total_spent DESC
LIMIT 10"""
            explanation = "Identifies the highest value retail customers by joining store sales with customer profile records and computing lifetime purchase value."

        # Default fallback query
        else:
            sql = """SELECT 
    i.i_product_name AS product_name,
    i.i_category AS category,
    SUM(s.ss_ext_sales_price) AS total_sales,
    SUM(s.ss_quantity) AS total_quantity
FROM store_sales s
JOIN item i ON s.ss_item_sk = i.i_item_sk
GROUP BY i.i_product_name, i.i_category
ORDER BY total_sales DESC
LIMIT 10"""
            explanation = f"Analyzes store sales by product and category to answer: '{question}'. Summarizes revenue and units sold."

        return {
            "sql": sql,
            "explanation": explanation,
            "is_simulated": True,
            "model_name": f"Qwen3-4B (Simulated — Endpoint {cfg['endpoint']} offline)",
            "endpoint": cfg["endpoint"],
            "error": "Qwen3-4B endpoint is not running or unreachable. Using built-in natural-language semantic generator.",
        }


# Global singleton instance
qwen_service = QwenService()
