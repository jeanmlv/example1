# example1

import pandas as pd
import plotly.express as px
import streamlit as st

from src.ui import show_table


# ============================================================
# ARD - Configuration
# ============================================================

COLORS = {
    "High": "#12B76A",
    "Medium": "#F79009",
    "Low": "#D92D20",
    "Mapped": "#12B76A",
    "Missing": "#F79009",
    "Available": "#12B76A",
    "Not available": "#98A2B3",
}


# ============================================================
# ARD - Data preparation
# ============================================================

def build_ard_data(filtered):
    """
    Build study-level ARD readiness and mapping metrics.

    Sources:
        01_STUDIES: selected study population
        06_ARD: ARD availability and inventory metadata
        06C_ARD_VARIABLES: detailed VOI mapping records

    Mapping metrics include only studies with available ARDs.
    """

    studies = filtered["01_STUDIES"].copy()
    inventory = filtered["06_ARD"].copy()
    voi = filtered["06C_ARD_VARIABLES"].copy()

    # Normalize study identifiers
    for frame in (studies, inventory, voi):
        frame["Study ID"] = (
            frame["Study ID"]
            .astype("string")
            .str.strip()
        )

    studies = (
        studies
        .dropna(subset=["Study ID"])
        .drop_duplicates("Study ID")
    )

    # Restrict inventory to selected studies
    inventory = inventory[
        inventory["Study ID"].isin(studies["Study ID"])
    ].copy()

    # Identify studies with documented ARD files
    names = (
        inventory["ARD Name"]
        .astype("string")
        .str.strip()
        .str.lower()
    )

    invalid_names = [
        "",
        "none",
        "nan",
        "not available",
        "n/a",
        "na",
        "-",
    ]

    available = inventory[
        names.notna()
        & ~names.isin(invalid_names)
    ]

    available_ids = set(available["Study ID"])

    # Mapping records for studies with available ARDs
    voi = voi[
        voi["Study ID"].isin(available_ids)
    ].copy()

    voi["Status"] = (
        voi["Status"]
        .astype("string")
        .str.strip()
        .str.title()
    )

    # Use only recognized mapping statuses
    valid = voi[
        voi["Status"].isin(["Mapped", "Missing"])
    ]

    # Count detailed mapping records by study
    counts = (
        valid.groupby(["Study ID", "Status"])
        .size()
        .unstack(fill_value=0)
        .reindex(
            columns=["Mapped", "Missing"],
            fill_value=0
        )
    )

    # Study-level summary
    summary = studies[
        ["Study ID", "Study Name"]
    ].copy()

    summary["ARD Status"] = summary["Study ID"].map(
        lambda x: (
            "Available"
            if x in available_ids
            else "Not available"
        )
    )

    summary = summary.merge(
        counts.reset_index(),
        on="Study ID",
        how="left"
    )

    # Calculate actual VOI coverage
    summary["Total VOI"] = (
        summary["Mapped"] + summary["Missing"]
    )

    summary["Coverage %"] = summary["Mapped"].div(
        summary["Total VOI"].where(
            summary["Total VOI"] > 0
        )
    )

    # Recalculate coverage classification
    summary["Coverage Level"] = pd.cut(
        summary["Coverage %"],
        bins=[-0.001, 0.5, 0.8, 1.0],
        labels=["Low", "Medium", "High"],
        right=False,
        include_lowest=True,
    ).astype("string")

    summary.loc[
        summary["Coverage %"].eq(1),
        "Coverage Level"
    ] = "High"

    summary["Coverage Level"] = (
        summary["Coverage Level"]
        .fillna("Not assessed")
    )

    return summary, inventory, voi


# ============================================================
# ARD - Donut chart helper
# ============================================================

