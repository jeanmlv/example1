"""ARGES Commons — Streamlit clinical data inventory dashboard.
Run: streamlit run arges_commons_dashboard.py
Dependencies: streamlit pandas plotly openpyxl
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import html
import re

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# -----------------------------------------------------------------------------
# App configuration
# -----------------------------------------------------------------------------
st.set_page_config(page_title="ARGES Commons", page_icon="🧬", layout="wide", initial_sidebar_state="expanded")

JNJ_RED = "#EB1700"
JNJ_DARK = "#262626"
SOFT_RED = "#FFF2F0"
SOFT_GRAY = "#F6F7F9"
BORDER = "#E6E8EC"
MUTED = "#667085"

st.markdown(
    f"""
    <style>
      .stApp {{background:#FFFFFF; color:{JNJ_DARK};}}
      .block-container {{padding-top:1.3rem; padding-bottom:3rem; max-width:1500px;}}
      [data-testid="stSidebar"] {{background:#FAFAFB; border-right:1px solid {BORDER};}}
      h1,h2,h3 {{letter-spacing:-0.02em;}}
      h1 {{font-size:2rem !important;}}
      div[data-testid="stMetric"] {{background:#fff;border:1px solid {BORDER};border-radius:14px;padding:14px 16px;box-shadow:0 2px 10px rgba(16,24,40,.04);}}
      div[data-testid="stMetricLabel"] {{color:{MUTED};}}
      div[data-testid="stMetricValue"] {{color:{JNJ_DARK};}}
      .brand {{display:flex;align-items:center;gap:14px;padding:4px 0 14px 0;}}
      .brand-mark {{font-family:Georgia,serif;font-size:29px;font-weight:700;color:{JNJ_RED};white-space:nowrap;}}
      .brand-divider {{height:30px;width:1px;background:{BORDER};}}
      .brand-sub {{font-size:15px;font-weight:700;color:{JNJ_DARK};}}
      .eyebrow {{font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:{JNJ_RED};font-weight:800;}}
      .hero {{padding:22px 24px;border:1px solid {BORDER};border-radius:18px;background:linear-gradient(135deg,#fff 0%,{SOFT_RED} 100%);margin-bottom:18px;}}
      .hero-title {{font-size:28px;font-weight:800;line-height:1.15;margin:5px 0 6px 0;}}
      .hero-copy {{color:{MUTED};font-size:14px;max-width:900px;}}
      .section-note {{color:{MUTED};font-size:13px;margin-top:-8px;margin-bottom:12px;}}
      .pill {{display:inline-block;padding:3px 9px;border-radius:999px;background:{SOFT_RED};color:#B42318;font-size:12px;font-weight:700;margin-right:5px;}}
      .stButton>button, .stDownloadButton>button {{border-radius:10px;border:1px solid {BORDER};}}
      .stDownloadButton>button:hover {{border-color:{JNJ_RED};color:{JNJ_RED};}}
      div[data-baseweb="select"] > div {{border-radius:10px;}}
      [data-testid="stDataFrame"] {{border:1px solid {BORDER};border-radius:12px;overflow:hidden;}}
      hr {{border-color:{BORDER};}}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Workbook loading / normalization
# -----------------------------------------------------------------------------
REQUIRED_SHEETS = [
    "01_STUDIES", "02_DATA_AVAILABILITY", "03_ASSETS", "04_PROCESSING",
    "05_DATA_SPLITS", "05A_DATA_SPLIT_DETAILS", "06_ARD", "06A_CD_VOI",
    "06B_UC_VOI", "06C_ARD_VARIABLES", "07_DATA_ANALYSIS", "08_EXTERNAL_ANALYSIS",
]

@st.cache_data(show_spinner=False)
def load_workbook(source) -> dict[str, pd.DataFrame]:
    """Load all workbook sheets and lightly normalize column labels."""
    sheets = pd.read_excel(source, sheet_name=None, engine="openpyxl")
    out = {}
    for name, df in sheets.items():
        df = df.copy()
        df.columns = [re.sub(r"\s+", " ", str(c).replace("\n", " ")).strip() for c in df.columns]
        df = df.dropna(how="all")
        out[name] = df
    return out


def resolve_default_workbook() -> Path | None:
    """Find ARGES_COMMONS.xlsx beside the script (or a similarly named copy)."""
    root = Path(__file__).resolve().parent
    preferred = root / "ARGES_COMMONS.xlsx"
    if preferred.exists():
        return preferred
    candidates = sorted(root.glob("ARGES_COMMONS*.xlsx"))
    return candidates[0] if candidates else None


def clean_text_values(series: pd.Series) -> list[str]:
    return sorted(series.dropna().astype(str).str.strip().loc[lambda s: s.ne("")].unique().tolist())


def filter_by_study(df: pd.DataFrame, study_ids: set[str]) -> pd.DataFrame:
    if df.empty or "Study ID" not in df.columns or not study_ids:
        return df.iloc[0:0].copy() if not study_ids and "Study ID" in df.columns else df.copy()
    return df[df["Study ID"].astype(str).isin(study_ids)].copy()


def status_color(value: object) -> str:
    v = str(value).strip().lower()
    if v in {"available", "complete", "completed", "approved", "mapped", "high"}:
        return "#12B76A"
    if v in {"pending", "medium", "in progress"}:
        return "#F79009"
    if v in {"missing", "not available", "not started", "low"}:
        return "#D92D20"
    return "#98A2B3"


def dataframe_height(df: pd.DataFrame, max_rows: int = 14) -> int:
    return min(38 + 35 * (len(df) + 1), 38 + 35 * (max_rows + 1))


def show_table(df: pd.DataFrame, *, key: str, max_rows: int = 14, link_cols: list[str] | None = None):
    """Consistent dataframe renderer with safe link-column support."""
    cfg = {}
    for col in link_cols or []:
        if col in df.columns:
            cfg[col] = st.column_config.LinkColumn(col, display_text="Open ↗")
    st.dataframe(df, use_container_width=True, hide_index=True, height=dataframe_height(df, max_rows), column_config=cfg, key=key)


def to_excel_bytes(frames: dict[str, pd.DataFrame]) -> bytes:
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        for sheet, df in frames.items():
            safe = re.sub(r"[\\/*?:\[\]]", "_", sheet)[:31]
            df.to_excel(writer, sheet_name=safe, index=False)
    bio.seek(0)
    return bio.getvalue()


def download_row(df: pd.DataFrame, stem: str, *, excel_frames: dict[str, pd.DataFrame] | None = None):
    c1, c2, spacer = st.columns([1, 1, 5])
    with c1:
        st.download_button("Download CSV", df.to_csv(index=False).encode("utf-8-sig"), f"{stem}.csv", "text/csv", key=f"csv_{stem}")
    with c2:
        frames = excel_frames or {stem[:31]: df}
        st.download_button("Download Excel", to_excel_bytes(frames), f"{stem}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"xlsx_{stem}")


def donut_from_status(df: pd.DataFrame, col: str, title: str):
    if col not in df.columns or df[col].dropna().empty:
        st.info(f"No data available for {title}.")
        return
    counts = df[col].fillna("Not specified").astype(str).value_counts().reset_index()
    counts.columns = [col, "Count"]
    fig = px.pie(counts, names=col, values="Count", hole=.64, title=title,
                 color_discrete_sequence=[JNJ_RED, "#F97066", "#FECACA", "#667085", "#98A2B3"])
    fig.update_traces(textposition="outside", textinfo="percent+label")
    fig.update_layout(height=350, margin=dict(l=10,r=10,t=55,b=10), legend_title_text="")
    st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------------------------
# Data source
# -----------------------------------------------------------------------------
default_file = resolve_default_workbook()
# Production/local mode: the workbook is loaded automatically from the same folder
# as this script. The upload control is intentionally hidden from the sidebar.
source = default_file
if source is None:
    st.error("ARGES_COMMONS.xlsx was not found. Place it beside this script or upload it from the sidebar.")
    st.stop()

try:
    data = load_workbook(source)
except Exception as exc:
    st.error(f"The workbook could not be loaded: {exc}")
    st.stop()

missing_sheets = [s for s in REQUIRED_SHEETS if s not in data]
if missing_sheets:
    st.warning("Some expected sheets are not present: " + ", ".join(missing_sheets))

# Safe accessors
getdf = lambda name: data.get(name, pd.DataFrame()).copy()
studies = getdf("01_STUDIES")
if studies.empty or "Study ID" not in studies.columns:
    st.error("Sheet 01_STUDIES with a Study ID column is required.")
    st.stop()

# -----------------------------------------------------------------------------
# Global filters — driven by the master study table
# -----------------------------------------------------------------------------
with st.sidebar:
    # Compact corporate brand retained above the filters.
    st.markdown(
        f'<div style="padding:10px 0 20px 0;">'
        f'<div style="font-family:Georgia,serif;font-size:24px;font-weight:700;color:{JNJ_RED};white-space:nowrap;">Johnson&amp;Johnson</div>'
        f'<div style="font-size:12px;color:{MUTED};margin-top:4px;">ARGES Commons • Clinical Data Inventory</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown("### Filters")

    # Requested order: Study → Phase → Trial status → Compound.
    # Each subsequent filter is populated from the rows that remain after the
    # preceding selections, keeping the controls contextual and intuitive.
    eligible = studies.copy()

    study_options = clean_text_values(eligible.get("Study Name", pd.Series(dtype=str)))
    selected_studies = st.multiselect("Study", study_options)
    if selected_studies and "Study Name" in eligible:
        eligible = eligible[eligible["Study Name"].astype(str).isin(selected_studies)]

    phases = st.multiselect("Phase", clean_text_values(eligible.get("Phase", pd.Series(dtype=str))))
    if phases and "Phase" in eligible:
        eligible = eligible[eligible["Phase"].astype(str).isin(phases)]

    statuses = st.multiselect("Trial status", clean_text_values(eligible.get("Trial Status", pd.Series(dtype=str))))
    if statuses and "Trial Status" in eligible:
        eligible = eligible[eligible["Trial Status"].astype(str).isin(statuses)]

    compounds = st.multiselect("Compound", clean_text_values(eligible.get("Compound", pd.Series(dtype=str))))
    if compounds and "Compound" in eligible:
        eligible = eligible[eligible["Compound"].astype(str).isin(compounds)]

    selected_ids = set(eligible["Study ID"].dropna().astype(str))

    st.markdown("---")
    st.caption(f"{len(selected_ids)} of {studies['Study ID'].nunique()} studies selected")

# -----------------------------------------------------------------------------
# Header and navigation
# -----------------------------------------------------------------------------
st.markdown(
    '<div class="hero"><div class="eyebrow">Clinical data inventory</div>'
    '<div class="hero-title">ARGES Commons Dashboard</div>'
    '<div class="hero-copy">A study-centric view from source assets and processing through data splits, analysis-ready datasets, variable traceability, analyses, and external data.</div></div>',
    unsafe_allow_html=True,
)

pages = ["Overview", "Studies & Assets", "Data Availability", "Processing", "Data Splits", "ARD", "Variable Definitions", "Data Analysis", "External Data"]
page = st.segmented_control("Navigation", pages, default="Overview", label_visibility="collapsed") or "Overview"

# Materialize globally filtered frames
filtered = {name: filter_by_study(df, selected_ids) for name, df in data.items()}
filtered["01_STUDIES"] = eligible.copy()

# -----------------------------------------------------------------------------
# Overview
# -----------------------------------------------------------------------------
if page == "Overview":
    s = filtered["01_STUDIES"]
    avail = filtered.get("02_DATA_AVAILABILITY", pd.DataFrame())
    ard = filtered.get("06_ARD", pd.DataFrame())
    splits = filtered.get("05_DATA_SPLITS", pd.DataFrame())

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Studies", s["Study ID"].nunique() if "Study ID" in s else 0)
    c2.metric("Patients", f"{pd.to_numeric(s.get('Patients'), errors='coerce').sum():,.0f}" if "Patients" in s else "—")
    c3.metric("Videos", f"{pd.to_numeric(s.get('Videos'), errors='coerce').sum():,.0f}" if "Videos" in s else "—")
    ard_available = 0
    if "Analysis-Ready-Dataset (ARD)" in avail:
        ard_available = avail["Analysis-Ready-Dataset (ARD)"].astype(str).str.lower().eq("available").sum()
    c4.metric("ARD available", ard_available)
    avg_cov = pd.to_numeric(ard.get("Coverage %"), errors="coerce").mean() if "Coverage %" in ard else float("nan")
    c5.metric("Mean ARD coverage", f"{avg_cov:.0%}" if pd.notna(avg_cov) else "—")

    left, right = st.columns([1, 1], gap="large")
    with left:
        st.markdown("### Portfolio by disease")
        if "Disease" in s and not s.empty:
            tmp = s["Disease"].fillna("Not specified").value_counts().reset_index(); tmp.columns=["Disease","Studies"]
            fig = px.bar(tmp, x="Studies", y="Disease", orientation="h", text="Studies", color_discrete_sequence=[JNJ_RED])
            fig.update_layout(height=330, margin=dict(l=5,r=10,t=15,b=10), yaxis_title="", xaxis_title="Studies", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No study data for the current filters.")
    with right:
        st.markdown("### Trial status")
        if "Trial Status" in s.columns and not s["Trial Status"].dropna().empty:
            counts = s["Trial Status"].fillna("Not specified").astype(str).value_counts().reset_index()
            counts.columns = ["Trial Status", "Count"]
            fig = px.pie(
                counts, names="Trial Status", values="Count", hole=.62,
                color_discrete_sequence=[JNJ_RED, "#F97066", "#FECACA", "#667085", "#98A2B3"]
            )
            # Keep labels inside the plot and reserve room for the legend so
            # long trial-status names are never clipped.
            fig.update_traces(textposition="inside", textinfo="percent", insidetextorientation="horizontal")
            fig.update_layout(
                height=330,
                margin=dict(l=5, r=10, t=15, b=10),
                legend=dict(orientation="v", yanchor="middle", y=.5, xanchor="left", x=1.02),
                legend_title_text=""
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No trial-status data for the current filters.")


# -----------------------------------------------------------------------------
# Studies & Assets
# -----------------------------------------------------------------------------
elif page == "Studies & Assets":
    st.header("Studies & Assets")
    st.markdown('<div class="section-note">Study portfolio and the source assets registered for each study.</div>', unsafe_allow_html=True)
    s = filtered["01_STUDIES"]
    assets = filtered.get("03_ASSETS", pd.DataFrame())
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Studies", s["Study ID"].nunique() if "Study ID" in s else 0)
    c2.metric("Assets", len(assets))
    c3.metric("Asset types", assets["Asset Type"].nunique() if "Asset Type" in assets else 0)
    c4.metric("Sources", assets["Source"].nunique() if "Source" in assets else 0)
    t1,t2 = st.tabs(["Studies", "Assets"])
    with t1:
        show_table(s, key="studies_table", link_cols=["ClinicalTrials Link"]); download_row(s,"filtered_studies")
    with t2:
        show_table(assets, key="assets_table"); download_row(assets,"filtered_assets")

# -----------------------------------------------------------------------------
# Data Availability
# -----------------------------------------------------------------------------
elif page == "Data Availability":
    st.header("Data Availability")
    st.markdown('<div class="section-note">Availability matrix across source data, SDTM/ADaM, ARD, annotations, clinical ground truth and feature vectors.</div>', unsafe_allow_html=True)
    df = filtered.get("02_DATA_AVAILABILITY", pd.DataFrame())
    status_cols = [c for c in ["Videos","SDTM/ADaM (Med.ai)","SDTM/ADaM (Domino)","Analysis-Ready-Dataset (ARD)","Symptom Data","QS","ADQS","Feature Vectors"] if c in df.columns]
    c1,c2,c3 = st.columns(3)
    c1.metric("Studies", df["Study ID"].nunique() if "Study ID" in df else 0)
    if status_cols:
        values = df[status_cols].astype(str).apply(lambda x: x.str.lower())
        c2.metric("Available cells", int(values.eq("available").sum().sum()))
        c3.metric("Pending cells", int(values.eq("pending").sum().sum()))
    show_table(df, key="availability_table", link_cols=["Clinical GT Location"])
    download_row(df,"filtered_data_availability")

# -----------------------------------------------------------------------------
# Processing
# -----------------------------------------------------------------------------
elif page == "Processing":
    st.header("Processing")
    st.markdown('<div class="section-note">Pipeline readiness from preprocessing and feature extraction through CMES inference and modeling.</div>', unsafe_allow_html=True)
    df = filtered.get("04_PROCESSING", pd.DataFrame())
    stages = [c for c in ["Preprocessing","Feature Extraction","CMES Inference","Modeling"] if c in df.columns]
    if stages and not df.empty:
        long = df.melt(id_vars=[c for c in ["Study ID","Study Name"] if c in df], value_vars=stages, var_name="Stage", value_name="Status")
        long["Status"] = long["Status"].fillna("Not specified")
        summary = long.groupby(["Stage","Status"], as_index=False).size().rename(columns={"size":"Studies"})
        fig = px.bar(summary, x="Stage", y="Studies", color="Status", barmode="stack",
                     color_discrete_map={"Complete":"#12B76A","Pending":"#F79009","Not Started":"#D92D20","Not specified":"#D0D5DD"})
        fig.update_layout(height=360, margin=dict(l=5,r=5,t=15,b=10), legend_title_text="")
        st.plotly_chart(fig, use_container_width=True)
    show_table(df, key="processing_table"); download_row(df,"filtered_processing")

# -----------------------------------------------------------------------------
# Data Splits
# -----------------------------------------------------------------------------
elif page == "Data Splits":
    st.header("Data Splits")
    st.markdown('<div class="section-note">Study-level split definitions with subject/video-level detail where available.</div>', unsafe_allow_html=True)
    splits = filtered.get("05_DATA_SPLITS", pd.DataFrame())
    details = filtered.get("05A_DATA_SPLIT_DETAILS", pd.DataFrame())
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Split records", len(splits)); c2.metric("Detail records", len(details))
    c3.metric("Subjects", details["Subject ID"].nunique() if "Subject ID" in details else 0)
    c4.metric("Videos / bags", details["Bag ID"].nunique() if "Bag ID" in details else 0)
    if not splits.empty and "Split Type" in splits:
        tmp=splits["Split Type"].fillna("Not specified").value_counts().reset_index(); tmp.columns=["Split Type","Records"]
        fig=px.bar(tmp,x="Split Type",y="Records",text="Records",color_discrete_sequence=[JNJ_RED]); fig.update_layout(height=300,margin=dict(l=5,r=5,t=10,b=10),showlegend=False)
        st.plotly_chart(fig,use_container_width=True)
    t1,t2=st.tabs(["Split definitions","Split details"])
    with t1: show_table(splits,key="split_table"); download_row(splits,"filtered_data_splits")
    with t2: show_table(details,key="split_details_table"); download_row(details,"filtered_split_details")

# -----------------------------------------------------------------------------
# ARD
# -----------------------------------------------------------------------------
elif page == "ARD":
    st.header("Analysis-Ready Data (ARD)")
    st.markdown('<div class="section-note">ARD inventory, variable-of-interest mapping coverage, and gap status by study.</div>', unsafe_allow_html=True)
    df=filtered.get("06_ARD",pd.DataFrame())
    c1,c2,c3,c4=st.columns(4)
    c1.metric("ARD records",len(df))
    mapped=pd.to_numeric(df.get("Mapped"),errors="coerce").sum() if "Mapped" in df else 0
    missing=pd.to_numeric(df.get("Missing"),errors="coerce").sum() if "Missing" in df else 0
    c2.metric("Mapped VOI",f"{mapped:,.0f}"); c3.metric("Missing VOI",f"{missing:,.0f}")
    avg=pd.to_numeric(df.get("Coverage %"),errors="coerce").mean() if "Coverage %" in df else float("nan")
    c4.metric("Mean coverage",f"{avg:.0%}" if pd.notna(avg) else "—")
    if not df.empty and {"Study Name","Coverage %"}.issubset(df):
        ch=df[["Study Name","Coverage %","Coverage Level"] if "Coverage Level" in df else ["Study Name","Coverage %"]].copy(); ch["Coverage %"]=pd.to_numeric(ch["Coverage %"],errors="coerce")
        fig=px.bar(ch.dropna(subset=["Coverage %"]).sort_values("Coverage %"),x="Coverage %",y="Study Name",orientation="h",color="Coverage Level" if "Coverage Level" in ch else None,text_auto=".0%",color_discrete_map={"High":"#12B76A","Medium":"#F79009","Low":"#D92D20"})
        fig.update_xaxes(tickformat=".0%",range=[0,1]); fig.update_layout(height=max(330,28*len(ch)),margin=dict(l=5,r=5,t=15,b=10),yaxis_title="",legend_title_text="")
        st.plotly_chart(fig,use_container_width=True)
    show_table(df,key="ard_table",link_cols=["Location"]); download_row(df,"filtered_ard")

# -----------------------------------------------------------------------------
# Variable definitions / traceability
# -----------------------------------------------------------------------------
elif page == "Variable Definitions":
    st.header("Variable Definitions & Traceability")
    st.markdown('<div class="section-note">Search variables of interest and trace their mapping into ARD variables across UC and CD studies.</div>', unsafe_allow_html=True)
    mapping=filtered.get("06C_ARD_VARIABLES",pd.DataFrame())
    cd=getdf("06A_CD_VOI"); uc=getdf("06B_UC_VOI")
    q=st.text_input("Search variable",placeholder="e.g., CALPRO, MAYO, RHI, endoscopy...")
    status_opts=clean_text_values(mapping.get("Status",pd.Series(dtype=str)))
    selected_var_status=st.multiselect("Mapping status",status_opts)
    view=mapping.copy()
    if q:
        searchable=[c for c in ["Variable of Interest","Description","ARD Variable","ARD Description"] if c in view]
        if searchable:
            mask=pd.Series(False,index=view.index)
            for c in searchable: mask |= view[c].fillna("").astype(str).str.contains(q,case=False,regex=False)
            view=view[mask]
    if selected_var_status and "Status" in view: view=view[view["Status"].astype(str).isin(selected_var_status)]
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Mapping rows",len(view)); c2.metric("VOI",view["Variable of Interest"].nunique() if "Variable of Interest" in view else 0)
    c3.metric("Mapped",view["Status"].astype(str).str.lower().eq("mapped").sum() if "Status" in view else 0)
    c4.metric("Studies",view["Study Name"].nunique() if "Study Name" in view else 0)
    t1,t2,t3=st.tabs(["ARD variable mapping","CD variables of interest","UC variables of interest"])
    with t1: show_table(view,key="variable_mapping_table",max_rows=18); download_row(view,"filtered_ard_variables")
    with t2: show_table(cd,key="cd_voi_table",max_rows=18)
    with t3: show_table(uc,key="uc_voi_table",max_rows=18)

# -----------------------------------------------------------------------------
# Data analysis
# -----------------------------------------------------------------------------
elif page == "Data Analysis":
    st.header("Data Analysis")
    st.markdown('<div class="section-note">Analysis registry linking ARD inputs, SAP references, code versions, owners, and outputs.</div>', unsafe_allow_html=True)
    df=filtered.get("07_DATA_ANALYSIS",pd.DataFrame())
    c1,c2,c3=st.columns(3); c1.metric("Analyses",len(df)); c2.metric("Studies",df["Study ID"].nunique() if "Study ID" in df else 0); c3.metric("Owners",df["Analysis Owner"].nunique() if "Analysis Owner" in df else 0)
    donut_from_status(df,"Status","Analysis status")
    show_table(df,key="analysis_table",link_cols=["Dataset Location","SAP Location","Reports Location"]); download_row(df,"filtered_data_analysis")

# -----------------------------------------------------------------------------
# External data
# -----------------------------------------------------------------------------
elif page == "External Data":
    st.header("External Data")
    st.markdown('<div class="section-note">External datasets, access status, licensing, provenance, and intended use.</div>', unsafe_allow_html=True)
    df=getdf("08_EXTERNAL_ANALYSIS")
    q=st.text_input("Search external datasets",placeholder="dataset, domain, modality, provider...")
    if q and not df.empty:
        mask=pd.Series(False,index=df.index)
        for c in df.columns: mask |= df[c].fillna("").astype(str).str.contains(q,case=False,regex=False)
        df=df[mask]
    c1,c2,c3=st.columns(3); c1.metric("External datasets",len(df)); c2.metric("Available",df["Access Status"].astype(str).str.lower().eq("available").sum() if "Access Status" in df else 0); c3.metric("Modalities",df["Data Modality"].nunique() if "Data Modality" in df else 0)
    donut_from_status(df,"Access Status","External data access")
    show_table(df,key="external_table",max_rows=16,link_cols=["License / Terms Link"]); download_row(df,"filtered_external_data")

st.markdown("---")
st.caption("ARGES Commons • Data shown reflects the selected workbook and active filters. Validate source metadata before operational or clinical use.")
