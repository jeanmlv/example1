# example1

import pandas as pd
import streamlit as st
from pathlib import Path
import sys

COMMONS_DIRECTORY = Path(__file__).resolve().parent
if str(COMMONS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(COMMONS_DIRECTORY))

from src.config import REQUIRED_SHEETS, PAGES
from src.data_loader import (
    load_workbook,
    resolve_default_workbook,
    filter_by_study,
    clean_text_values,
)
from src.ui import apply_theme, render_header
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
)


def render_filters(studies: pd.DataFrame) -> tuple[pd.DataFrame, set[str]]:
    """Render main-page study filters and return the matching study IDs."""
    st.subheader("Filters")
    eligible = studies.copy()
    columns = st.columns(4)
    filter_specs = (
        ("Study", "Study Name"),
        ("Phase", "Phase"),
        ("Trial status", "Trial Status"),
        ("Compound", "Compound"),
    )

    for column, (label, field) in zip(columns, filter_specs):
        with column:
            selected = st.multiselect(
                label,
                clean_text_values(eligible.get(field, pd.Series(dtype=str))),
            )
        if selected and field in eligible:
            eligible = eligible[eligible[field].astype(str).isin(selected)]

    selected_ids = set(eligible["Study ID"].dropna().astype(str))
    st.caption(
        f"{len(selected_ids)} of {studies['Study ID'].nunique()} studies selected"
    )
    st.markdown("---")
    return eligible, selected_ids


apply_theme()

source = resolve_default_workbook()
if source is None:
    st.error(
        "ARGES_COMMONS.xlsx was not found. Place it beside Arges_Commons_Dashboard.py."
    )
    st.stop()
try:
    data = load_workbook(source)
except Exception as exc:
    st.error(f"The workbook could not be loaded: {exc}")
    st.stop()
missing = [s for s in REQUIRED_SHEETS if s not in data]
if missing:
    st.warning("Some expected sheets are not present: " + ", ".join(missing))

studies = data.get("01_STUDIES", pd.DataFrame()).copy()
if studies.empty or "Study ID" not in studies.columns:
    st.error("Sheet 01_STUDIES with a Study ID column is required.")
    st.stop()

# render_header()
st.caption(
    "A study-centric view from source assets and processing through data splits, analysis-ready datasets, variable traceability, analyses, and external data."
)

eligible, selected_ids = render_filters(studies)
page = (
    st.segmented_control(
        "Navigation", PAGES, default="Overview", label_visibility="collapsed"
    )
    or "Overview"
)
filtered = {name: filter_by_study(df, selected_ids) for name, df in data.items()}
filtered["01_STUDIES"] = eligible.copy()
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
}
ROUTES[page](filtered, data)
st.markdown("---")
st.caption(
    "ARGES Commons • Data shown reflects the selected workbook and active filters. Validate source metadata before operational or clinical use."
)