def render_donut(
    labels,
    values,
    title,
    center,
    key
):
    """Render a compact portfolio donut chart."""

    if not sum(values):
        st.subheader(title)
        st.caption("No records in the selected scope.")
        return

    fig = px.pie(
        names=labels,
        values=values,
        hole=0.72,
        color=labels,
        color_discrete_map=COLORS,
    )

    fig.update_traces(
        textinfo="percent",
        hovertemplate=(
            "%{label}: %{value:,}"
            "<extra></extra>"
        ),
    )

    fig.update_layout(
        title=title,
        height=300,
        margin=dict(
            l=10,
            r=10,
            t=45,
            b=10
        ),
        legend=dict(
            orientation="h",
            y=-0.08,
        ),
        annotations=[
            dict(
                text=center,
                x=0.5,
                y=0.5,
                showarrow=False,
                font_size=22,
            )
        ],
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        key=key,
    )


# ============================================================
# ARD - KPI metrics
# ============================================================

def render_metrics(summary):
    """Render portfolio availability and mapping KPIs."""

    total_studies = len(summary)

    available = summary[
        summary["ARD Status"].eq("Available")
    ]

    available_studies = len(available)

    mapped = int(
        available["Mapped"].sum()
    )

    missing = int(
        available["Missing"].sum()
    )

    total_voi = mapped + missing

    overall_coverage = (
        mapped / total_voi
        if total_voi > 0
        else None
    )

    ard_availability = (
        available_studies / total_studies
        if total_studies > 0
        else None
    )

    coverage_text = (
        f"{overall_coverage:.1%}"
        if overall_coverage is not None
        else "—"
    )

    availability_text = (
        f"{ard_availability:.1%}"
        if ard_availability is not None
        else "—"
    )

    # --------------------------------------------------------
    # Row 1 - ARD availability
    # --------------------------------------------------------

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Studies in scope",
        total_studies,
        help=(
            "Total unique studies included "
            "in the current global filter selection."
        ),
    )

    c2.metric(
        "ARD available",
        available_studies,
        help=(
            "Studies with a documented ARD "
            "filename in 06_ARD."
        ),
    )

    c3.metric(
        "ARD availability",
        availability_text,
        help=(
            "Studies with available ARDs divided "
            "by all studies in the selected scope."
        ),
    )

    # --------------------------------------------------------
    # Row 2 - VOI mapping coverage
    # --------------------------------------------------------

    c4, c5, c6 = st.columns(3)

    c4.metric(
        "Mapped VOI",
        f"{mapped:,}",
        help=(
            "Number of study-variable records "
            "classified as Mapped in 06C_ARD_VARIABLES."
        ),
    )

    c5.metric(
        "Missing VOI",
        f"{missing:,}",
        help=(
            "Number of study-variable records "
            "classified as Missing in 06C_ARD_VARIABLES."
        ),
    )

    c6.metric(
        "Overall VOI Coverage",
        coverage_text,
        help=(
            "Mapped VOI divided by Mapped + Missing VOI. "
            "Calculated from 06C_ARD_VARIABLES for "
            "studies with available ARDs."
        ),
    )

    st.caption(
        "Mapping metrics count study-variable records, "
        "not unique variable names. Studies without ARDs "
        "are excluded from VOI mapping metrics."
    )

    return {
        "total_studies": total_studies,
        "available_studies": available_studies,
        "unavailable_studies": (
            total_studies - available_studies
        ),
        "mapped": mapped,
        "missing": missing,
        "total_voi": total_voi,
        "coverage_text": coverage_text,
        "availability_text": availability_text,
    }

# ============================================================
# ARD - Coverage explorer
# ============================================================

