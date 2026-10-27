"""
Plotly Interactive Visualisations for DataLens.
Adheres strictly to the color theme:
- Primary: #4169E1 (royal blue)
- Highlight: #8B5CF6 (purple)
- Secondary: #BAE6FD (light blue)
- Text: #172554 (navy)
- Background: #FFFFFF (card white)
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.config import COLORS

# Default layout styling template
BASE_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Plus Jakarta Sans, sans-serif", color=COLORS["text"], size=12),
    margin=dict(l=40, r=40, t=50, b=40),
    hoverlabel=dict(
        bgcolor="#FFFFFF",
        bordercolor=COLORS["primary"],
        font=dict(color=COLORS["text"], family="Plus Jakarta Sans, sans-serif"),
    ),
)


def render_category_bar_chart(df: pd.DataFrame) -> go.Figure:
    """Renders sales revenue by product category."""
    if df.empty or "category" not in df.columns or "total_sales" not in df.columns:
        return go.Figure()

    fig = px.bar(
        df,
        x="category",
        y="total_sales",
        title="Sales by Product Category",
        labels={"category": "Product Category", "total_sales": "Total Sales (USD)"},
        color="total_sales",
        color_continuous_scale=[[0.0, "#BAE6FD"], [0.5, "#4169E1"], [1.0, "#8B5CF6"]],
    )
    fig.update_layout(
        **BASE_LAYOUT,
        showlegend=False,
        coloraxis_showscale=False,
        xaxis=dict(showgrid=False, linecolor=COLORS["border"]),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickprefix="$"),
    )
    fig.update_traces(
        marker=dict(cornerradius=6),
        hovertemplate="<b>Category:</b> %{x}<br><b>Sales:</b> $%{y:,.2f}<extra></extra>",
    )
    return fig


def render_sales_trend_chart(df: pd.DataFrame) -> go.Figure:
    """Renders time-series sales trend with gradient line and fill."""
    if df.empty:
        return go.Figure()

    # Create readable date/period label
    if "year" in df.columns and "month" in df.columns:
        df["period"] = df["month"].astype(str) + " " + df["year"].astype(str)
        x_col = "period"
    elif "date" in df.columns:
        x_col = "date"
    else:
        x_col = df.columns[0]

    y_col = "total_sales" if "total_sales" in df.columns else ("sales" if "sales" in df.columns else df.columns[-1])

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df[x_col],
            y=df[y_col],
            mode="lines+markers",
            line=dict(color=COLORS["primary"], width=3, shape="spline"),
            marker=dict(size=7, color=COLORS["highlight"], line=dict(color="#FFFFFF", width=2)),
            fill="tozeroy",
            fillcolor="rgba(65, 105, 225, 0.08)",
            hovertemplate="<b>Period:</b> %{x}<br><b>Revenue:</b> $%{y:,.2f}<extra></extra>",
        )
    )

    fig.update_layout(
        **BASE_LAYOUT,
        title="Sales Trends Over Time",
        xaxis=dict(showgrid=False, linecolor=COLORS["border"]),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickprefix="$"),
    )
    return fig


def render_top_products_chart(df: pd.DataFrame) -> go.Figure:
    """Renders top 10 products horizontal bar chart."""
    if df.empty:
        return go.Figure()

    name_col = "product_name" if "product_name" in df.columns else ("i_product_name" if "i_product_name" in df.columns else df.columns[0])
    val_col = "sales" if "sales" in df.columns else ("total_sales" if "total_sales" in df.columns else df.columns[1])

    # Sort ascending for horizontal bar chart display
    plot_df = df.sort_values(by=val_col, ascending=True).tail(10)

    fig = px.bar(
        plot_df,
        x=val_col,
        y=name_col,
        orientation="h",
        title="Top 10 Products by Sales",
        labels={name_col: "Product", val_col: "Sales (USD)"},
        color=val_col,
        color_continuous_scale=[[0.0, "#A78BFA"], [1.0, "#4169E1"]],
    )
    fig.update_layout(
        **BASE_LAYOUT,
        coloraxis_showscale=False,
        yaxis=dict(showgrid=False, linecolor=COLORS["border"]),
        xaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickprefix="$"),
    )
    fig.update_traces(
        marker=dict(cornerradius=5),
        hovertemplate="<b>Product:</b> %{y}<br><b>Sales:</b> $%{x:,.2f}<extra></extra>",
    )
    return fig


def render_channel_comparison_chart(df: pd.DataFrame) -> go.Figure:
    """Renders channel comparison (Store, Web, Catalog) donut chart."""
    if df.empty or "channel" not in df.columns:
        return go.Figure()

    val_col = "sales" if "sales" in df.columns else ("total_sales" if "total_sales" in df.columns else df.columns[1])

    colors = [COLORS["primary"], COLORS["highlight"], "#38BDF8"]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=df["channel"],
                values=df[val_col],
                hole=0.55,
                marker=dict(colors=colors, line=dict(color="#FFFFFF", width=2)),
                textinfo="label+percent",
                hoverinfo="label+value+percent",
                hovertemplate="<b>%{label} Channel</b><br>Sales: $%{value:,.2f}<br>Share: %{percent}<extra></extra>",
            )
        ]
    )
    fig.update_layout(
        **BASE_LAYOUT,
        title="Multi-Channel Sales Distribution",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
    )
    return fig


def render_generic_chart(df: pd.DataFrame, question_hint: str = "") -> go.Figure:
    """
    Intelligently generates a suitable Plotly chart based on dataframe structure.
    Determines whether a bar, line, or donut chart is most appropriate.
    """
    if df.empty or len(df.columns) < 2:
        return go.Figure()

    cols = list(df.columns)
    q = question_hint.lower()

    # Identify numeric columns and categorical/date columns
    numeric_cols = [c for c in cols if pd.api.types.is_numeric_dtype(df[c])]
    non_numeric_cols = [c for c in cols if c not in numeric_cols]

    if not numeric_cols:
        return go.Figure()

    num_col = numeric_cols[0]
    cat_col = non_numeric_cols[0] if non_numeric_cols else cols[0]

    # 1. Time series trend (if date or month column exists)
    is_time = any("date" in c.lower() or "month" in c.lower() or "year" in c.lower() for c in cols)
    if is_time:
        time_col = [c for c in cols if any(k in c.lower() for k in ["date", "month", "year"])][0]
        fig = px.line(
            df,
            x=time_col,
            y=num_col,
            title=f"{num_col.replace('_', ' ').title()} Over Time",
            markers=True,
            line_shape="spline",
        )
        fig.update_traces(line=dict(color=COLORS["primary"], width=3), marker=dict(size=6, color=COLORS["highlight"]))
        fig.update_layout(**BASE_LAYOUT)
        return fig

    # 2. Composition / Channel pie chart (if small number of rows e.g. <= 5 or channel)
    if len(df) <= 5 and any(k in q for k in ["channel", "proportion", "share", "ratio", "breakdown"]):
        fig = px.pie(
            df,
            names=cat_col,
            values=num_col,
            title=f"{cat_col.replace('_', ' ').title()} Share",
            hole=0.45,
            color_discrete_sequence=[COLORS["primary"], COLORS["highlight"], "#38BDF8", "#A78BFA", "#BAE6FD"],
        )
        fig.update_layout(**BASE_LAYOUT)
        return fig

    # 3. Bar chart default for rankings & comparisons
    is_ranking = any(k in q for k in ["top", "highest", "best", "product", "category"]) or len(df) <= 15
    if is_ranking:
        if len(df) > 8:
            # Horizontal bar
            fig = px.bar(
                df.tail(12),
                x=num_col,
                y=cat_col,
                orientation="h",
                title=f"{num_col.replace('_', ' ').title()} by {cat_col.replace('_', ' ').title()}",
                color=num_col,
                color_continuous_scale=[[0.0, "#A78BFA"], [1.0, "#4169E1"]],
            )
            fig.update_layout(**BASE_LAYOUT, coloraxis_showscale=False)
            fig.update_traces(marker=dict(cornerradius=4))
            return fig
        else:
            # Vertical bar
            fig = px.bar(
                df,
                x=cat_col,
                y=num_col,
                title=f"{num_col.replace('_', ' ').title()} by {cat_col.replace('_', ' ').title()}",
                color=num_col,
                color_continuous_scale=[[0.0, "#BAE6FD"], [0.5, "#4169E1"], [1.0, "#8B5CF6"]],
            )
            fig.update_layout(**BASE_LAYOUT, coloraxis_showscale=False)
            fig.update_traces(marker=dict(cornerradius=6))
            return fig

    # Generic bar
    fig = px.bar(df, x=cat_col, y=num_col, title=f"Analysis of {num_col}")
    fig.update_layout(**BASE_LAYOUT)
    return fig
