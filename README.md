# example1

import pandas as pd
import streamlit as st


# ============================================================
# Helpers
# ============================================================

AVAILABLE_VALUES = {"available", "yes", "y", "true", "1"}


def _is_available(value) -> bool:
    """Return True when a value represents available data."""
    if pd.isna(value):
        return False

    return str(value).strip().lower() in AVAILABLE_VALUES


def _availability_count(df: pd.DataFrame, column: str) -> int:
    """Count unique studies with data available for a given column."""
    if column not in df.columns or "Study ID" not in df.columns:
        return 0

    temp = df[["Study ID", column]].copy()
    temp = temp[temp[column].apply(_is_available)]

    return temp["Study ID"].dropna().astype(str).nunique()


def _status_icon(value) -> str:
    """Convert availability values into a compact visual indicator."""
    if pd.isna(value):
        return "—"

    value = str(value).strip().lower()

    if value in {"available", "yes", "y", "true", "1"}:
        return "●"

    if value in {"pending", "in progress"}:
        return "◐"

    if value in {"missing", "no", "n", "false", "0"}:
        return "○"

    return "—"


def _split_locations(value) -> list[str]:
    """
    Split multiline location cells into individual paths.
    Keeps the Excel structure as one study per row while allowing
    paths to be displayed separately in the dashboard.
    """
    if pd.isna(value):
        return []

    text = str(value).strip()

    if not text:
        return []

    # Locations in the workbook are expected to be separated
    # by line breaks.
    locations = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    return locations