def render_coverage_chart(summary):

    st.subheader("Study Mapping Coverage")

    st.caption(
        "Variable-of-interest mapping coverage by study, "
        "based on detailed mapping records."
    )

    available = summary[
        summary["ARD Status"].eq("Available")
    ].copy()

    chart = available.dropna(
        subset=["Coverage %"]
    ).copy()

    # Coverage filters
    c1, c2 = st.columns([2, 1])

    with c1:

        levels = st.multiselect(
            "Coverage level",
            options=[
                "High",
                "Medium",
                "Low"
            ],
            key="ard_coverage_levels",
        )

    with c2:

        sort_order = st.selectbox(
            "Sort by",
            options=[
                "Highest coverage",
                "Lowest coverage",
                "Study name",
            ],
            key="ard_coverage_sort",
        )

    if levels:
        chart = chart[
            chart["Coverage Level"].isin(levels)
        ]

    if sort_order == "Highest coverage":

        chart = chart.sort_values(
            "Coverage %",
            ascending=True
        )

    elif sort_order == "Lowest coverage":

        chart = chart.sort_values(
            "Coverage %",
            ascending=False
        )

    else:

        chart = chart.sort_values(
            "Study Name",
            ascending=False
        )

    st.caption(
        f"{len(chart)} of {len(available)} studies "
        "with available ARDs displayed."
    )

    if chart.empty:

        st.info(
            "No mapping coverage available "
            "for the selected filters."
        )

        return

    fig = px.bar(
        chart,
        x="Coverage %",
        y="Study Name",
        color="Coverage Level",
        orientation="h",
        text="Coverage %",
        color_discrete_map=COLORS,
        custom_data=[
            "Mapped",
            "Missing",
            "Total VOI",
        ],
        category_orders={
            "Coverage Level": [
                "High",
                "Medium",
                "Low",
            ]
        },
    )

    fig.update_traces(
        texttemplate="%{text:.1%}",
        textposition="outside",
        cliponaxis=False,
        hovertemplate=(
            "<b>%{y}</b>"
            "<br>Coverage: %{x:.1%}"
            "<br>Mapped VOI: %{customdata[0]:.0f}"
            "<br>Missing VOI: %{customdata[1]:.0f}"
            "<br>Total VOI: %{customdata[2]:.0f}"
            "<extra></extra>"
        ),
    )

    fig.update_xaxes(
        tickformat=".0%",
        range=[0, 1.12],
        title="VOI Mapping Coverage",
        tickvals=[
            0,
            0.2,
            0.4,
            0.6,
            0.8,
            1.0,
        ],
    )

    fig.update_yaxes(
        categoryorder="array",
        categoryarray=chart["Study Name"].tolist(),
        title="",
    )

    fig.update_layout(
        height=max(
            320,
            25 * len(chart) + 80
        ),
        margin=dict(
            l=5,
            r=45,
            t=15,
            b=10,
        ),
        legend_title_text="Coverage level",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        bargap=0.25,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        key="ard_coverage_chart",
    )

    st.caption(
        "Coverage levels: High ≥ 80% | "
        "Medium ≥ 50% and < 80% | Low < 50%. "
        "Studies without valid mapping records "
        "are not included in this chart."
    )


# ============================================================
# ARD - Inventory tab
# ============================================================

def render_inventory(summary, inventory):

    st.markdown("#### ARD Inventory")

    st.caption(
        "Study-level ARD availability, file locations "
        "and recalculated VOI mapping coverage."
    )

    availability_filter = st.selectbox(
        "ARD availability",
        options=[
            "All",
            "Available",
            "Not available",
        ],
        key="ard_inventory_status",
    )

    # Remove legacy mapping columns before joining
    metadata = inventory.drop(
        columns=[
            "Study Name",
            "Mapped",
            "Missing",
            "Coverage %",
            "Coverage Level",
            "Total Variables of Interest",
            "Total VOI",
            "ARD Status",
        ],
        errors="ignore",
    )

    table = summary.merge(
        metadata,
        on="Study ID",
        how="left",
    )

    if availability_filter != "All":

        table = table[
            table["ARD Status"].eq(
                availability_filter
            )
        ]

    # Display percentages rather than Excel fractions
    table["Coverage %"] = table["Coverage %"].map(
        lambda x: (
            f"{x:.1%}"
            if pd.notna(x)
            else "—"
        )
    )

    for col in [
        "Mapped",
        "Missing",
        "Total VOI",
    ]:

        table[col] = (
            table[col]
            .astype("Int64")
        )

    # Professional column ordering
    preferred_columns = [
        "Study ID",
        "Study Name",
        "ARD Status",
        "ARD Name",
        "Location",
        "Total VOI",
        "Mapped",
        "Missing",
        "Coverage %",
        "Coverage Level",
    ]

    ordered_columns = [
        c for c in preferred_columns
        if c in table.columns
    ]

    remaining_columns = [
        c for c in table.columns
        if c not in ordered_columns
    ]

    table = table[
        ordered_columns + remaining_columns
    ]

    st.caption(
        f"{len(table):,} inventory records displayed."
    )

    show_table(
        table,
        key="ard_table",
        link_cols=["Location"],
    )


