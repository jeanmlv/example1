# example1

import pandas as pd
import plotly.express as px
import streamlit as st

from src.ui import show_table


# ============================================================
# CONFIGURATION
# ============================================================

COLORS = {
    "Train": "#E2231A",
    "Validation": "#F79009",
    "Test": "#64748B",
    "Development": "#E2231A",
    "Internal Test": "#F79009",
    "Holdout": "#64748B",
}


# ============================================================
# HELPERS
# ============================================================

def clean(s):
    return (
        s.fillna("")
        .astype(str)
        .str.strip()
    )


def unique_count(df, col):

    if not {"Study ID", col}.issubset(df):
        return 0

    valid = (
        clean(df[col]).ne("")
        & clean(df["Study ID"]).ne("")
    )

    return len(
        df.loc[
            valid,
            ["Study ID", col],
        ].drop_duplicates()
    )


def scope(df, studies):

    if (
        df.empty
        or "Study Name" not in df
        or "Study Name" not in studies
    ):
        return df

    allowed = (
        clean(studies["Study Name"])
        .str.upper()
    )

    return df[
        clean(df["Study Name"])
        .str.upper()
        .isin(allowed)
    ].copy()


def chart(fig):

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(
            l=5,
            r=5,
            t=10,
            b=10,
        ),
        legend_title_text="",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


# ============================================================
# SPLIT INTEGRITY CHECKS
# ============================================================

def integrity(d):

    rows = []

    for (sid, name), g in d.groupby(
        ["Study ID", "Study Name"],
        dropna=False,
    ):

        # ----------------------------------------------------
        # IDENTIFIER OVERLAP ACROSS DATASET ROLES
        # ----------------------------------------------------

        checks = [
            (
                "Subject ID",
                "Subjects across dataset roles",
            ),
            (
                "Bag ID",
                "Bags across dataset roles",
            ),
            (
                "Video File Path",
                "Video paths across dataset roles",
            ),
        ]

        for col, label in checks:

            valid = g[
                clean(g[col]).ne("")
                & clean(g["Dataset Role"]).ne("")
            ]

            count = int(
                (
                    valid.groupby(col)[
                        "Dataset Role"
                    ].nunique() > 1
                ).sum()
            )

            if count:
                result = "Review"

            elif (
                len(valid)
                and valid[
                    "Dataset Role"
                ].nunique() > 1
            ):
                result = "No overlap detected"

            else:
                result = "Not evaluated"

            rows.append(
                [
                    name,
                    label,
                    count,
                    result,
                ]
            )

        # ----------------------------------------------------
        # DEVELOPMENT FOLD OVERLAP
        # ----------------------------------------------------

        dev = g[
            g["Dataset Role"].eq("Development")
            & clean(g["Subject ID"]).ne("")
            & g["CV Fold"].notna()
        ]

        count = int(
            (
                dev.groupby("Subject ID")[
                    "CV Fold"
                ].nunique() > 1
            ).sum()
        )

        if count:
            result = "Review"

        elif dev["CV Fold"].nunique() > 1:
            result = "No overlap detected"

        else:
            result = "Not evaluated"

        rows.append(
            [
                name,
                "Subjects assigned to multiple development folds",
                count,
                result,
            ]
        )

        # ----------------------------------------------------
        # MISSING IDENTIFIERS
        # ----------------------------------------------------

        for col in [
            "Subject ID",
            "Bag ID",
            "Video File Path",
            "Dataset Role",
            "CV Fold",
        ]:

            count = int(
                clean(g[col]).eq("").sum()
            )

            rows.append(
                [
                    name,
                    "Missing " + col,
                    count,
                    (
                        "Review"
                        if count
                        else "No missing values"
                    ),
                ]
            )

        # ----------------------------------------------------
        # DUPLICATE RECORDS
        # ----------------------------------------------------

        count = int(
            g.duplicated().sum()
        )

        rows.append(
            [
                name,
                "Exact duplicate detail rows",
                count,
                (
                    "Review"
                    if count
                    else "No duplicates detected"
                ),
            ]
        )

    return pd.DataFrame(
        rows,
        columns=[
            "Study",
            "Check",
            "Count",
            "Result",
        ],
    )


# ============================================================
# MAIN PAGE
# ============================================================

