"""
Formatting helper utilities for DataLens metrics, tables, and currency values.
"""

from typing import Union, Any


def format_currency(value: Union[int, float, None]) -> str:
    """Formats numeric value as USD currency."""
    if value is None:
        return "$0.00"
    try:
        val = float(value)
        if abs(val) >= 1_000_000_000:
            return f"${val / 1_000_000_000:.2f}B"
        elif abs(val) >= 1_000_000:
            return f"${val / 1_000_000:.2f}M"
        elif abs(val) >= 1_000:
            return f"${val:,.2f}"
        else:
            return f"${val:.2f}"
    except (ValueError, TypeError):
        return str(value)


def format_number(value: Union[int, float, None]) -> str:
    """Formats numeric count with comma separation or abbreviation."""
    if value is None:
        return "0"
    try:
        val = float(value)
        if abs(val) >= 1_000_000:
            return f"{val / 1_000_000:.2f}M"
        elif abs(val) >= 1_000:
            return f"{int(val):,}"
        elif val.is_integer():
            return f"{int(val)}"
        else:
            return f"{val:.1f}"
    except (ValueError, TypeError):
        return str(value)


def format_percentage(value: Union[int, float, None]) -> str:
    """Formats ratio as percentage."""
    if value is None:
        return "0.0%"
    try:
        return f"{float(value):.1f}%"
    except (ValueError, TypeError):
        return str(value)


def format_duration(seconds: float) -> str:
    """Formats execution time in ms or seconds."""
    if seconds < 1.0:
        return f"{seconds * 1000:.0f} ms"
    return f"{seconds:.2f} s"


def get_status_badge(status: str) -> str:
    """Returns HTML badge for query or connection status."""
    st = status.lower()
    if st in ("success", "connected", "active"):
        return f'<span style="background-color: #DCFCE7; color: #166534; padding: 3px 8px; border-radius: 9999px; font-size: 0.75rem; font-weight: 600;">● {status.upper()}</span>'
    elif st in ("error", "failed", "rejected", "disconnected"):
        return f'<span style="background-color: #FEE2E2; color: #991B1B; padding: 3px 8px; border-radius: 9999px; font-size: 0.75rem; font-weight: 600;">● {status.upper()}</span>'
    elif st in ("warning", "demo", "simulated"):
        return f'<span style="background-color: #FEF3C7; color: #92400E; padding: 3px 8px; border-radius: 9999px; font-size: 0.75rem; font-weight: 600;">● {status.upper()}</span>'
    else:
        return f'<span style="background-color: #F1F5F9; color: #475569; padding: 3px 8px; border-radius: 9999px; font-size: 0.75rem; font-weight: 600;">{status}</span>'
