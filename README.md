# example1

############# arges commons dashboard.py


import os
import re
import sys
from pathlib import Path

import pandas as pd
import streamlit as st


# =========================================================
# PATH CONFIGURATION
# =========================================================

COMMONS_DIRECTORY = Path(__file__).resolve().parent

if str(COMMONS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(COMMONS_DIRECTORY))

LOCAL_WORKBOOK = COMMONS_DIRECTORY / "ARGES_COMMONS.xlsx"


# =========================================================
# PROJECT IMPORTS
# =========================================================

from src.config import REQUIRED_SHEETS, PAGES, JNJ_RED
from src.data_loader import filter_by_study
from src.filters import clean_text_values

from views import (
    overview,
    studies_assets,
    data_availability,
    processing,
    data_splits,
    ard,
    variable_definitions,
    data_analysis,
    external_data,
    arges_models,
    deployments,
)


# =========================================================
# DATA SOURCE CONFIGURATION
# =========================================================

# Default: SharePoint (Domino / production)
#
# For local development:
# PowerShell:
# $env:ARGES_DATA_SOURCE = "local"
#
# This avoids requiring SharePoint credentials
# when testing the dashboard locally.

DATA_SOURCE = os.getenv(
    "ARGES_DATA_SOURCE",
    "sharepoint",
).strip().lower()

if DATA_SOURCE not in {"local", "sharepoint"}:
    st.error(
        "Invalid ARGES_DATA_SOURCE. "
        "Expected 'local' or 'sharepoint'."
    )
    st.stop()


# =========================================================
# WORKBOOK LOADING
# =========================================================

@st.cache_data(
    ttl=3600,
    show_spinner="Loading ARGES Commons workbook...",
)
def load_data(
    source: str,
    local_path: str,
    local_mtime: int = 0,
) -> dict[str, pd.DataFrame]:
    """
    Load ARGES Commons from the configured data source.

    Local:
        Read the Excel workbook from the dashboard directory.

    SharePoint:
        Retrieve the shared workbook using Microsoft Graph.

    local_mtime:
        Included in the cache key so changes to the local
        workbook invalidate cached data.
    """

    if source == "local":

        workbook_path = Path(local_path)

        if not workbook_path.is_file():
            raise FileNotFoundError(
                f"Local workbook not found: {workbook_path}"
            )

        frames = pd.read_excel(
            workbook_path,
            sheet_name=None,
            engine="openpyxl",
        )

    elif source == "sharepoint":

        # Import only when SharePoint is required.
        from src.fetch_arges_commons_workbook import (
            load_workbook,
        )

        frames = load_workbook(verbose=False)

    else:
        raise ValueError(f"Unsupported data source: {source}")

    # Normalize sheet names and column names.
    out = {}

    for name, df in frames.items():

        df = df.copy()

        df.columns = [
            re.sub(
                r"\s+",
                " ",
                str(c).replace("\n", " "),
            ).strip()
            for c in df.columns
        ]

        out[str(name).strip()] = df.dropna(how="all")

    return out


# =========================================================
# STUDY FILTERS
# =========================================================

