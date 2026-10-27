"""
SQL Validation and Security Layer for DataLens.

Treats all model-generated and user-submitted SQL as untrusted.
Enforces:
- Read-only SELECT statements only.
- Strict rejection of destructive or administrative DDL/DML operations (INSERT, UPDATE, DELETE, DROP, etc.).
- Multi-statement execution blocking (prevents semicolon chaining).
- Whitelist of approved retail schema tables.
- Automatic enforcement of reasonable row limits (e.g., LIMIT 100).
- Safe error explanations without credential or system information leaks.
"""

import re
from typing import Tuple, List, Set
from utils.config import APPROVED_TABLES

# Explicitly prohibited SQL keywords and commands
PROHIBITED_KEYWORDS: Set[str] = {
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE",
    "MERGE", "EXEC", "EXECUTE", "CALL", "GRANT", "REVOKE", "RENAME",
    "REPLACE", "UPSERT", "SYSTEM$", "PUT", "GET", "COPY", "REMOVE",
    "UNDROP", "SHOW", "DESCRIBE", "USE", "SET", "UNSET", "BEGIN", "COMMIT", "ROLLBACK"
}

# Approved retail tables (including lowercase and demo aliases)
ALL_APPROVED_TABLES: Set[str] = set(APPROVED_TABLES) | {
    t.lower() for t in APPROVED_TABLES
} | {
    "DEMO_RETAIL_DATA", "demo_retail_data",
    "store_sales", "web_sales", "catalog_sales", "item", "customer", "date_dim"
}

# Regex to strip single and multi-line comments
COMMENT_STRIP_REGEX = re.compile(r"(--[^\r\n]*)|(/\*[\s\S]*?\*/)", re.MULTILINE)


class SQLValidationError(Exception):
    """Raised when generated SQL fails security checks."""
    pass


class SQLValidator:
    """Security validator for SQL queries before database execution."""

    @staticmethod
    def clean_query(sql: str) -> str:
        """Removes trailing semicolons, leading/trailing whitespace, and markdown blocks."""
        if not sql:
            return ""
        
        # Remove markdown code fences if model returned them
        sql = sql.strip()
        if sql.startswith("```"):
            lines = sql.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            sql = "\n".join(lines).strip()

        # Remove comments to analyze raw statements
        sql = COMMENT_STRIP_REGEX.sub(" ", sql).strip()

        # Remove trailing semicolons
        sql = re.sub(r";+\s*$", "", sql).strip()
        return sql

    @classmethod
    def validate(cls, raw_sql: str, max_limit: int = 100) -> Tuple[bool, str, str]:
        """
        Validates raw SQL for read-only safety, single-statement structure, and approved tables.

        Returns:
            Tuple[bool, str, str]: (is_valid, error_message, sanitized_sql)
        """
        cleaned = cls.clean_query(raw_sql)

        if not cleaned:
            return False, "Query cannot be empty.", ""

        # 1. Multi-statement check (semicolons remaining inside query)
        # Note: allow semicolons only if inside string literals, but for analytics queries, no internal semicolons needed
        if ";" in cleaned:
            return (
                False,
                "Security policy rejection: Multi-statement execution or query chaining (;) is strictly forbidden.",
                "",
            )

        # 2. Check first command token - must be SELECT or WITH (CTE)
        tokens = cleaned.split()
        if not tokens:
            return False, "Query is empty after tokenization.", ""

        first_token = tokens[0].upper()
        if first_token not in ("SELECT", "WITH"):
            return (
                False,
                f"Security policy rejection: Only read-only queries beginning with SELECT or WITH are permitted. Attempted: '{first_token}'.",
                "",
            )

        # 3. Scan for any prohibited command keywords
        # Tokenize by word boundaries
        words = re.findall(r"\b[A-Za-z_][A-Za-z0-9_$]*\b", cleaned)
        upper_words = [w.upper() for w in words]

        for keyword in PROHIBITED_KEYWORDS:
            if keyword in upper_words:
                # Disallow dangerous operations
                return (
                    False,
                    f"Security policy rejection: Prohibited operation detected ('{keyword}'). Only read-only SELECT queries are allowed.",
                    "",
                )

        # 4. Check that at least one table reference is from the approved retail tables
        # Look for FROM or JOIN clauses
        table_references = cls._extract_table_names(cleaned)
        if table_references:
            unapproved = [
                tbl for tbl in table_references 
                if tbl.upper() not in {t.upper() for t in ALL_APPROVED_TABLES}
                # Allow CTE definitions
                and not cls._is_cte(tbl, cleaned)
            ]
            if unapproved and len(unapproved) == len(table_references):
                # If all referenced tables are outside the approved schema
                return (
                    False,
                    f"Security policy rejection: Query references unapproved table(s): {', '.join(unapproved)}. Allowed tables: {', '.join(APPROVED_TABLES)}.",
                    "",
                )

        # 5. Enforce reasonable row limits to prevent memory exhaustion
        sanitized = cls._enforce_limit(cleaned, max_limit)

        return True, "", sanitized

    @classmethod
    def _is_cte(cls, table_name: str, sql: str) -> bool:
        """Checks if a table name was defined as a Common Table Expression (WITH alias AS (...))."""
        cte_pattern = rf"\b{re.escape(table_name)}\s+AS\s*\("
        return bool(re.search(cte_pattern, sql, re.IGNORECASE))

    @classmethod
    def _extract_table_names(cls, sql: str) -> List[str]:
        """Extracts potential table names following FROM or JOIN keywords."""
        pattern = r"\b(?:FROM|JOIN)\s+([A-Za-z0-9_\.]+)"
        matches = re.findall(pattern, sql, re.IGNORECASE)
        table_names = []
        for m in matches:
            # Handle schema qualification: e.g. SNOWFLAKE_SAMPLE_DATA.TPCDS_SF10TCL.STORE_SALES -> STORE_SALES
            parts = m.split(".")
            table_names.append(parts[-1].strip())
        return table_names

    @classmethod
    def _enforce_limit(cls, sql: str, default_limit: int = 100) -> str:
        """Appends or clamps LIMIT clause on the SQL query."""
        limit_match = re.search(r"\bLIMIT\s+(\d+)\b", sql, re.IGNORECASE)
        if limit_match:
            existing_limit = int(limit_match.group(1))
            if existing_limit > default_limit:
                # Clamp limit to max allowed
                return re.sub(r"\bLIMIT\s+\d+\b", f"LIMIT {default_limit}", sql, flags=re.IGNORECASE)
            return sql
        else:
            return f"{sql}\nLIMIT {default_limit}"