def render(filtered, data):

    st.header("Data Splits")

    st.caption(
        "Dataset partitioning, observed assignments "
        "and split integrity."
    )

    s = filtered.get(
        "05_DATA_SPLITS",
        pd.DataFrame(),
    ).copy()

    d = filtered.get(
        "05A_DATA_SPLIT_DETAILS",
        pd.DataFrame(),
    ).copy()

    # ========================================================
    # GLOBAL STUDY FILTERS
    # ========================================================

    # GALAXI split definitions may share a base Study ID.
    # Study Name is used to preserve study-level selection.

    studies = filtered.get(
        "01_STUDIES",
        pd.DataFrame(),
    )

    if "Study Name" in studies:

        s = scope(
            data.get(
                "05_DATA_SPLITS",
                s,
            ),
            studies,
        )

        d = scope(
            data.get(
                "05A_DATA_SPLIT_DETAILS",
                d,
            ),
            studies,
        )

    if s.empty and d.empty:

        st.info(
            "No split records in the selected scope."
        )

        return

    # ========================================================
    # DATASET OVERVIEW
    # ========================================================

    st.subheader("Dataset Overview")

    c = st.columns(4)

    labels = [
        "Split records",
        "Detail records",
        "Unique subjects",
        "Unique bags",
    ]

    values = [
        len(s),
        len(d),
        unique_count(
            d,
            "Subject ID",
        ),
        unique_count(
            d,
            "Bag ID",
        ),
    ]

    for col, label, val in zip(
        c,
        labels,
        values,
    ):
        col.metric(
            label,
            f"{val:,}",
        )

    st.caption(
        "Subjects and bags are counted within "
        "each Study ID. Bags are not necessarily "
        "individual video files."
    )

    # ========================================================
    # DATASET PARTITIONING
    # ========================================================

    st.subheader("Dataset Partitioning")

    if (
        not s.empty
        and {
            "Split Type",
            "Split %",
            "Study Name",
        }.issubset(s)
    ):

        # ----------------------------------------------------
        # TRAIN / VALIDATION / TEST
        # ----------------------------------------------------

        planned = s[
            s["Split Type"].isin(
                [
                    "Train",
                    "Validation",
                    "Test",
                ]
            )
        ].copy()

        planned["Percent"] = (
            pd.to_numeric(
                planned["Split %"],
                errors="coerce",
            ) * 100
        )

        if not planned.empty:

            st.caption(
                "Configured Train / Validation / Test "
                "proportions; not observed patient counts."
            )

            fig = px.bar(
                planned,
                x="Percent",
                y="Study Name",
                color="Split Type",
                orientation="h",
                barmode="stack",
                category_orders={
                    "Split Type": [
                        "Train",
                        "Validation",
                        "Test",
                    ]
                },
                color_discrete_map=COLORS,
                height=max(
                    300,
                    35 * planned[
                        "Study Name"
                    ].nunique() + 90,
                ),
            )

            chart(fig)

        # ----------------------------------------------------
        # CROSS-VALIDATION & HOLDOUT
        # ----------------------------------------------------

        cv = s[
            s["Split Type"].isin(
                [
                    "CV Fold",
                    "Test set",
                    "Holdout set",
                ]
            )
        ].copy()

        cv["Percent"] = (
            pd.to_numeric(
                cv["Split %"],
                errors="coerce",
            ) * 100
        )

        if not cv.empty:

            st.subheader(
                "Cross-validation & Holdout"
            )

            fig = px.bar(
                cv,
                x="Percent",
                y="Study Name",
                color="Split Label",
                orientation="h",
                barmode="stack",
                height=280,
            )

            chart(fig)

    # ========================================================
    # OBSERVED DATASET DISTRIBUTION
    # ========================================================

    required = {
        "Study ID",
        "Study Name",
        "Subject ID",
        "Bag ID",
        "Dataset Role",
        "CV Fold",
        "Video File Path",
        "Split Label",
    }

    if not d.empty and required.issubset(d):

        d["Dataset Role"] = (
            clean(d["Dataset Role"])
            .replace(
                {
                    "dev": "Development",
                    "int_test": "Internal Test",
                    "holdout": "Holdout",
                }
            )
        )

        st.subheader(
            "Observed Dataset Distribution"
        )

        st.caption(
            "Computed from detail records only; "
            "counts are unique within each study and role."
        )

        measure = st.radio(
            "Distribution measure",
            [
                "Subjects",
                "Bags",
                "Video paths",
            ],
            horizontal=True,
            key="split_measure",
        )

        col = {
            "Subjects": "Subject ID",
            "Bags": "Bag ID",
            "Video paths": "Video File Path",
        }[measure]

        x = (
            d[
                clean(d[col]).ne("")
            ]
            .groupby(
                [
                    "Study ID",
                    "Study Name",
                    "Dataset Role",
                ]
            )[col]
            .nunique()
            .reset_index(name="Count")
        )

        fig = px.bar(
            x,
            x="Study Name",
            y="Count",
            color="Dataset Role",
            barmode="group",
            text="Count",
            color_discrete_map=COLORS,
            height=330,
        )

        chart(fig)

        # ====================================================
        # SPLIT INTEGRITY
        # ====================================================

        st.subheader("Split Integrity")

        st.caption(
            "Checks use the complete detail records "
            "for the selected studies, before local "
            "explorer filters. Development folds are "
            "assignment groups, not training iterations. "
            "Results do not certify absence of leakage "
            "in the actual training pipeline."
        )

        checks = integrity(d)

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Studies evaluated",
            d["Study ID"].nunique(),
        )

        c2.metric(
            "Checks requiring review",
            int(
                checks["Result"]
                .eq("Review")
                .sum()
            ),
        )

        c3.metric(
            "Not evaluated",
            int(
                checks["Result"]
                .eq("Not evaluated")
                .sum()
            ),
        )

        show_table(
            checks,
            key="split_integrity",
        )

    else:

        st.info(
            "Split integrity not evaluated: "
            "required detail fields are unavailable "
            "in this scope."
        )

    # ========================================================
    # DATA SPLIT EXPLORER
    # ========================================================

    st.subheader("Data Split Explorer")

    q = st.text_input(
        "Search study, split or identifier",
        key="split_search",
    )

    types = (
        sorted(
            clean(s["Split Type"]).unique()
        )
        if "Split Type" in s
        else []
    )

    selected = st.multiselect(
        "Definition split type",
        types,
        key="split_types",
    )

    roles = (
        sorted(
            clean(d["Dataset Role"]).unique()
        )
        if "Dataset Role" in d
        else []
    )

    selected_roles = st.multiselect(
        "Detail dataset role",
        roles,
        key="split_roles",
    )

    # Local filters affect explorer tables only.
    # Integrity checks retain the full selected study scope.

    if selected:

        s = s[
            s["Split Type"].isin(
                selected
            )
        ]

    if selected_roles:

        d = d[
            d["Dataset Role"].isin(
                selected_roles
            )
        ]

    if q:

        s = s[
            s.fillna("")
            .astype(str)
            .apply(
                lambda c: c.str.contains(
                    q,
                    case=False,
                    regex=False,
                )
            )
            .any(axis=1)
        ]

        d = d[
            d.fillna("")
            .astype(str)
            .apply(
                lambda c: c.str.contains(
                    q,
                    case=False,
                    regex=False,
                )
            )
            .any(axis=1)
        ]

    # ========================================================
    # INVENTORY TABS
    # ========================================================

    t1, t2, t3 = st.tabs(
        [
            "Split definitions",
            "Split details",
            "Cross-validation",
        ]
    )

    # --------------------------------------------------------
    # TAB 1 - SPLIT DEFINITIONS
    # --------------------------------------------------------

    with t1:

        show_table(
            s,
            key="split_table",
        )

    # --------------------------------------------------------
    # TAB 2 - SPLIT DETAILS
    # --------------------------------------------------------

    with t2:

        show_table(
            d,
            key="split_details_table",
        )

    # --------------------------------------------------------
    # TAB 3 - CROSS-VALIDATION
    # --------------------------------------------------------

    with t3:

        if "Split Type" in s:

            cv_records = s[
                s["Split Type"].isin(
                    [
                        "CV Fold",
                        "Test set",
                        "Holdout set",
                    ]
                )
            ]

            show_table(
                cv_records,
                key="split_cv_table",
            )


