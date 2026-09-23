from __future__ import annotations

from io import BytesIO
from pathlib import Path
import re

import pandas as pd
import streamlit as st


# Matches examples such as:
# ADEF_SAS7BDAT_PARAMCD_MAYO_AVAL
# ADEF_SAS7BDAT_PARAMCD_CLINRSP_AVALC
PARAMCD_PATTERN = re.compile(
    r"^(?P<source>.+?)_PARAMCD_(?P<variable>.+?)_(?P<value_type>AVALC|AVAL)$",
    flags=re.IGNORECASE,
)

ARD_SEARCH_DIRS = (
    Path("ard_data"),
    Path("data") / "ard",
    Path("data") / "ards",
    Path("."),
)


@st.cache_data(show_spinner=False)
def load_ard_csv(path: str) -> pd.DataFrame:
    """Load an ARD CSV from disk."""
    return pd.read_csv(path, low_memory=False)


@st.cache_data(show_spinner=False)
def load_uploaded_ard(file_bytes: bytes) -> pd.DataFrame:
    """Load an ARD CSV uploaded through Streamlit."""
    return pd.read_csv(BytesIO(file_bytes), low_memory=False)


def discover_ard_files() -> list[Path]:
    """Find local ARD CSV files in the supported project folders."""
    found: list[Path] = []

    for directory in ARD_SEARCH_DIRS:
        if not directory.exists() or not directory.is_dir():
            continue

        for path in directory.glob("*.csv"):
            # Avoid accidentally treating generic CSV exports as ARDs.
            if directory == Path(".") and "ard" not in path.name.lower():
                continue
            found.append(path.resolve())

    return sorted(set(found), key=lambda p: p.name.lower())


def extract_study_id_from_filename(filename: str, study_ids=None) -> str | None:
    """
    Match a known Study ID against the ARD filename.
    Longest IDs are checked first to avoid partial matches.
    """
    if not study_ids:
        return None

    upper_name = filename.upper()
    candidates = sorted(
        [str(x).strip() for x in study_ids if pd.notna(x) and str(x).strip()],
        key=len,
        reverse=True,
    )

    for study_id in candidates:
        if study_id.upper() in upper_name:
            return study_id

    return None


def get_available_variables(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse PARAMCD value columns.

    Returns one row per detected value column with:
    Variable, Source, Value Type, Column.
    """
    records = []

    for column in df.columns:
        match = PARAMCD_PATTERN.match(str(column))
        if not match:
            continue

        records.append(
            {
                "Variable": match.group("variable").upper(),
                "Source": match.group("source"),
                "Value Type": match.group("value_type").upper(),
                "Column": column,
            }
        )

    if not records:
        return pd.DataFrame(columns=["Variable", "Source", "Value Type", "Column"])

    variables = pd.DataFrame(records)

    # Prefer AVAL when the same PARAMCD has both AVAL and AVALC,
    # but preserve both options for cases where they carry different information.
    variables["_type_order"] = variables["Value Type"].map({"AVAL": 0, "AVALC": 1}).fillna(9)
    variables = (
        variables.sort_values(["Variable", "_type_order", "Source", "Column"])
        .drop(columns="_type_order")
        .reset_index(drop=True)
    )

    return variables


def variable_option_label(row: pd.Series, duplicated_variables: set[str]) -> str:
    """Create a readable selectbox label while disambiguating duplicates."""
    variable = str(row["Variable"])
    if variable not in duplicated_variables:
        return variable
    return f"{variable} · {row['Value Type']} · {row['Source']}"


def prepare_variable_data(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """
    Return a normalized long-like frame for one selected PARAMCD column.

    Output fields:
      USUBJID, AVISIT, AVISITN, AVISIT_ORDER, VALUE
    Missing source columns are created as NA.
    """
    wanted = ["USUBJID", "AVISIT", "AVISITN", "AVISIT_ORDER"]
    out = pd.DataFrame(index=df.index)

    for col in wanted:
        out[col] = df[col] if col in df.columns else pd.NA

    out["VALUE"] = df[column]
    return out


def ordered_visits(variable_df: pd.DataFrame) -> list[str]:
    """Return visit labels in clinical order when an ordering variable exists."""
    if "AVISIT" not in variable_df.columns:
        return []

    work = variable_df.loc[variable_df["AVISIT"].notna()].copy()
    if work.empty:
        return []

    work["AVISIT"] = work["AVISIT"].astype(str)

    for order_col in ("AVISIT_ORDER", "AVISITN"):
        if order_col in work.columns:
            order = pd.to_numeric(work[order_col], errors="coerce")
            if order.notna().any():
                work["_order"] = order
                return (
                    work[["AVISIT", "_order"]]
                    .groupby("AVISIT", as_index=False)["_order"]
                    .min()
                    .sort_values(["_order", "AVISIT"])["AVISIT"]
                    .tolist()
                )

    return sorted(work["AVISIT"].dropna().unique().tolist())


def numeric_values(series: pd.Series) -> pd.Series:
    """Coerce an AVAL series to numeric and remove missing values."""
    return pd.to_numeric(series, errors="coerce").dropna()
