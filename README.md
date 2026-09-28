# example1

import pandas as pd
import streamlit as st


# =============================================================================
# CONFIGURATION
# =============================================================================

STATUS_COLUMNS = {
    "Videos": "Videos",
    "SDTM/ADaM (Med.ai)": "Med.ai",
    "SDTM/ADaM (Domino)": "Domino",
    "Analysis-Ready-Dataset (ARD)": "ARD",
    "Symptom Data": "Symptom",
    "QS": "QS",
    "ADQS": "ADQS",
    "Annotations": "Annotations",
    "Clinical GT": "Clinical GT",
    "Feature Vectors": "Feature Vectors",
}

LOCATION_COLUMNS = {
    "SDTM/ADaM": "SDTM/ADaM Location",
    "ARD": "ARD Location",
    "Annotations": "Annotations Location",
    "Clinical GT": "Clinical GT Location",
    "Feature Vectors": "Feature Vectors Location",
}


# =============================================================================
# HELPERS
# =============================================================================

def normalize_text(value):
    """Return a clean string representation of a cell value."""
    if pd.isna(value):
        return ""

    text = str(value).strip()

    if text.lower() in {"nan", "none", "null"}:
        return ""

    return text


def split_locations(value):
    """
    Split multiple locations stored in a single Excel cell.

    Expected Excel format:
        path_1
        path_2
        path_3

    Each location should preferably be separated with Alt + Enter.
    """
    text = normalize_text(value)

    if not text:
        return []

    locations = []

    for item in text.splitlines():
        item = item.strip()

        if item:
            locations.append(item)

    return locations


def count_locations(series):
    """Count all registered locations across a pandas Series."""
    if series is None:
        return 0

    total = 0

    for value in series:
        total += len(split_locations(value))

    return total


def status_symbol(value):
    """
    Convert availability status into a compact symbol.

    ● = Available / Yes
    ◐ = Pending
    ○ = Missing / No / empty
    """
    value = normalize_text(value).lower()

    if value in {"available", "yes", "y", "true"}:
        return "●"

    if value in {"pending", "in progress"}:
        return "◐"

    return "○"


def availability_status(value):
    """Normalize status text for the Data Locations cards."""
    value = normalize_text(value).lower()

    if value in {"available", "yes", "y", "true"}:
        return "Available"

    if value in {"pending", "in progress"}:
        return "Pending"

    return "Missing"


def get_location_count(df, column):
    """Safely count locations from a dataframe column."""
    if column not in df.columns:
        return 0

    return count_locations(df[column])


def render_location_list(locations):
    """Display individual locations in a readable format."""
    for index, location in enumerate(locations, start=1):
        st.markdown(f"**Location {index}**")

        # Make web URLs clickable.
        if location.lower().startswith(("http://", "https://")):
            st.markdown(f"[Open location ↗]({location})")
            st.code(location, language=None)

        # Domino/file-system paths are displayed as code.
        else:
            st.code(location, language=None)


