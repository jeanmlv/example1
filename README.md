# example1

"""Render the ARGES Commons clinical data inventory dashboard."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
import re

import pandas as pd
import plotly.express as px
import streamlit as st


REQUIRED_SHEETS = [
    "01_STUDIES",
    "02_DATA_AVAILABILITY",
    "03_ASSETS",
    "04_PROCESSING",
    "05_DATA_SPLITS",
    "05A_DATA_SPLIT_DETAILS",
    "06_ARD",
    "06A_CD_VOI",
    "06B_UC_VOI",
    "06C_ARD_VARIABLES",
    "07_DATA_ANALYSIS",
    "08_EXTERNAL_ANALYSIS",
]
JNJ_RED = "#EB1700"
JNJ_DARK = "#262626"
BORDER = "#E6E8EC"
MUTED = "#667085"

st.markdown(
    f"""
    <style>
      .block-container {{padding-top:1.3rem; padding-bottom:3rem; max-width:1500px;}}
      h1,h2,h3 {{letter-spacing:-0.02em;}}
      h1 {{font-size:2rem !important;}}
      div[data-testid="stMetric"] {{background:#fff;border:1px solid {BORDER};border-radius:14px;padding:14px 16px;box-shadow:0 2px 10px rgba(16,24,40,.04);}}
      div[data-testid="stMetricLabel"] {{color:{MUTED};}}
      div[data-testid="stMetricValue"] {{color:{JNJ_DARK};}}
      .section-note {{color:{MUTED};font-size:13px;margin-top:-8px;margin-bottom:12px;}}
      .stButton>button, .stDownloadButton>button {{border-radius:10px;border:1px solid {BORDER};}}
      .stDownloadButton>button:hover {{border-color:{JNJ_RED};color:{JNJ_RED};}}
      div[data-baseweb="select"] > div {{border-radius:10px;}}
      hr {{border-color:{BORDER};}}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load_workbook(source: Path) -> dict[str, pd.DataFrame]:
    """Load all workbook sheets and normalize their column labels."""
    sheets = pd.read_excel(source, sheet_name=None, engine="openpyxl")
    normalized_sheets = {}
    for name, dataframe in sheets.items():
        dataframe = dataframe.copy()
        dataframe.columns = [
            re.sub(r"\s+", " ", str(column).replace("\n", " ")).strip()
            for column in dataframe.columns
        ]
        if "variable_of_interest" in dataframe.columns:
            dataframe["variable_of_interest"] = (
                dataframe["variable_of_interest"]
                .astype("string")
                .str.replace("[", "", regex=False)
                .str.replace("]", "", regex=False)
                .str.replace("'", "", regex=False)
                .str.replace(",", "", regex=False)
            )
        normalized_sheets[name] = dataframe.dropna(how="all")
    return normalized_sheets


def resolve_default_workbook() -> Path | None:
    """Find the workbook beside this page, then at the repository root."""
    page_directory = Path(__file__).resolve().parent
    repository_root = Path(__file__).resolve().parents[3]
    for directory in (page_directory, repository_root):
        preferred = directory / "ARGES_COMMONS.xlsx"
        if preferred.exists():
            return preferred
        candidates = sorted(directory.glob("ARGES_COMMONS*.xlsx"))
        if candidates:
            return candidates[0]
    return None


def clean_text_values(series: pd.Series) -> list[str]:
    """Return the non-empty string values in sorted order."""
    values = series.dropna().astype(str).str.strip()
    return sorted(values.loc[values.ne("")].unique().tolist())


def filter_by_study(dataframe: pd.DataFrame, study_ids: set[str]) -> pd.DataFrame:
    """Restrict assigned rows to selected studies while preserving unassigned rows."""
    if dataframe.empty or "Study ID" not in dataframe.columns:
        return dataframe.copy()
    if not study_ids:
        return dataframe.iloc[0:0].copy()
    study_id_values = dataframe["Study ID"].astype("string").str.strip()
    matches_selection = study_id_values.isin(study_ids)
    is_unassigned = study_id_values.isna() | study_id_values.eq("")
    return dataframe[matches_selection | is_unassigned].copy()


def dataframe_height(dataframe: pd.DataFrame, max_rows: int = 14) -> int:
    """Keep table heights usable while limiting long result sets."""
    return min(38 + 35 * (len(dataframe) + 1), 38 + 35 * (max_rows + 1))


def show_table(
    dataframe: pd.DataFrame,
    *,
    max_rows: int = 14,
    link_columns: list[str] | None = None,
) -> None:
    """Render a dataframe, configuring requested columns as links."""
    column_config = {}
    for column in link_columns or []:
        if column in dataframe.columns:
            column_config[column] = st.column_config.LinkColumn(
                column, display_text="Open 🔗"
            )
    st.dataframe(
        dataframe,
        use_container_width=True,
        hide_index=True,
        height=dataframe_height(dataframe, max_rows),
        column_config=column_config,
    )


def to_excel_bytes(frames: dict[str, pd.DataFrame]) -> bytes:
    """Serialize named dataframes into an Excel workbook."""
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for sheet_name, dataframe in frames.items():
            safe_name = re.sub(r"[\\/*?:\[\]]", "_", sheet_name)[:31]
            dataframe.to_excel(writer, sheet_name=safe_name, index=False)
    buffer.seek(0)
    return buffer.getvalue()


def download_row(
    dataframe: pd.DataFrame,
    stem: str,
    *,
    excel_frames: dict[str, pd.DataFrame] | None = None,
) -> None:
    """Display CSV and Excel exports for a dataframe."""
    csv_column, excel_column, _ = st.columns([1, 1, 5])
    with csv_column:
        st.download_button(
            "Download CSV",
            dataframe.to_csv(index=False).encode("utf-8-sig"),
            f"{stem}.csv",
            "text/csv",
            key=f"csv_{stem}",
            type="secondary",
        )
    with excel_column:
        frames = excel_frames or {stem[:31]: dataframe}
        st.download_button(
            "Download Excel",
            to_excel_bytes(frames),
            f"{stem}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"xlsx_{stem}",
            type="secondary",
        )


def donut_from_status(dataframe: pd.DataFrame, column: str, title: str) -> None:
    """Render a status distribution donut when values are available."""
    if column not in dataframe.columns or dataframe[column].dropna().empty:
        st.info(f"No data available for {title}.")
        return
    counts = dataframe[column].fillna("Not specified").astype(str).value_counts()
    chart_data = counts.rename_axis(column).reset_index(name="Count")
    figure = px.pie(
        chart_data,
        names=column,
        values="Count",
        hole=0.64,
        title=title,
        color_discrete_sequence=[
            JNJ_RED,
            "#F97066",
            "#FECACA",
            "#667085",
            "#98A2B3",
        ],
    )
    figure.update_traces(textposition="outside", textinfo="percent+label")
    figure.update_layout(height=350, legend_title_text="")
    st.plotly_chart(figure, use_container_width=True)


def render_filters(studies: pd.DataFrame) -> pd.DataFrame:
    """Render contextual study filters at the top of the Commons page."""
    st.subheader("Filters")
    eligible = studies.copy()
    study_column, phase_column, status_column, compound_column = st.columns(4)

    with study_column:
        selected_studies = st.multiselect(
            "Study", clean_text_values(eligible.get("Study Name", pd.Series(dtype=str)))
        )
    if selected_studies and "Study Name" in eligible:
        eligible = eligible[eligible["Study Name"].astype(str).isin(selected_studies)]

    with phase_column:
        phases = st.multiselect(
            "Phase", clean_text_values(eligible.get("Phase", pd.Series(dtype=str)))
        )
    if phases and "Phase" in eligible:
        eligible = eligible[eligible["Phase"].astype(str).isin(phases)]

    with status_column:
        statuses = st.multiselect(
            "Trial status",
            clean_text_values(eligible.get("Trial Status", pd.Series(dtype=str))),
        )
    if statuses and "Trial Status" in eligible:
        eligible = eligible[eligible["Trial Status"].astype(str).isin(statuses)]

    with compound_column:
        compounds = st.multiselect(
            "Compound",
            clean_text_values(eligible.get("Compound", pd.Series(dtype=str))),
        )
    if compounds and "Compound" in eligible:
        eligible = eligible[eligible["Compound"].astype(str).isin(compounds)]

    selected_count = eligible["Study ID"].nunique()
    total_count = studies["Study ID"].nunique()
    st.caption(f"{selected_count} of {total_count} studies selected")
    return eligible


def render_overview(filtered: dict[str, pd.DataFrame]) -> None:
    """Render the portfolio overview dashboard."""
    studies = filtered["01_STUDIES"]
    availability = filtered.get("02_DATA_AVAILABILITY", pd.DataFrame())
    ard = filtered.get("06_ARD", pd.DataFrame())
    metrics = st.columns(5)
    metrics[0].metric("Studies", studies["Study ID"].nunique())
    patients = pd.to_numeric(studies.get("Patients"), errors="coerce").sum()
    videos = pd.to_numeric(studies.get("Videos"), errors="coerce").sum()
    metrics[1].metric("Patients", f"{patients:,.0f}")
    metrics[2].metric("Videos", f"{videos:,.0f}")
    ard_available = 0
    ard_column = "Analysis-Ready-Dataset (ARD)"
    if ard_column in availability:
        ard_available = (
            availability[ard_column].astype(str).str.lower().eq("available").sum()
        )
    metrics[3].metric("ARD available", ard_available)
    coverage = pd.to_numeric(ard.get("Coverage %"), errors="coerce").mean()
    metrics[4].metric(
        "Mean ARD coverage", f"{coverage:.0%}" if pd.notna(coverage) else "-"
    )

    disease_column, status_column = st.columns(2)
    with disease_column:
        st.subheader("Portfolio by disease")
        if "Disease" in studies and not studies.empty:
            chart_data = studies["Disease"].fillna("Not specified").value_counts()
            chart_data = chart_data.rename_axis("Disease").reset_index(name="Studies")
            figure = px.bar(
                chart_data,
                x="Studies",
                y="Disease",
                orientation="h",
                text="Studies",
                color_discrete_sequence=[JNJ_RED],
            )
            figure.update_layout(yaxis_title="", showlegend=False)
            st.plotly_chart(figure, use_container_width=True)
        else:
            st.info("No study data for the current filters.")
    with status_column:
        st.subheader("Trial status")
        donut_from_status(studies, "Trial Status", "")


def render_page_content(
    filtered: dict[str, pd.DataFrame], data: dict[str, pd.DataFrame]
) -> None:
    """Render the Commons content corresponding to a selected tab."""
    page = st.session_state["arges_commons_active_tab"]
    if page == "Overview":
        render_overview(filtered)
    elif page == "Studies & Assets":
        st.header("Studies & Assets")
        st.markdown(
            '<div class="section-note">Study portfolio and the source assets registered for each study.</div>',
            unsafe_allow_html=True,
        )
        assets = filtered.get("03_ASSETS", pd.DataFrame())
        study_tab, asset_tab = st.tabs(["Studies", "Assets"])
        with study_tab:
            show_table(filtered["01_STUDIES"], link_columns=["ClinicalTrials Link"])
            download_row(filtered["01_STUDIES"], "filtered_studies")
        with asset_tab:
            show_table(assets)
            download_row(assets, "filtered_assets")
    elif page == "Data Availability":
        st.header("Data Availability")
        st.markdown(
            '<div class="section-note">Availability matrix across source data, SDTM/ADaM, ARD, annotations, clinical ground truth and feature vectors.</div>',
            unsafe_allow_html=True,
        )
        dataframe = filtered.get("02_DATA_AVAILABILITY", pd.DataFrame())
        show_table(dataframe, link_columns=["Clinical GT Location"])
        download_row(dataframe, "filtered_data_availability")
    elif page == "Processing":
        st.header("Processing")
        st.markdown(
            '<div class="section-note">Pipeline readiness from preprocessing and feature extraction through CMES inference and modeling.</div>',
            unsafe_allow_html=True,
        )
        dataframe = filtered.get("04_PROCESSING", pd.DataFrame())
        stages = [
            column
            for column in [
                "Preprocessing",
                "Feature Extraction",
                "CMES Inference",
                "Modeling",
            ]
            if column in dataframe.columns
        ]
        if stages and not dataframe.empty:
            identifiers = [
                column
                for column in ["Study ID", "Study Name"]
                if column in dataframe.columns
            ]
            chart_data = dataframe.melt(identifiers, stages, "Stage", "Status")
            chart_data["Status"] = chart_data["Status"].fillna("Not specified")
            summary = chart_data.groupby(["Stage", "Status"], as_index=False).size()
            figure = px.bar(
                summary, x="Stage", y="size", color="Status", barmode="stack"
            )
            st.plotly_chart(figure, use_container_width=True)
        show_table(dataframe)
        download_row(dataframe, "filtered_processing")
    elif page == "Data Splits":
        st.header("Data Splits")
        st.markdown(
            '<div class="section-note">Study-level split definitions with subject/video-level detail where available.</div>',
            unsafe_allow_html=True,
        )
        splits = filtered.get("05_DATA_SPLITS", pd.DataFrame())
        details = filtered.get("05A_DATA_SPLIT_DETAILS", pd.DataFrame())
        if not splits.empty and "Split Type" in splits:
            chart_data = (
                splits["Split Type"]
                .fillna("Not specified")
                .value_counts()
                .reset_index()
            )
            chart_data.columns = ["Split Type", "Records"]
            figure = px.bar(
                chart_data,
                x="Split Type",
                y="Records",
                text="Records",
                color_discrete_sequence=[JNJ_RED],
            )
            figure.update_layout(
                height=300,
                margin=dict(l=5, r=5, t=10, b=10),
                showlegend=False,
            )
            st.plotly_chart(figure, use_container_width=True)
        split_tab, detail_tab = st.tabs(["Split definitions", "Split details"])
        with split_tab:
            show_table(splits)
            download_row(splits, "filtered_data_splits")
        with detail_tab:
            show_table(details)
            download_row(details, "filtered_split_details")
    elif page == "ARD":
        st.header("Analysis-Ready Data (ARD)")
        st.markdown(
            '<div class="section-note">ARD inventory, variable-of-interest mapping coverage, and gap status by study.</div>',
            unsafe_allow_html=True,
        )
        dataframe = filtered.get("06_ARD", pd.DataFrame())
        if not dataframe.empty and {"Study Name", "Coverage %"}.issubset(
            dataframe.columns
        ):
            columns = ["Study Name", "Coverage %"]
            if "Coverage Level" in dataframe.columns:
                columns.append("Coverage Level")
            chart_data = dataframe[columns].copy()
            chart_data["Coverage %"] = pd.to_numeric(
                chart_data["Coverage %"], errors="coerce"
            )
            figure = px.bar(
                chart_data.dropna(subset=["Coverage %"]).sort_values("Coverage %"),
                x="Coverage %",
                y="Study Name",
                orientation="h",
                color="Coverage Level" if "Coverage Level" in chart_data else None,
                text_auto=".0%",
                color_discrete_map={
                    "High": "#12B76A",
                    "Medium": "#F79009",
                    "Low": "#D92D20",
                },
            )
            figure.update_xaxes(tickformat=".0%", range=[0, 1])
            figure.update_layout(
                height=max(330, 28 * len(chart_data)),
                margin=dict(l=5, r=5, t=15, b=10),
                yaxis_title="",
                legend_title_text="",
            )
            st.plotly_chart(figure, use_container_width=True)
        show_table(dataframe, link_columns=["Location"])
        download_row(dataframe, "filtered_ard")
    elif page == "Variable Definitions":
        st.header("Variable Definitions & Traceability")
        st.markdown(
            '<div class="section-note">Search variables of interest and trace their mapping into ARD variables across UC and CD studies.</div>',
            unsafe_allow_html=True,
        )
        mapping = filtered.get("06C_ARD_VARIABLES", pd.DataFrame())
        query = st.text_input(
            "Search variable", placeholder="e.g., CALPRO, MAYO, RHI, endoscopy..."
        )
        if query:
            searchable = [
                column
                for column in [
                    "Variable of Interest",
                    "Description",
                    "ARD Variable",
                    "ARD Description",
                ]
                if column in mapping.columns
            ]
            matches = pd.Series(False, index=mapping.index)
            for column in searchable:
                matches |= (
                    mapping[column]
                    .fillna("")
                    .astype(str)
                    .str.contains(query, case=False, regex=False)
                )
            mapping = mapping[matches]
        mapping_tab, cd_tab, uc_tab = st.tabs(
            [
                "ARD variable mapping",
                "CD variables of interest",
                "UC variables of interest",
            ]
        )
        with mapping_tab:
            show_table(mapping, max_rows=18)
            download_row(mapping, "filtered_ard_variables")
        with cd_tab:
            show_table(data.get("06A_CD_VOI", pd.DataFrame()), max_rows=18)
        with uc_tab:
            show_table(data.get("06B_UC_VOI", pd.DataFrame()), max_rows=18)
    elif page == "Data Analysis":
        st.header("Data Analysis")
        st.markdown(
            '<div class="section-note">Analysis registry linking ARD inputs, SAP references, code versions, owners, and outputs.</div>',
            unsafe_allow_html=True,
        )
        dataframe = filtered.get("07_DATA_ANALYSIS", pd.DataFrame())
        donut_from_status(dataframe, "Status", "Analysis status")
        show_table(
            dataframe,
            link_columns=["Dataset Location", "SAP Location", "Reports Location"],
        )
        download_row(dataframe, "filtered_data_analysis")
    else:
        st.header("External Data")
        st.markdown(
            '<div class="section-note">External datasets, access status, licensing, provenance, and intended use.</div>',
            unsafe_allow_html=True,
        )
        dataframe = data.get("08_EXTERNAL_ANALYSIS", pd.DataFrame()).copy()
        query = st.text_input(
            "Search external datasets",
            placeholder="dataset, domain, modality, provider...",
        )
        if query and not dataframe.empty:
            matches = pd.Series(False, index=dataframe.index)
            for column in dataframe.columns:
                matches |= (
                    dataframe[column]
                    .fillna("")
                    .astype(str)
                    .str.contains(query, case=False, regex=False)
                )
            dataframe = dataframe[matches]
        donut_from_status(dataframe, "Access Status", "External data access")
        show_table(dataframe, max_rows=16, link_columns=["License / Terms Link"])
        download_row(dataframe, "filtered_external_data")


def render_page(
    filtered: dict[str, pd.DataFrame], data: dict[str, pd.DataFrame]
) -> None:
    """Render the Commons navigation tabs and their associated content."""
    page_names = [
        "Overview",
        "Studies & Assets",
        "Data Availability",
        "Processing",
        "Data Splits",
        "ARD",
        "Variable Definitions",
        "Data Analysis",
        "External Data",
    ]
    tabs = st.tabs(page_names)
    for page_name, tab in zip(page_names, tabs):
        with tab:
            st.session_state["arges_commons_active_tab"] = page_name
            render_page_content(filtered, data)


def main() -> None:
    """Load the Commons workbook and render its filtered inventory views."""
    # st.markdown(
    #     '<div class="page-note">A study-centric view from source assets and processing through data splits, analysis-ready datasets, variable traceability, analyses, and external data.</div>',
    #     unsafe_allow_html=True,
    # )
    source = resolve_default_workbook()
    if source is None:
        st.error("ARGES_COMMONS.xlsx was not found at the repository root.")
        return
    try:
        data = load_workbook(source)
    except Exception as error:
        st.error(f"The workbook could not be loaded: {error}")
        return
    missing_sheets = [sheet for sheet in REQUIRED_SHEETS if sheet not in data]
    if missing_sheets:
        st.warning("Some expected sheets are not present: " + ", ".join(missing_sheets))
    studies = data.get("01_STUDIES", pd.DataFrame()).copy()
    if studies.empty or "Study ID" not in studies.columns:
        st.error("Sheet 01_STUDIES with a Study ID column is required.")
        return
    eligible = render_filters(studies)
    selected_ids = set(eligible["Study ID"].dropna().astype(str))
    filtered = {
        name: filter_by_study(dataframe, selected_ids)
        for name, dataframe in data.items()
    }
    filtered["01_STUDIES"] = eligible.copy()
    st.divider()
    render_page(filtered, data)

    st.caption(
        "ARGES Commons • Data shown reflects the selected workbook and active filters. Validate source metadata before operational or clinical use."
    )


main()
