"""External Data portfolio view for ARGES Commons."""

import pandas as pd
import plotly.express as px
import streamlit as st

from src.ui import show_table

SOURCE_SHEET = "08_EXTERNAL_ANALYSIS"
JNJ_RED = "#EB1700"
JNJ_CORAL = "#FF6B61"
JNJ_LIGHT_CORAL = "#FFB3AE"
JNJ_DARK_RED = "#A90F00"
JNJ_GRAY = "#667085"
JNJ_PALETTE = [JNJ_RED, JNJ_CORAL, JNJ_LIGHT_CORAL, JNJ_DARK_RED, JNJ_GRAY]

STATUS_COLORS = {
    "Available": JNJ_RED,
    "Pending": JNJ_CORAL,
    "Restricted": JNJ_DARK_RED,
    "Not available": JNJ_GRAY,
    "Unknown": JNJ_GRAY,
}


def _style_chart(fig, height):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=height,
        showlegend=False,
        margin=dict(l=5, r=35, t=10, b=15),
        xaxis_title="Datasets",
        yaxis_title="",
        font=dict(color="#F2F4F7"),
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(152,162,179,0.15)", zeroline=False)
    fig.update_yaxes(showgrid=False)
    return fig



def _normalize_status(value):
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "<na>", "n/a", "-"}:
        return "Unknown"
    return next((s for s in STATUS_COLORS if s.casefold() == text.casefold()), text)


def _unique_values(df, column):
    if column not in df:
        return []
    return sorted(df[column].dropna().astype(str).str.strip().loc[lambda s: s.ne("")].unique().tolist())


def _valid_link(value):
    return isinstance(value, str) and value.strip().lower().startswith(("https://", "http://"))


