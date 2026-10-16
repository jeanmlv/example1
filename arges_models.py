"""ARGES Commons dashboard: model version inventory (09_ARGES_MODELS)."""

import pandas as pd
import plotly.express as px
import streamlit as st

from src.config import JNJ_RED

SHEET = "09_ARGES_MODELS"


def _clean(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def _status_group(value):
    status = _clean(value).lower()
    if "unreleased" in status or "not released" in status:
        return "Unreleased"
    if "released" in status:
        return "Released"
    return "Other / Not specified"


def render(filtered: dict[str, pd.DataFrame], data: dict[str, pd.DataFrame]) -> None:
    st.header("ARGES Models")
    st.markdown(
        '<div class="section-note">ARGES pipeline versions, release status, '
        'release notes, changes, and deployment references.</div>',
        unsafe_allow_html=True,
    )

    # Model versions are pipeline-level metadata, not study-level records.
    # Use the unfiltered workbook data so Study/Compound filters do not hide them.
    df = data.get(SHEET, pd.DataFrame()).copy()
    if df.empty:
        st.info("No ARGES model information is available in 09_ARGES_MODELS.")
        return

    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(how="all")
    if "Pipeline" not in df.columns or "version" not in df.columns:
        st.warning("The sheet must contain the 'Pipeline' and 'version' columns.")
        return

    df = df[df["Pipeline"].map(_clean).ne("")].copy()
    if df.empty:
        st.info("No model versions are registered.")
        return

    df["Pipeline"] = df["Pipeline"].map(_clean)
    df["version"] = df["version"].map(_clean)
    if "status" not in df:
        df["status"] = ""
    df["Release group"] = df["status"].map(_status_group)

    # Filters are independent of study-level filters.
    left, right = st.columns(2)
    with left:
        pipelines = st.multiselect(
            "Pipeline", sorted(df["Pipeline"].unique()), key="models_pipeline_filter"
        )
    with right:
        statuses = st.multiselect(
            "Release status", ["Released", "Unreleased", "Other / Not specified"],
            key="models_status_filter",
        )
    if pipelines:
        df = df[df["Pipeline"].isin(pipelines)]
    if statuses:
        df = df[df["Release group"].isin(statuses)]

    if df.empty:
        st.info("No versions match the selected filters.")
        return

    a, b, c, d = st.columns(4)
    a.metric("Model records", f"{len(df):,}")
    b.metric("Pipelines", f"{df['Pipeline'].nunique():,}")
    c.metric("Released records", f"{df['Release group'].eq('Released').sum():,}")
    d.metric("Unreleased records", f"{df['Release group'].eq('Unreleased').sum():,}")

    left, right = st.columns(2, gap="large")
    with left:
        st.markdown("### Versions by pipeline")
        counts = df.groupby("Pipeline", as_index=False).size().rename(columns={"size": "Versions"})
        fig = px.bar(counts.sort_values("Versions"), x="Versions", y="Pipeline", orientation="h", text="Versions")
        fig.update_traces(marker_color=JNJ_RED)
        fig.update_layout(height=max(300, 55 * len(counts)), margin=dict(l=5, r=10, t=15, b=10), yaxis_title="", showlegend=False)
        st.plotly_chart(fig, width="stretch")
    with right:
        st.markdown("### Release status")
        counts = df["Release group"].value_counts().rename_axis("Status").reset_index(name="Records")
        fig = px.pie(counts, names="Status", values="Records", hole=0.6,
                     color="Status", color_discrete_map={"Released": JNJ_RED, "Unreleased": "#F97066", "Other / Not specified": "#667085"})
        fig.update_layout(height=300, margin=dict(l=5, r=10, t=15, b=10), legend_title_text="")
        st.plotly_chart(fig, width="stretch")

    st.markdown("### Model version inventory")
    preferred = ["Pipeline", "version", "status", "Release notes", "Key changes to previous version", "Key deployments", "FE", "MAP", "CMES", "MES", "UCEIS"]
    columns = [c for c in preferred if c in df.columns]
    columns += [c for c in df.columns if c not in columns and c != "Release group"]
    st.dataframe(df[columns].reset_index(drop=True), width="stretch", hide_index=True,
                 column_config={"Release notes": st.column_config.TextColumn(width="large"),
                                "Key changes to previous version": st.column_config.TextColumn(width="large"),
                                "Key deployments": st.column_config.TextColumn(width="medium")})
    st.caption("Each spreadsheet row is retained as a separate model record, including repeated version numbers.")
