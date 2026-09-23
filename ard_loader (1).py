from __future__ import annotations

from io import BytesIO

import re
from pathlib import Path
from typing import Iterable

import pandas as pd
import streamlit as st

# Expected ARD naming convention, for example:
# ADEF_SAS7BDAT_PARAMCD_MAYO_AVAL
# ADEF_SAS7BDAT_PARAMCD_CLINRSP_AVALC
PARAMCD_PATTERN = re.compile(
    r"^(?P<source>.+?)_PARAMCD_(?P<parameter>.+?)_(?P<value_type>AVALC|AVAL)$",
    flags=re.IGNORECASE,
)

# Locations searched automatically. Keeping ARDs outside the repository is fine;
# these folders are only local/runtime conventions.
DEFAULT_ARD_DIRS = (
    Path("ard_data"),
    Path("data") / "ard",
    Path("data") / "ards",
    Path("."),
)


def discover_ard_files(search_dirs: Iterable[Path] = DEFAULT_ARD_DIRS) -> list[Path]:
    """Return unique CSV ARD files found in the supported local locations."""
    files: list[Path] = []
    seen: set[str] = set()

    for directory in search_dirs:
        directory = Path(directory)
        if not directory.exists() or not directory.is_dir():
            continue

        # Root is intentionally non-recursive; dedicated ARD folders are recursive.
        candidates = directory.glob("*.csv") if directory == Path(".") else directory.rglob("*.csv")
        for path in candidates:
            resolved = str(path.resolve())
            if resolved not in seen:
                seen.add(resolved)
                files.append(path)

    return sorted(files, key=lambda p: p.name.lower())


def study_id_from_filename(path: str | Path, study_ids: Iterable[str]) -> str | None:
    """Match a workbook Study ID to an ARD filename when the ID is embedded in it."""
    name = Path(path).name.upper()
    matches = [str(s) for s in study_ids if str(s).strip() and str(s).upper() in name]
    return max(matches, key=len) if matches else None


def filter_ard_files_for_studies(files: Iterable[Path], study_ids: Iterable[str]) -> list[Path]:
    """Prefer ARDs matching the currently filtered studies; fall back to all files."""
    files = list(files)
    ids = [str(x) for x in study_ids if pd.notna(x)]
    if not ids:
        return files
    matched = [p for p in files if study_id_from_filename(p, ids)]
    return matched or files


@st.cache_data(show_spinner=False)
def load_ard(path: str) -> pd.DataFrame:
    """Load an ARD CSV with Streamlit caching."""
    return pd.read_csv(path, low_memory=False)



@st.cache_data(show_spinner=False)
def load_uploaded_ard(file_bytes: bytes) -> pd.DataFrame:
    """Load an ARD CSV uploaded through Streamlit."""
    return pd.read_csv(BytesIO(file_bytes), low_memory=False)


@st.cache_data(show_spinner=False)
def variable_catalog(columns: tuple[str, ...]) -> pd.DataFrame:
    """Parse PARAMCD_*_AVAL / PARAMCD_*_AVALC columns into a clean catalog."""
    rows = []
    for column in columns:
        match = PARAMCD_PATTERN.match(str(column))
        if not match:
            continue
        info = match.groupdict()
        rows.append(
            {
                "Variable": info["parameter"],
                "Source": info["source"],
                "Value Type": info["value_type"].upper(),
                "Column": column,
            }
        )

    catalog = pd.DataFrame(rows)
    if catalog.empty:
        return pd.DataFrame(columns=["Variable", "Source", "Value Type", "Column", "Label"])

    # A PARAMCD can theoretically exist in more than one source/type, so the UI label
    # remains unambiguous without exposing the full technical column name.
    duplicate_param = catalog["Variable"].duplicated(keep=False)
    catalog["Label"] = catalog["Variable"]
    catalog.loc[duplicate_param, "Label"] = (
        catalog.loc[duplicate_param, "Variable"]
        + " · "
        + catalog.loc[duplicate_param, "Source"]
        + " · "
        + catalog.loc[duplicate_param, "Value Type"]
    )
    return catalog.sort_values(["Variable", "Source", "Value Type"], kind="stable").reset_index(drop=True)


def prepare_variable_data(ard: pd.DataFrame, value_column: str, value_type: str) -> tuple[pd.DataFrame, str]:
    """Return subject/visit/value data and detected display kind (numeric/categorical)."""
    keep = [c for c in ["USUBJID", "AVISIT", "AVISITN", "AVISIT_ORDER", value_column] if c in ard.columns]
    out = ard[keep].copy()
    out = out.rename(columns={value_column: "VALUE"})

    if str(value_type).upper() == "AVAL":
        numeric = pd.to_numeric(out["VALUE"], errors="coerce")
        # AVAL should be numeric; only keep numeric values for quantitative plots.
        out["VALUE"] = numeric
        kind = "numeric"
    else:
        out["VALUE"] = out["VALUE"].astype("string")
        kind = "categorical"

    out = out[out["VALUE"].notna()].copy()
    if kind == "categorical":
        out = out[out["VALUE"].str.strip().ne("")].copy()

    return out, kind


def ordered_visits(df: pd.DataFrame) -> list[str]:
    """Return visits in clinical order using AVISIT_ORDER/AVISITN when available."""
    if "AVISIT" not in df.columns or df.empty:
        return []

    order_col = "AVISIT_ORDER" if "AVISIT_ORDER" in df.columns else "AVISITN" if "AVISITN" in df.columns else None
    if order_col:
        tmp = df[["AVISIT", order_col]].copy()
        tmp[order_col] = pd.to_numeric(tmp[order_col], errors="coerce")
        tmp = tmp.groupby("AVISIT", dropna=False)[order_col].min().reset_index()
        tmp = tmp.sort_values([order_col, "AVISIT"], na_position="last")
        return tmp["AVISIT"].dropna().astype(str).tolist()

    return sorted(df["AVISIT"].dropna().astype(str).unique().tolist())