def _render_location_block(
    title: str,
    status_value,
    location_value,
):
    """Render one Data Locations section."""

    available = _is_available(status_value)
    locations = _split_locations(location_value)

    status = "Available" if available else "Missing"

    st.markdown(
        f"""
        <div style="
            border: 1px solid rgba(128,128,128,0.25);
            border-radius: 12px;
            padding: 16px 18px;
            margin-bottom: 12px;
        ">
            <div style="
                display:flex;
                justify-content:space-between;
                align-items:center;
                margin-bottom:4px;
            ">
                <strong>{title}</strong>
                <span style="
                    font-size:12px;
                    font-weight:700;
                    opacity:0.80;
                ">
                    {status}
                </span>
            </div>
            <div style="
                font-size:12px;
                opacity:0.65;
            ">
                {len(locations)} location{"s" if len(locations) != 1 else ""}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if locations:
        with st.expander(
            f"View {len(locations)} {title.lower()} location"
            f'{"s" if len(locations) != 1 else ""}'
        ):
            for i, location in enumerate(locations, start=1):
                st.markdown(f"**Location {i}**")
                st.code(location, language=None)

    elif available:
        st.caption("Available, but no location is currently registered.")

    else:
        st.caption("No location registered.")


# ============================================================
# Main page
# ============================================================

def render(filtered, data):

    # --------------------------------------------------------
    # Header
    # --------------------------------------------------------

    st.header("Data Availability")

    st.markdown(
        """
        <div class="section-note">
            Study-level availability across clinical source data,
            SDTM/ADaM, analysis-ready datasets, annotations,
            clinical ground truth and feature vectors.
        </div>
        """,
        unsafe_allow_html=True,
    )

    df = filtered.get("02_DATA_AVAILABILITY", pd.DataFrame()).copy()

    if df.empty:
        st.info("No data availability records found for the selected filters.")
        return

    # --------------------------------------------------------
    # KPI cards
    # --------------------------------------------------------

    total_studies = (
        df["Study ID"].dropna().astype(str).nunique()
        if "Study ID" in df.columns
        else 0
    )

    sdtm_adam = max(
        _availability_count(df, "SDTM/ADaM (Med.ai)"),
        _availability_count(df, "SDTM/ADaM (Domino)"),
    )

    ard = _availability_count(
        df,
        "Analysis-Ready-Dataset (ARD)"
    )

    annotations = _availability_count(
        df,
        "Annotations"
    )

    clinical_gt = _availability_count(
        df,
        "Clinical GT"
    )

    feature_vectors = _availability_count(
        df,
        "Feature Vectors"
    )

    k1, k2, k3, k4, k5, k6 = st.columns(6)

    k1.metric("Studies", total_studies)
    k2.metric("SDTM/ADaM", sdtm_adam)
    k3.metric("ARD", ard)
    k4.metric("Annotations", annotations)
    k5.metric("Clinical GT", clinical_gt)
    k6.metric("Feature Vectors", feature_vectors)

    st.markdown("")

    # --------------------------------------------------------
    # Availability Matrix
    # --------------------------------------------------------

    st.subheader("Availability Matrix")

    st.markdown(
        """
        <div class="section-note">
            Study-level overview of available data assets.
            ● Available &nbsp;&nbsp; ○ Missing / No &nbsp;&nbsp; ◐ Pending
        </div>
        """,
        unsafe_allow_html=True,
    )

    matrix_columns = [
        "Study ID",
        "Study Name",
        "Videos",
        "SDTM/ADaM (Med.ai)",
        "SDTM/ADaM (Domino)",
        "Analysis-Ready-Dataset (ARD)",
        "Symptom Data",
        "QS",
        "ADQS",
        "Annotations",
        "Clinical GT",
        "Feature Vectors",
    ]

    existing_columns = [
        col for col in matrix_columns
        if col in df.columns
    ]

    matrix = df[existing_columns].copy()

    # Remove rows without a Study ID
    if "Study ID" in matrix.columns:
        matrix = matrix[
            matrix["Study ID"].notna()
            & matrix["Study ID"].astype(str).str.strip().ne("")
        ]

    # Convert availability values to visual indicators
    identifier_columns = {"Study ID", "Study Name"}

    for col in matrix.columns:
        if col not in identifier_columns:
            matrix[col] = matrix[col].apply(_status_icon)

    # Shorter display names
    matrix = matrix.rename(
        columns={
            "SDTM/ADaM (Med.ai)": "Med.ai",
            "SDTM/ADaM (Domino)": "Domino",
            "Analysis-Ready-Dataset (ARD)": "ARD",
            "Symptom Data": "Symptom",
            "Clinical GT": "Clinical GT",
            "Feature Vectors": "Feature Vectors",
        }
    )

    st.dataframe(
        matrix,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Study ID": st.column_config.TextColumn(
                "Study ID",
                width="medium",
            ),
            "Study Name": st.column_config.TextColumn(
                "Study",
                width="medium",
            ),
            "Med.ai": st.column_config.TextColumn(
                "Med.ai",
                width="small",
            ),
            "Domino": st.column_config.TextColumn(
                "Domino",
                width="small",
            ),
            "ARD": st.column_config.TextColumn(
                "ARD",
                width="small",
            ),
            "Symptom": st.column_config.TextColumn(
                "Symptom",
                width="small",
            ),
            "QS": st.column_config.TextColumn(
                "QS",
                width="small",
            ),
            "ADQS": st.column_config.TextColumn(
                "ADQS",
                width="small",
            ),
            "Annotations": st.column_config.TextColumn(
                "Annotations",
                width="small",
            ),
            "Clinical GT": st.column_config.TextColumn(
                "Clinical GT",
                width="small",
            ),
            "Feature Vectors": st.column_config.TextColumn(
                "Feature Vectors",
                width="small",
            ),
        },
        key="availability_matrix",
    )

    # --------------------------------------------------------
    # Data Locations
    # --------------------------------------------------------

    st.markdown("---")
    st.subheader("Data Locations")

    st.markdown(
        """
        <div class="section-note">
            Detailed storage locations are shown when a single study
            is selected from the sidebar.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Determine studies represented in current filtered dataset
    if "Study ID" not in df.columns:
        st.info("Study ID is required to display data locations.")
        return

    valid_df = df[
        df["Study ID"].notna()
        & df["Study ID"].astype(str).str.strip().ne("")
    ].copy()

    study_ids = valid_df["Study ID"].astype(str).unique()

    if len(study_ids) != 1:
        st.info(
            "Select one study from the sidebar to view its "
            "Annotations, Clinical GT and Feature Vector locations."
        )
        return

    study_df = valid_df[
        valid_df["Study ID"].astype(str) == study_ids[0]
    ]

    row = study_df.iloc[0]

    study_name = (
        str(row.get("Study Name", "")).strip()
        if pd.notna(row.get("Study Name"))
        else ""
    )

    study_id = str(row.get("Study ID", "")).strip()

    if study_name:
        st.markdown(f"### {study_name}")
        st.caption(study_id)
    else:
        st.markdown(f"### {study_id}")

    # --------------------------------------------------------
    # Location cards
    # --------------------------------------------------------

    _render_location_block(
        "Annotations",
        row.get("Annotations"),
        row.get("Annotations Location"),
    )

    _render_location_block(
        "Clinical GT",
        row.get("Clinical GT"),
        row.get("Clinical GT Location"),
    )

    _render_location_block(
        "Feature Vectors",
        row.get("Feature Vectors"),
        row.get("Feature Vectors Location"),
    )