# ============================================================
# ARD - Variable mapping tab
# ============================================================

def render_variable_mapping(voi):

    st.markdown("#### Variable Mapping Explorer")

    st.caption(
        "Explore individual variable-of-interest "
        "mapping records from 06C_ARD_VARIABLES."
    )

    if voi.empty:

        st.info(
            "No variable mapping records "
            "are available for the selected studies."
        )

        return

    detail = voi.copy()

    study_names = sorted(
        detail["Study Name"]
        .dropna()
        .astype(str)
        .unique()
    )

    c1, c2 = st.columns(2)

    with c1:

        selected_studies = st.multiselect(
            "Study",
            options=study_names,
            key="ard_voi_studies",
        )

    with c2:

        selected_statuses = st.multiselect(
            "Mapping status",
            options=[
                "Mapped",
                "Missing",
            ],
            key="ard_voi_status",
        )

    search = st.text_input(
        "Search variables",
        placeholder=(
            "Variable name, description, ARD code..."
        ),
        key="ard_voi_search",
    ).strip()

    if selected_studies:

        detail = detail[
            detail["Study Name"]
            .isin(selected_studies)
        ]

    if selected_statuses:

        detail = detail[
            detail["Status"]
            .isin(selected_statuses)
        ]

    if search:

        search_columns = [
            c for c in detail.columns
            if c not in [
                "Study ID",
                "Status"
            ]
        ]

        if search_columns:

            mask = (
                detail[search_columns]
                .astype("string")
                .apply(
                    lambda s: s.str.contains(
                        search,
                        case=False,
                        regex=False,
                        na=False,
                    )
                )
                .any(axis=1)
            )

            detail = detail[mask]

    st.caption(
        f"{len(detail):,} of {len(voi):,} "
        "mapping records displayed."
    )

    show_table(
        detail,
        key="ard_voi_table",
    )

# ============================================================
# ARD - Main render
# ============================================================

def render(filtered, data):

    st.header("Analysis-Ready Dataset (ARD)")

    st.markdown(
        '<div class="section-note">'
        "Clinical data readiness, variable mapping "
        "coverage and ARD inventory across the "
        "ARGES portfolio."
        "</div>",
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # Prepare filtered data
    # --------------------------------------------------------

    try:

        summary, inventory, voi = build_ard_data(
            filtered
        )

    except KeyError as exc:

        st.error(
            f"Required ARD sheet or column "
            f"is missing: {exc}"
        )

        return

    if summary.empty:

        st.info(
            "No studies match the selected filters."
        )

        return

    # --------------------------------------------------------
    # 1. Portfolio KPIs
    # --------------------------------------------------------

    metrics = render_metrics(summary)

    # --------------------------------------------------------
    # 2. Study mapping coverage
    # --------------------------------------------------------

    st.markdown("---")

    render_coverage_chart(summary)

    # --------------------------------------------------------
    # 3. ARD Explorer
    # --------------------------------------------------------

    st.markdown("---")

    st.subheader("ARD Explorer")

    st.caption(
        "Study-level inventory, variable traceability, "
        "mapping gaps and data quality checks."
    )

    tab1, tab2 = st.tabs(
        [
            "ARD Inventory",
            "Variable Mapping",
        ]
    )

    with tab1:

        render_inventory(
            summary,
            inventory,
        )

    with tab2:

        render_variable_mapping(
            voi
        )


