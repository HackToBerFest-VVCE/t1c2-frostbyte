"""SQL Validator and Sanitizer Module for DataLens Live.

Ensures strict SQL safety:
- Only read-only SELECT (or WITH ... SELECT) queries are allowed.
- Multiple statements are rejected.
- Data manipulation/definition statements (INSERT, UPDATE, DELETE, DROP, etc.) are strictly blocked.
- Only allowlisted Snowflake tables are permitted (STORE_SALES, WEB_SALES, CATALOG_SALES, ITEM, CUSTOMER, DATE_DIM).
- Enforces an automatic LIMIT clause (default 100 rows).
"""

import re
from typing import Tuple, List, Set
import sqlparse
from sqlparse.sql import IdentifierList, Identifier, Function
from sqlparse.tokens import Keyword, DML

# Approved base tables in Snowflake TPCDS_SF10TCL
ALLOWED_TABLES = {
    "STORE_SALES",
    "WEB_SALES",
    "CATALOG_SALES",
    "ITEM",
    "CUSTOMER",
    "DATE_DIM",
}

# Forbidden keywords / commands that modify data or execute system actions
FORBIDDEN_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "CREATE",
    "REPLACE", "MERGE", "GRANT", "REVOKE", "COPY", "EXECUTE", "EXEC",
    "CALL", "PUT", "GET", "REMOVE", "SYSTEM$", "UNLOAD", "INTO OUTFILE",
    "INTO DUMPFILE", "INFORMATION_SCHEMA", "ACCOUNT_USAGE"
]


def clean_sql_text(raw_sql: str) -> str:
    """Strip markdown code blocks, comments, and extraneous whitespace."""
    if not raw_sql:
        return ""
    
    # Remove markdown code fences if present (e.g. ```sql ... ```)
    cleaned = re.sub(r"^```(?:sql)?\s*", "", raw_sql.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())
    
    # Remove trailing semicolons for consistent processing
    cleaned = cleaned.strip().rstrip(";")
    return cleaned.strip()


def extract_cte_aliases(sql: str) -> Set[str]:
    """Extract CTE names defined in WITH cte_name AS (...) blocks."""
    cte_pattern = r"(?:with|,)\s*([a-zA-Z0-9_]+)\s+as\s*\("
    matches = re.findall(cte_pattern, sql, flags=re.IGNORECASE)
    return {m.upper() for m in matches}


def extract_table_references(sql: str) -> List[str]:
    """Extract referenced table names from FROM and JOIN clauses."""
    tables = []
    # Match patterns like: FROM table_name, JOIN table_name, FROM db.schema.table
    patterns = [
        r"\bFROM\s+([a-zA-Z0-9_\.\"]+)",
        r"\bJOIN\s+([a-zA-Z0-9_\.\"]+)",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, sql, flags=re.IGNORECASE):
            raw_target = match.group(1).strip().replace('"', '')
            # If qualified (e.g. SNOWFLAKE_SAMPLE_DATA.TPCDS_SF10TCL.STORE_SALES), take the table part
            table_name = raw_target.split(".")[-1].upper()
            if table_name and table_name not in ("SELECT", "LATERAL", "FLATTEN"):
                tables.append(table_name)
    return tables


def validate_and_sanitize_sql(
    raw_sql: str,
    default_limit: int = 100,
    allow_custom_limit: bool = True
) -> Tuple[bool, str, str]:
    """
    Validate a user or LLM-generated SQL query for safety.

    Returns:
        (is_valid: bool, sanitized_sql: str, error_message: str)
    """
    if not raw_sql or not raw_sql.strip():
        return False, "", "SQL query cannot be empty."

    sql = clean_sql_text(raw_sql)

    # 1. Reject multiple statements (check for semicolons inside query text)
    statements = sqlparse.split(sql)
    if len(statements) > 1:
        return False, "", "Multiple SQL statements are not permitted for security reasons."

    parsed = sqlparse.parse(sql)
    if not parsed:
        return False, "", "Unable to parse SQL query."

    statement = parsed[0]

    # 2. Check statement type: Must be a SELECT or WITH statement
    stmt_type = statement.get_type().upper()
    first_token = ""
    for token in statement.tokens:
        if not token.is_whitespace:
            first_token = token.value.upper()
            break

    if stmt_type != "SELECT" and first_token not in ("SELECT", "WITH"):
        return False, "", f"Only read-only SELECT queries are allowed. Found statement type: '{stmt_type or first_token}'."

    # 3. Check for strictly forbidden keywords anywhere in tokens
    upper_sql = sql.upper()
    for forbidden in FORBIDDEN_KEYWORDS:
        # Check as full word boundary
        if re.search(r"\b" + re.escape(forbidden) + r"\b", upper_sql):
            return False, "", f"Disallowed keyword detected: '{forbidden}'. Only read-only operations are permitted."

    # 4. Check for comments that could be used for SQL injection obfuscation
    if "--" in sql or "/*" in sql:
        # Strip comments using sqlparse
        sql = sqlparse.format(sql, strip_comments=True).strip()

    # 5. Extract tables and ensure they match the allowlist (or CTE aliases)
    cte_aliases = extract_cte_aliases(sql)
    table_refs = extract_table_references(sql)

    if not table_refs:
        # If no tables found (e.g. SELECT 1 or SELECT CURRENT_TIMESTAMP()), allow it
        pass
    else:
        disallowed = []
        for tbl in table_refs:
            if tbl not in ALLOWED_TABLES and tbl not in cte_aliases:
                disallowed.append(tbl)
        
        if disallowed:
            return (
                False,
                "",
                f"Access to table(s) {', '.join(set(disallowed))} is not permitted. "
                f"Allowed tables: {', '.join(sorted(ALLOWED_TABLES))}."
            )

    # 6. Enforce LIMIT 100 if not present
    has_limit = re.search(r"\bLIMIT\s+(\d+)", sql, flags=re.IGNORECASE)
    if not has_limit:
        # Also check for FETCH FIRST
        has_fetch = re.search(r"\bFETCH\s+FIRST\s+(\d+)\s+ROWS\s+ONLY", sql, flags=re.IGNORECASE)
        if not has_fetch:
            sql = f"{sql}\nLIMIT {default_limit}"
    else:
        # If limit is present and greater than 500, clamp it for safety
        limit_val = int(has_limit.group(1))
        if limit_val > 500:
            sql = re.sub(r"\bLIMIT\s+\d+", f"LIMIT {default_limit}", sql, flags=re.IGNORECASE)

    # Format cleanly with sqlparse
    formatted_sql = sqlparse.format(
        sql,
        reindent=True,
        keyword_case="upper",
        identifier_case="lower"
    )

    return True, formatted_sql, ""
