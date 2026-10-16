# example1


import pandas as pd
import plotly.express as px
import streamlit as st

from src.ui import show_table, download_row


# ============================================================
# ARD - Helper functions
# ============================================================

def get_coverage(series):
    """
    Convert coverage values to numeric percentages (0-100).

    Supports:
    - Numeric values between 0 and 1 (e.g. 0.89)
    - Percentage strings (e.g. "89%")
    - Missing or invalid values
    """
    if series is None:
        return pd.Series(dtype=float)

    raw = series.astype("string").str.strip()
    has_percent = raw.str.contains("%", regex=False, na=False)

    values = pd.to_numeric(
        raw.str.replace("%", "", regex=False)
           .str.replace(",", ".", regex=False),
        errors="coerce"
    )

    # Excel percentages may be stored as fractions.
    # If percentage symbols exist, those values are already 0-100.
    if not has_percent.any():
        valid = values.dropna()
        if not valid.empty and valid.between(0, 1).all():
            values = values * 100

    return values


def calculate_mean_coverage(df):
    """
    Calculate mean ARD coverage considering only
    studies with coverage >= 1%.
    """
    if df.empty or "Coverage %" not in df.columns:
        return float("nan")

    coverage = get_coverage(df["Coverage %"])

    valid_coverage = coverage[coverage >= 1]

    return valid_coverage.mean()


# ============================================================
# ARD - KPI metrics
# ============================================================

def render_metrics(df):

    c1, c2, c3, c4 = st.columns(4)

    # ARD records
    c1.metric(
        "ARD records",
        len(df)
    )

    # Mapped variables of interest
    mapped = (
        pd.to_numeric(df["Mapped"], errors="coerce").sum()
        if "Mapped" in df.columns
        else 0
    )

    c2.metric(
        "Mapped VOI",
        f"{mapped:,.0f}"
    )

    # Missing variables of interest
    missing = (
        pd.to_numeric(df["Missing"], errors="coerce").sum()
        if "Missing" in df.columns
        else 0
    )

    c3.metric(
        "Missing VOI",
        f"{missing:,.0f}"
    )

    # Mean coverage - exclude studies below 1%
    avg = calculate_mean_coverage(df)

    c4.metric(
        "Mean coverage",
        f"{avg:.0f}%" if pd.notna(avg) else "—",
        help="Average ARD coverage considering only studies with coverage >= 1%."
    )


# ============================================================
# ARD - Coverage chart
# ============================================================

def render_coverage_chart(df):

    required_columns = {"Study Name", "Coverage %"}

    if df.empty or not required_columns.issubset(df.columns):
        return

    cols = ["Study Name", "Coverage %"]

    if "Coverage Level" in df.columns:
        cols.append("Coverage Level")

    x = df[cols].copy()

    # Convert coverage to percentage scale (0-100)
    x["Coverage %"] = get_coverage(x["Coverage %"])

    x = x.dropna(subset=["Coverage %"])

    if x.empty:
        return

    x = x.sort_values("Coverage %")

    # Convert to fraction for Plotly percentage formatting
    x["Coverage Plot"] = x["Coverage %"] / 100

    fig = px.bar(
        x,
        x="Coverage Plot",
        y="Study Name",
        orientation="h",
        color=(
            "Coverage Level"
            if "Coverage Level" in x.columns
            else None
        ),
        text="Coverage Plot",
        color_discrete_map={
            "High": "#12B76A",
            "Medium": "#F79009",
            "Low": "#D92D20"
        },
        custom_data=["Coverage %"]
    )

    fig.update_traces(
        texttemplate="%{text:.0%}",
        textposition="inside",
        hovertemplate=(
            "Study: %{y}"
            "<br>Coverage: %{customdata[0]:.1f}%"
            "<extra></extra>"
        )
    )

    fig.update_xaxes(
        tickformat=".0%",
        range=[0, 1]
    )

    fig.update_layout(
        height=max(330, 28 * len(x)),
        margin=dict(l=5, r=5, t=15, b=10),
        xaxis_title="Coverage",
        yaxis_title="",
        legend_title_text=""
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ============================================================
# ARD - Main render
# ============================================================

def render(filtered, data):

    st.header("Analysis-Ready Data (ARD)")

    st.markdown(
        '<div class="section-note">'
        'ARD inventory, variable-of-interest mapping coverage, '
        'and gap status by study.'
        '</div>',
        unsafe_allow_html=True
    )

    # Filtered ARD inventory
    df = filtered.get("06_ARD", pd.DataFrame())

    # KPI metrics
    render_metrics(df)

    # Coverage visualization
    render_coverage_chart(df)

    # ARD inventory table
    show_table(
        df,
        key="ard_table",
        link_cols=["Location"]
    )

    # Export data
    download_row(
        df,
        "filtered_ard"
    )