def render_filters(
    studies: pd.DataFrame,
) -> tuple[pd.DataFrame, set[str]]:
    """
    Render main-page study filters.

    Filters are applied sequentially so available options
    reflect previous selections.
    """

    st.subheader("Filters")

    eligible = studies.copy()

    filter_specs = (
        ("Study", "Study Name"),
        ("Disease", "Disease"),
        ("Phase", "Phase"),
        ("Trial status", "Trial Status"),
        ("Compound", "Compound"),
    )

    columns = st.columns(len(filter_specs))

    for column, (label, field) in zip(
        columns,
        filter_specs,
    ):

        options = clean_text_values(
            eligible.get(
                field,
                pd.Series(dtype=str),
            )
        )

        widget_key = (
            "arges_commons_filter_"
            + field.lower().replace(" ", "_")
        )

        # Remove selections that are no longer available
        # after applying an upstream filter.
        previous = st.session_state.get(widget_key, [])

        valid_previous = [
            value
            for value in previous
            if value in options
        ]

        if previous != valid_previous:
            st.session_state[widget_key] = valid_previous

        with column:

            selected = st.multiselect(
                label,
                options,
                key=widget_key,
            )

        if selected and field in eligible.columns:

            eligible = eligible[
                eligible[field]
                .astype(str)
                .str.strip()
                .isin(selected)
            ].copy()

    selected_ids = set(
        eligible["Study ID"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    total_studies = (
        studies["Study ID"]
        .dropna()
        .astype(str)
        .str.strip()
        .nunique()
    )

    st.caption(
        f"{len(selected_ids)} of "
        f"{total_studies} studies selected"
    )

    # Selected study names.
    with st.expander(
        f"View selected studies ({len(selected_ids)})",
        expanded=False,
    ):

        if eligible.empty:

            st.info(
                "No studies match the current filters."
            )

        else:

            display_cols = [
                col
                for col in [
                    "Study Name",
                    "Study ID",
                    "Disease",
                    "Phase",
                ]
                if col in eligible.columns
            ]

            selected_studies = (
                eligible[display_cols]
                .drop_duplicates()
                .copy()
            )

            if "Study Name" in selected_studies.columns:

                selected_studies = (
                    selected_studies.sort_values(
                        "Study Name"
                    )
                )

            st.dataframe(
                selected_studies,
                use_container_width=True,
                hide_index=True,
            )

    # Workbook refresh.
    if DATA_SOURCE == "sharepoint":

        st.button(
            "🔄 Reload workbook from SharePoint",
            on_click=load_data.clear,
            key="arges_reload_sharepoint",
        )

    else:

        st.button(
            "🔄 Reload local workbook",
            on_click=load_data.clear,
            key="arges_reload_local",
        )

        st.caption(
            "Local development mode — "
            "using the local ARGES_COMMONS.xlsx."
        )

    st.markdown("---")

    return eligible, selected_ids


# =========================================================
# THEME-AWARE STYLING
# =========================================================

st.markdown(
    f"""
    <style>

    /* Main application */

    .stApp {{
        background-color: var(--background-color);
        color: var(--text-color);
    }}

    .block-container {{
        padding-top: 1.3rem;
        padding-bottom: 3rem;
        max-width: 1500px;
    }}

    /* Typography */

    h1, h2, h3 {{
        letter-spacing: -0.02em;
        color: var(--text-color);
    }}

    h1 {{
        font-size: 2rem !important;
    }}

    /* KPI cards */

    div[data-testid="stMetric"] {{
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.25);
        border-radius: 14px;
        padding: 14px 16px;
        box-shadow: 0 2px 10px rgba(16, 24, 40, 0.06);
    }}

    div[data-testid="stMetricLabel"] {{
        color: var(--text-color) !important;
    }}

    div[data-testid="stMetricLabel"] p {{
        color: var(--text-color) !important;
        opacity: 0.78;
    }}

    div[data-testid="stMetricValue"] {{
        color: var(--text-color) !important;
    }}

    div[data-testid="stMetricValue"] > div {{
        color: var(--text-color) !important;
    }}

    /* ARGES branding */

    .hero {{
        padding: 22px 24px;
        border: 1px solid rgba(128, 128, 128, 0.25);
        border-radius: 18px;
        background-color: var(--secondary-background-color);
        margin-bottom: 18px;
    }}

    .hero-title {{
        font-size: 28px;
        font-weight: 800;
        line-height: 1.15;
        margin: 5px 0 6px 0;
        color: var(--text-color);
    }}

    .hero-copy,
    .section-note {{
        color: var(--text-color);
        opacity: 0.70;
        font-size: 13px;
    }}

    /* Tables and controls */

    [data-testid="stDataFrame"] {{
        border: 1px solid rgba(128, 128, 128, 0.25);
        border-radius: 12px;
        overflow: hidden;
    }}

    hr {{
        border-color: rgba(128, 128, 128, 0.25);
    }}

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# LOAD WORKBOOK
# =========================================================

try:

    local_mtime = (
        LOCAL_WORKBOOK.stat().st_mtime_ns
        if DATA_SOURCE == "local"
        and LOCAL_WORKBOOK.is_file()
        else 0
    )

    data = load_data(
        DATA_SOURCE,
        str(LOCAL_WORKBOOK),
        local_mtime,
    )

except (Exception, SystemExit) as exc:

    # The SharePoint helper may raise SystemExit
    # when credentials or Graph access are unavailable.

    st.error(
        f"The workbook could not be loaded "
        f"from {DATA_SOURCE}: {exc}"
    )

    st.button(
        "Retry workbook loading",
        on_click=load_data.clear,
        key="arges_retry_loading",
    )

    st.stop()


# =========================================================
# WORKBOOK VALIDATION
# =========================================================

missing = [
    sheet
    for sheet in REQUIRED_SHEETS
    if sheet not in data
]

if missing:

    st.warning(
        "Some expected sheets are not present: "
        + ", ".join(missing)
    )

studies = data.get(
    "01_STUDIES",
    pd.DataFrame(),
).copy()

if studies.empty or "Study ID" not in studies.columns:

    st.error(
        "Sheet 01_STUDIES with a Study ID column "
        "is required."
    )

    st.stop()


# =========================================================
# HEADER
# =========================================================

st.caption(
    "A study-centric view from source assets and "
    "processing through data splits, analysis-ready "
    "datasets, variable traceability, analyses, "
    "and external data."
)


# =========================================================
# GLOBAL FILTERS
# =========================================================

eligible, selected_ids = render_filters(studies)

filtered = {
    name: filter_by_study(df, selected_ids)
    for name, df in data.items()
}

# Prevent empty study selections from accidentally
# restoring the complete inventory in study-linked tables.
if not selected_ids:

    for name, df in filtered.items():

        if "Study ID" in df.columns:

            filtered[name] = df.iloc[0:0].copy()

filtered["01_STUDIES"] = eligible.copy()


# =========================================================
# PAGE ROUTES
# =========================================================

ROUTES = {
    "Overview": overview.render,
    "Studies & Assets": studies_assets.render,
    "Data Availability": data_availability.render,
    "Processing": processing.render,
    "Data Splits": data_splits.render,
    "ARD": ard.render,
    "Variable Definitions": variable_definitions.render,
    "Data Analysis": data_analysis.render,
    "External Data": external_data.render,
    "ARGES Models": arges_models.render,
    "Deployments": deployments.render,
}

# Preserve the configured navigation order.
# Include new routes if they are not yet listed in PAGES.

navigation_pages = [
    page_name
    for page_name in PAGES
    if page_name in ROUTES
]

for page_name in ROUTES:

    if page_name not in navigation_pages:

        navigation_pages.append(page_name)


# =========================================================
# NAVIGATION
# =========================================================

page = (
    st.segmented_control(
        "Navigation",
        navigation_pages,
        default="Overview",
        label_visibility="collapsed",
        key="arges_commons_navigation",
    )
    or "Overview"
)


# =========================================================
# RENDER SELECTED PAGE
# =========================================================

if page == "Deployments":

    # Persistent writes remain disabled until the
    # SharePoint write integration is approved/configured.
    #
    # Do not pass a local workbook path as a SharePoint
    # write target.

    deployments.render(filtered, data)

else:

    ROUTES[page](filtered, data)


# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption(
    "ARGES Commons • Data shown reflects the selected "
    "workbook and active filters. Validate source metadata "
    "before operational or clinical use."
)