def render_location_asset(
    title,
    status,
    locations,
):
    """Render one asset/location block."""

    status_text = availability_status(status)
    number_locations = len(locations)

    if number_locations == 1:
        location_label = "1 location"
    else:
        location_label = f"{number_locations} locations"

    # -------------------------------------------------------------------------
    # Asset summary card
    # -------------------------------------------------------------------------

    st.markdown(
        f"""
        <div style="
            border: 1px solid rgba(128,128,128,0.25);
            border-radius: 12px;
            padding: 14px 16px;
            margin-bottom: 8px;
        ">
            <div style="
                display:flex;
                justify-content:space-between;
                align-items:center;
            ">
                <div>
                    <div style="
                        font-weight:700;
                        font-size:15px;
                    ">
                        {title}
                    </div>

                    <div style="
                        font-size:12px;
                        opacity:0.70;
                        margin-top:5px;
                    ">
                        {location_label}
                    </div>
                </div>

                <div style="
                    font-size:12px;
                    font-weight:700;
                ">
                    {status_text}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -------------------------------------------------------------------------
    # Location details
    # -------------------------------------------------------------------------

    if locations:

        if number_locations == 1:
            expander_label = f"View 1 {title.lower()} location"
        else:
            expander_label = (
                f"View {number_locations} {title.lower()} locations"
            )

        with st.expander(expander_label):
            render_location_list(locations)

    else:
        st.caption("No location registered.")


# =============================================================================
# AVAILABILITY MATRIX
# =============================================================================

def build_availability_matrix(df):
    """
    Create a compact study-level availability matrix.

    Locations are intentionally excluded because they are displayed separately
    in the Data Locations section.
    """

    if df.empty:
        return pd.DataFrame()

    matrix = pd.DataFrame()

    if "Study ID" in df.columns:
        matrix["Study ID"] = df["Study ID"]

    if "Study Name" in df.columns:
        matrix["Study"] = df["Study Name"]

    for source_column, display_name in STATUS_COLUMNS.items():
        if source_column in df.columns:
            matrix[display_name] = df[source_column].apply(status_symbol)

    # Keep one logical row per study.
    subset = [
        column
        for column in ["Study ID", "Study"]
        if column in matrix.columns
    ]

    if subset:
        matrix = matrix.drop_duplicates(subset=subset)

    return matrix


# =============================================================================
# MAIN VIEW
# =============================================================================

def render(filtered, data):

    # -------------------------------------------------------------------------
    # DATA
    # -------------------------------------------------------------------------

    df = filtered.get(
        "02_DATA_AVAILABILITY",
        pd.DataFrame(),
    ).copy()

    # -------------------------------------------------------------------------
    # HEADER
    # -------------------------------------------------------------------------

    st.header("Data Availability")

    st.markdown(
        """
        <div class="section-note">
            Study-level availability across clinical source data, SDTM/ADaM,
            analysis-ready datasets, annotations, clinical ground truth and
            feature vectors.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df.empty:
        st.info("No data availability information found for the current filters.")
        return

    # -------------------------------------------------------------------------
    # KPI COUNTS
    # -------------------------------------------------------------------------

    study_count = (
        df["Study ID"].nunique()
        if "Study ID" in df.columns
        else 0
    )

    sdtm_locations = get_location_count(
        df,
        "SDTM/ADaM Location",
    )

    ard_locations = get_location_count(
        df,
        "ARD Location",
    )

    annotation_locations = get_location_count(
        df,
        "Annotations Location",
    )

    clinical_gt_locations = get_location_count(
        df,
        "Clinical GT Location",
    )

    feature_vector_locations = get_location_count(
        df,
        "Feature Vectors Location",
    )

    # -------------------------------------------------------------------------
    # KPI CARDS
    # -------------------------------------------------------------------------

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    c1.metric(
        "Studies",
        study_count,
    )

    c2.metric(
        "SDTM/ADaM Assets",
        sdtm_locations,
    )

    c3.metric(
        "ARD Assets",
        ard_locations,
    )

    c4.metric(
        "Annotations",
        annotation_locations,
    )

    c5.metric(
        "Clinical GT",
        clinical_gt_locations,
    )

    c6.metric(
        "Feature Vectors",
        feature_vector_locations,
    )

    # -------------------------------------------------------------------------
    # AVAILABILITY MATRIX
    # -------------------------------------------------------------------------

    st.markdown("### Availability Matrix")

    st.markdown(
        """
        <div class="section-note">
            Study-level overview of available data assets.
            ● Available &nbsp;&nbsp; ○ Missing / No &nbsp;&nbsp; ◐ Pending
        </div>
        """,
        unsafe_allow_html=True,
    )

    matrix = build_availability_matrix(df)

    if not matrix.empty:
        st.dataframe(
            matrix,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No availability information available.")

    # -------------------------------------------------------------------------
    # DATA LOCATIONS
    # -------------------------------------------------------------------------

    st.markdown("---")
    st.markdown("### Data Locations")

    st.markdown(
        """
        <div class="section-note">
            Detailed storage locations are shown when a single study is
            selected from the sidebar.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Determine how many studies remain after filtering.
    if "Study ID" not in df.columns:
        st.info("Study ID is required to display data locations.")
        return

    study_ids = (
        df["Study ID"]
        .dropna()
        .astype(str)
        .unique()
    )

    # -------------------------------------------------------------------------
    # Only show detailed locations for one selected study
    # -------------------------------------------------------------------------

    if len(study_ids) != 1:
        st.info(
            "Select a single study from the sidebar to view its data locations."
        )
        return

    study_df = df[
        df["Study ID"].astype(str) == study_ids[0]
    ].copy()

    row = study_df.iloc[0]

    study_id = normalize_text(
        row.get("Study ID", "")
    )

    study_name = normalize_text(
        row.get("Study Name", "")
    )

    # -------------------------------------------------------------------------
    # Study heading
    # -------------------------------------------------------------------------

    if study_name:
        st.markdown(f"### {study_name}")

    if study_id:
        st.caption(study_id)

    # -------------------------------------------------------------------------
    # SDTM / ADaM
    # -------------------------------------------------------------------------

    sdtm_locations_list = []

    if "SDTM/ADaM Location" in study_df.columns:
        for value in study_df["SDTM/ADaM Location"]:
            sdtm_locations_list.extend(split_locations(value))

    # Determine SDTM status from Med.ai / Domino.
    sdtm_status = "Missing"

    medai_status = availability_status(
        row.get("SDTM/ADaM (Med.ai)", "")
    )

    domino_status = availability_status(
        row.get("SDTM/ADaM (Domino)", "")
    )

    if (
        medai_status == "Available"
        or domino_status == "Available"
        or sdtm_locations_list
    ):
        sdtm_status = "Available"

    elif (
        medai_status == "Pending"
        or domino_status == "Pending"
    ):
        sdtm_status = "Pending"

    render_location_asset(
        "SDTM/ADaM",
        sdtm_status,
        sdtm_locations_list,
    )

    # -------------------------------------------------------------------------
    # ARD
    # -------------------------------------------------------------------------

    ard_locations_list = []

    if "ARD Location" in study_df.columns:
        for value in study_df["ARD Location"]:
            ard_locations_list.extend(split_locations(value))

    render_location_asset(
        "ARD",
        row.get(
            "Analysis-Ready-Dataset (ARD)",
            "",
        ),
        ard_locations_list,
    )

    # -------------------------------------------------------------------------
    # ANNOTATIONS
    # -------------------------------------------------------------------------

    annotation_locations_list = []

    if "Annotations Location" in study_df.columns:
        for value in study_df["Annotations Location"]:
            annotation_locations_list.extend(split_locations(value))

    render_location_asset(
        "Annotations",
        row.get("Annotations", ""),
        annotation_locations_list,
    )

    # -------------------------------------------------------------------------
    # CLINICAL GT
    # -------------------------------------------------------------------------

    clinical_gt_locations_list = []

    if "Clinical GT Location" in study_df.columns:
        for value in study_df["Clinical GT Location"]:
            clinical_gt_locations_list.extend(split_locations(value))

    render_location_asset(
        "Clinical GT",
        row.get("Clinical GT", ""),
        clinical_gt_locations_list,
    )

    # -------------------------------------------------------------------------
    # FEATURE VECTORS
    # -------------------------------------------------------------------------

    feature_vector_locations_list = []

    if "Feature Vectors Location" in study_df.columns:
        for value in study_df["Feature Vectors Location"]:
            feature_vector_locations_list.extend(split_locations(value))

    render_location_asset(
        "Feature Vectors",
        row.get("Feature Vectors", ""),
        feature_vector_locations_list,
    )
