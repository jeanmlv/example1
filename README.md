# example1

############# arges commons dashboard.py

import re

import pandas as pd
import streamlit as st
from pathlib import Path
import sys

COMMONS_DIRECTORY = Path(__file__).resolve().parent
if str(COMMONS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(COMMONS_DIRECTORY))

from src.config import REQUIRED_SHEETS, PAGES, JNJ_RED
from src.data_loader import filter_by_study
from src.fetch_arges_commons_workbook import load_workbook
from src.filters import clean_text_values
from views import (
    overview,
    studies_assets,
    data_availability,
    processing,
    data_splits,
    ard,
    variable_definitions,
    data_analysis,
    external_data,
)


@st.cache_data(
    ttl=3600, show_spinner="Loading ARGES Commons workbook from SharePoint..."
)
def load_data() -> dict[str, pd.DataFrame]:
    """Fetch the workbook from SharePoint and normalize column names."""
    out = {}
    for name, df in load_workbook(verbose=False).items():
        df = df.copy()
        df.columns = [
            re.sub(r"\s+", " ", str(c).replace("\n", " ")).strip() for c in df.columns
        ]
        out[name] = df.dropna(how="all")
    return out


def render_filters(studies: pd.DataFrame) -> tuple[pd.DataFrame, set[str]]:
    """Render main-page study filters and return the matching study IDs."""
    st.subheader("Filters")
    eligible = studies.copy()
    columns = st.columns(4)
    filter_specs = (
        ("Study", "Study Name"),
        ("Phase", "Phase"),
        ("Trial status", "Trial Status"),
        ("Compound", "Compound"),
    )

    for column, (label, field) in zip(columns, filter_specs):
        with column:
            selected = st.multiselect(
                label,
                clean_text_values(eligible.get(field, pd.Series(dtype=str))),
            )
        if selected and field in eligible:
            eligible = eligible[eligible[field].astype(str).isin(selected)]

    selected_ids = set(eligible["Study ID"].dropna().astype(str))
    st.caption(
        f"{len(selected_ids)} of {studies['Study ID'].nunique()} studies selected"
    )
    st.button("🔄 Reload workbook from SharePoint", on_click=load_data.clear)
    st.markdown("---")

    return eligible, selected_ids


st.markdown(
    f"""
    <style>
    /* =========================================================
        ARGES Commons — theme-aware styling
        Works with both Streamlit Light and Dark modes
        ========================================================= */

    /* Main application */
    .stApp {{
        background-color: var(--background-color);
        color: var(--text-color);
    }}

    .block-container {{
        padding-top: 1.3rem;
        padding-bottom: 3rem;
        max-width: 1500px;
    }}

    /* Typography */
    h1, h2, h3 {{
        letter-spacing: -0.02em;
        color: var(--text-color);
    }}

    h1 {{
        font-size: 2rem !important;
    }}

    /* =========================================================
        KPI cards
        ========================================================= */

    div[data-testid="stMetric"] {{
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.25);
        border-radius: 14px;
        padding: 14px 16px;
        box-shadow: 0 2px 10px rgba(16, 24, 40, 0.06);
    }}

    div[data-testid="stMetricLabel"] {{
        color: var(--text-color) !important;
    }}

    div[data-testid="stMetricLabel"] p {{
        color: var(--text-color) !important;
        opacity: 0.78;
    }}

    div[data-testid="stMetricValue"] {{
        color: var(--text-color) !important;
    }}

    div[data-testid="stMetricValue"] > div {{
        color: var(--text-color) !important;
    }}

    /* =========================================================
        ARGES branding / hero
        ========================================================= */

    .eyebrow {{
        font-size: 12px;
        letter-spacing: .12em;
        text-transform: uppercase;
        color: {JNJ_RED};
        font-weight: 800;
    }}

    .hero {{
        padding: 22px 24px;
        border: 1px solid rgba(128, 128, 128, 0.25);
        border-radius: 18px;
        background-color: var(--secondary-background-color);
        margin-bottom: 18px;
    }}

    .hero-title {{
        font-size: 28px;
        font-weight: 800;
        line-height: 1.15;
        margin: 5px 0 6px 0;
        color: var(--text-color);
    }}

    .hero-copy,
    .section-note {{
        color: var(--text-color);
        opacity: 0.70;
        font-size: 13px;
    }}

    /* =========================================================
        Tables / controls
        ========================================================= */

    [data-testid="stDataFrame"] {{
        border: 1px solid rgba(128, 128, 128, 0.25);
        border-radius: 12px;
        overflow: hidden;
    }}

    hr {{
        border-color: rgba(128, 128, 128, 0.25);
    }}

    </style>
    """,
    unsafe_allow_html=True,
)

try:
    data = load_data()
except (Exception, SystemExit) as exc:  # fetch helper raises SystemExit on Graph errors
    st.error(f"The workbook could not be loaded: {exc}")
    st.stop()
missing = [s for s in REQUIRED_SHEETS if s not in data]
if missing:
    st.warning("Some expected sheets are not present: " + ", ".join(missing))