def render(filtered, data):
    st.header("External Data")
    st.markdown(
        '<div class="section-note">External dataset inventory, access readiness, '
        'provenance, licensing and intended analytical use.</div>',
        unsafe_allow_html=True,
    )

    # This sheet describes external sources, not necessarily a single clinical study.
    # Global study filters therefore do not automatically restrict this inventory.
    df = data.get(SOURCE_SHEET, pd.DataFrame()).copy()
    if df.empty:
        st.info("No external datasets are registered in 08_EXTERNAL_ANALYSIS.")
        return

    if "External Dataset ID" in df:
        df = df.loc[df["External Dataset ID"].notna()].copy()
        df = df.loc[df["External Dataset ID"].astype(str).str.strip().ne("")]

    if "Access Status" not in df:
        df["Access Status"] = "Unknown"
    df["Access Status"] = df["Access Status"].map(_normalize_status)

    demo_cols = [c for c in ["Dataset Name", "Dataset Description", "Notes"] if c in df]
    if demo_cols:
        demo = df[demo_cols].fillna("").astype(str).agg(" ".join, axis=1)
        if demo.str.contains(r"synthetic|fictitious|example for dashboard", case=False, regex=True).any():
            st.caption("Dataset registry includes demonstration/synthetic entries; verify sources and permissions before use.")

    st.subheader("External Data Portfolio")
    total = len(df)
    available = int(df["Access Status"].eq("Available").sum())
    pending = int(df["Access Status"].eq("Pending").sum())
    modalities = len(_unique_values(df, "Data Modality"))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Registered datasets", f"{total:,}", help="Datasets registered in the external analysis inventory.")
    c2.metric("Available", f"{available:,}", help="Datasets whose access status is marked Available; not a validation of licensing.")
    c3.metric("Pending access", f"{pending:,}", help="Datasets awaiting access according to the inventory.")
    c4.metric("Data modalities", f"{modalities:,}", help="Distinct non-empty modality labels; combined labels are counted as one category.")

    left, right = st.columns([1, 1])
    with left:
        st.markdown("#### Access Readiness")
        status_counts = df["Access Status"].value_counts().rename_axis("Status").reset_index(name="Datasets")
        fig = px.bar(
            status_counts, x="Datasets", y="Status", orientation="h",
            text="Datasets", color="Status", color_discrete_map=STATUS_COLORS,
        )
        fig.update_traces(textposition="outside", cliponaxis=False, hovertemplate="%{y}: %{x} datasets<extra></extra>")
        _style_chart(fig, max(220, 52 * len(status_counts) + 100))
        fig.update_xaxes(dtick=1, range=[0, max(status_counts["Datasets"].max() * 1.25, 1)])
        st.plotly_chart(fig, use_container_width=True, key="external_access_chart")
    with right:
        st.markdown("#### Data Modalities")
        if "Data Modality" in df and df["Data Modality"].notna().any():
            counts = df["Data Modality"].fillna("Unspecified").astype(str).value_counts().reset_index()
            counts.columns = ["Modality", "Datasets"]
            fig = px.bar(
                counts, x="Datasets", y="Modality", orientation="h",
                text="Datasets", color="Modality",
                color_discrete_sequence=JNJ_PALETTE,
            )
            fig.update_traces(textposition="outside", cliponaxis=False, hovertemplate="%{y}: %{x} datasets<extra></extra>")
            _style_chart(fig, max(220, 38 * len(counts) + 80))
            fig.update_xaxes(dtick=1, range=[0, max(counts["Datasets"].max() * 1.35, 1)])
            st.plotly_chart(fig, use_container_width=True, key="external_modality_chart")
        else:
            st.caption("No modality metadata available.")

    st.subheader("External Dataset Explorer")
    st.caption("Search and filter registered external sources; inspect provenance, access conditions and intended use.")
    q = st.text_input("Search datasets", placeholder="Dataset, disease, modality, provider, intended use...", key="external_search").strip()
    f1, f2, f3 = st.columns(3)
    with f1:
        statuses = st.multiselect("Access status", _unique_values(df, "Access Status"), key="external_status_filter")
    with f2:
        modality_filter = st.multiselect("Data modality", _unique_values(df, "Data Modality"), key="external_modality_filter")
    with f3:
        domains = st.multiselect("Disease / domain", _unique_values(df, "Disease / Domain"), key="external_domain_filter")

    view = df.copy()
    if statuses:
        view = view[view["Access Status"].isin(statuses)]
    if modality_filter and "Data Modality" in view:
        view = view[view["Data Modality"].isin(modality_filter)]
    if domains and "Disease / Domain" in view:
        view = view[view["Disease / Domain"].isin(domains)]
    if q:
        searchable = view.fillna("").astype(str)
        view = view[searchable.apply(lambda s: s.str.contains(q, case=False, regex=False)).any(axis=1)]

    st.caption(f"Showing {len(view):,} of {total:,} registered datasets.")
    if view.empty:
        st.info("No external datasets match the selected filters.")
        return

    main_columns = ["External Dataset ID", "Dataset Name", "Disease / Domain", "Data Modality",
                    "Provider / Organization", "Access Status", "License Type", "Used For"]
    detail_columns = ["External Dataset ID", "Dataset Name", "Dataset Description", "Source Type",
                      "External Source / Repository", "License Type", "License / Terms Link",
                      "Usage Restrictions", "Version", "Internal Location", "Access Status",
                      "Owner / Contact", "Used For", "Reference / Publication", "Notes"]
    tab1, tab2 = st.tabs(["Dataset Inventory", "Provenance & Access Details"])
    with tab1:
        show_table(view[[c for c in main_columns if c in view]], key="external_inventory_table", max_rows=100)
    with tab2:
        details = view[[c for c in detail_columns if c in view]].copy()
        link_cols = []
        if "License / Terms Link" in details and details["License / Terms Link"].dropna().map(_valid_link).all() and details["License / Terms Link"].notna().any():
            link_cols = ["License / Terms Link"]
        show_table(details, key="external_details_table", max_rows=100, link_cols=link_cols)
    st.caption("Access status is informational. Confirm source provenance, licensing, approved use and current access before analysis.")
