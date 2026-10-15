from __future__ import annotations

from io import BytesIO
import re
from pathlib import Path
from typing import Iterable

import pandas as pd
import streamlit as st

PARAMCD_PATTERN = re.compile(
    r"^(?P<source>.+?)_PARAMCD_(?P<parameter>.+?)_(?P<value_type>AVALC|AVAL)$",
    flags=re.IGNORECASE,
)

DEFAULT_ARD_DIRS = (
    Path("ard_data"),
    Path("data") / "ard",
    Path("data") / "ards",
    Path("."),
)


def discover_ard_files(search_dirs: Iterable[Path] = DEFAULT_ARD_DIRS) -> list[Path]:
    """Return unique CSV ARD files found in supported local locations."""
    files: list[Path] = []
    seen: set[str] = set()
    for directory in search_dirs:
        directory = Path(directory)
        if not directory.exists() or not directory.is_dir():
            continue
        candidates = directory.glob("*.csv") if directory == Path(".") else directory.rglob("*.csv")
        for path in candidates:
            resolved = str(path.resolve())
            if resolved not in seen:
                seen.add(resolved)
                files.append(path)
    return sorted(files, key=lambda p: p.name.lower())


def study_id_from_filename(path: str | Path, study_ids: Iterable[str]) -> str | None:
    """Match a workbook Study ID to an ARD filename when embedded in it."""
    name = Path(path).name.upper()
    matches = [str(s) for s in study_ids if str(s).strip() and str(s).upper() in name]
    return max(matches, key=len) if matches else None


def filter_ard_files_for_studies(files: Iterable[Path], study_ids: Iterable[str]) -> list[Path]:
    """Prefer ARDs matching filtered studies; fall back to all files."""
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
    """Parse PARAMCD_*_AVAL / PARAMCD_*_AVALC columns."""
    rows = []
    for column in columns:
        match = PARAMCD_PATTERN.match(str(column))
        if not match:
            continue
        info = match.groupdict()
        rows.append({
            "Variable": info["parameter"],
            "Source": info["source"],
            "Value Type": info["value_type"].upper(),
            "Column": column,
        })
    catalog = pd.DataFrame(rows)
    if catalog.empty:
        return pd.DataFrame(columns=["Variable", "Source", "Value Type", "Column", "Label"])
    duplicate_param = catalog["Variable"].duplicated(keep=False)
    catalog["Label"] = catalog["Variable"]
    catalog.loc[duplicate_param, "Label"] = (
        catalog.loc[duplicate_param, "Variable"] + " · "
        + catalog.loc[duplicate_param, "Source"] + " · "
        + catalog.loc[duplicate_param, "Value Type"]
    )
    return catalog.sort_values(["Variable", "Source", "Value Type"], kind="stable").reset_index(drop=True)


def prepare_variable_data(
    ard: pd.DataFrame, value_column: str, value_type: str
) -> tuple[pd.DataFrame, str]:
    """Return data for charts, using the last nonempty concatenated value.

    Example: '2 | 5 | 4 | 3' -> '3'. This is positional, NOT a verified
    chronological/latest-data-cut selection. The original ARD is unchanged.
    """
    keep = [
        c for c in ["USUBJID", "AVISIT", "AVISITN", "AVISIT_ORDER", value_column]
        if c in ard.columns
    ]
    out = ard[keep].copy().rename(columns={value_column: "VALUE"})
    raw = out["VALUE"].astype("string")

    # The merge separator is a pipe surrounded by whitespace.
    # Avoid interpreting a pipe inside ordinary text as a separator.
    concatenated = raw.str.contains(r"\s+\|\s+", regex=True, na=False)
    resolved = raw.str.strip()
    if concatenated.any():
        resolved.loc[concatenated] = raw.loc[concatenated].str.split(
            r"\s+\|\s+"
        ).map(
            lambda values: next(
                (part.strip() for part in reversed(values) if part.strip()),
                "",
            )
        )
    resolved = resolved.mask(resolved.eq(""), pd.NA)

    if str(value_type).upper() == "AVAL":
        out["VALUE"] = pd.to_numeric(resolved, errors="coerce")
        kind = "numeric"
    else:
        out["VALUE"] = resolved.astype("string")
        kind = "categorical"

    out = out.loc[out["VALUE"].notna()].copy()
    return out, kind


def ordered_visits(variable_df: pd.DataFrame) -> list[str]:
    """Return visit labels using AVISIT_ORDER as preferred clinical order."""
    if "AVISIT" not in variable_df.columns:
        return []
    work = variable_df.loc[variable_df["AVISIT"].notna()].copy()
    if work.empty:
        return []
    work["AVISIT"] = work["AVISIT"].astype(str)
    if "AVISIT_ORDER" in work.columns:
        order = work["AVISIT_ORDER"].astype("string").str.extract(
            r"^\s*(\d+)", expand=False
        )
        order = pd.to_numeric(order, errors="coerce")
        if order.notna().any():
            work["_order"] = order
            return (
                work[["AVISIT", "_order"]]
                .dropna(subset=["_order"])
                .groupby("AVISIT", as_index=False)["_order"]
                .min()
                .sort_values(["_order", "AVISIT"])["AVISIT"]
                .tolist()
            )
    if "AVISITN" in work.columns:
        order = pd.to_numeric(work["AVISITN"], errors="coerce")
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