studies = data.get("01_STUDIES", pd.DataFrame()).copy()
if studies.empty or "Study ID" not in studies.columns:
    st.error("Sheet 01_STUDIES with a Study ID column is required.")
    st.stop()

# render_header()
st.caption(
    "A study-centric view from source assets and processing through data splits, analysis-ready datasets, variable traceability, analyses, and external data."
)

eligible, selected_ids = render_filters(studies)
page = (
    st.segmented_control(
        "Navigation", PAGES, default="Overview", label_visibility="collapsed"
    )
    or "Overview"
)
filtered = {name: filter_by_study(df, selected_ids) for name, df in data.items()}
filtered["01_STUDIES"] = eligible.copy()
ROUTES = {
    "Overview": overview.render,
    "Studies & Assets": studies_assets.render,
    "Data Availability": data_availability.render,
    "Processing": processing.render,
    "Data Splits": data_splits.render,
    "ARD": ard.render,
    "Variable Definitions": variable_definitions.render,
    "Data Analysis": data_analysis.render,
    "External Data": external_data.render,
}
ROUTES[page](filtered, data)
st.markdown("---")
st.caption(
    "ARGES Commons • Data shown reflects the selected workbook and active filters. Validate source metadata before operational or clinical use."
)


############################# fetch arges commons workbook.py

"""Pull Arges Commons workbook in SharePoint via Microsoft Graph.

Auth: app-only (client credentials) using CLIENT_ID, CLIENT_SECRET, TENANT_ID
from .env. The app registration needs Sites.Read.All (or Sites.Selected with
access granted to the site) as an *application* permission with admin consent.

Usage:
    from scripts.fetch_arges_commons_workbook import load_workbook
    sheets = load_workbook()          # {sheet_name: DataFrame}
    df = sheets["Sheet1"]

    python scripts/fetch_arges_commons_workbook.py [--sheet NAME]
"""

import argparse
import base64
import io
import os
import time

import pandas as pd
import requests
from dotenv import load_dotenv

GRAPH = "https://graph.microsoft.com/v1.0"
FILE_URL = (
    "https://jnj.sharepoint.com/:x:/r/teams/ComputerVisionProductsJRDDataScience-M0XX-NovelUCScoreEndo"
    "/_layouts/15/Doc.aspx?sourcedoc=%7BD4D11FBC-A9FD-4B38-8180-D6B55BD25CF9%7D"
    "&file=ARGES_COMMONS.xlsx&action=default&mobileredirect=true&wdwpf=doclib-c"
)


def get_token() -> str:
    load_dotenv()
    tenant, cid, secret = (
        os.environ.get(k) for k in ("TENANT_ID", "CLIENT_ID", "CLIENT_SECRET")
    )
    if not all((tenant, cid, secret)):
        raise SystemExit("TENANT_ID, CLIENT_ID and CLIENT_SECRET must be set in .env")
    r = requests.post(
        f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
        data={
            "client_id": cid,
            "client_secret": secret,
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials",
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def get(session: requests.Session, url: str, **kw) -> requests.Response:
    r = session.get(url, timeout=60, **kw)
    if not r.ok:
        raise SystemExit(f"Graph error {r.status_code} for {url}\n{r.text}")
    return r


def find_item(session: requests.Session) -> tuple[str, str]:
    """Resolve the workbook directly from its sharing URL (no searching)."""
    token = base64.urlsafe_b64encode(FILE_URL.encode()).decode().rstrip("=")
    item = get(
        session, f"{GRAPH}/shares/u!{token}/driveItem?$select=id,parentReference"
    ).json()
    return item["parentReference"]["driveId"], item["id"]


def load_workbook(
    sheet: str | None = None, verbose: bool = True
) -> dict[str, pd.DataFrame]:
    """Return the ARGES_COMMONS workbook as {sheet_name: DataFrame}.

    Downloads the whole file into memory (nothing saved to disk) and parses it.
    sheet: load only this sheet (still returned as a one-item dict).
    """
    t0 = time.time()

    def log(msg):
        if verbose:
            print(f"[{time.time() - t0:6.1f}s] {msg}", flush=True)

    log("Requesting access token...")
    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {get_token()}"
    drive_id, item_id = find_item(session)
    log(f"Found workbook (item {item_id}).")

    log("Downloading workbook...")
    content = get(session, f"{GRAPH}/drives/{drive_id}/items/{item_id}/content").content
    log(f"Downloaded {len(content) / 1e6:.1f} MB. Parsing...")
    frames = pd.read_excel(io.BytesIO(content), sheet_name=sheet or None)
    if sheet:
        frames = {sheet: frames}
    # for name, df in frames.items():
    #     log(f"  {name!r}: {df.shape[0]} rows x {df.shape[1]} cols")
    return frames


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sheet", help="Sheet name (default: all)")
    args = p.parse_args()

    for name, df in load_workbook(args.sheet).items():
        print(f"\n=== {name}: {df.shape[0]} rows x {df.shape[1]} cols ===")
        print(df.head())


if __name__ == "__main__":
    main()


