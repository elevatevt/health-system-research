"""Shared paths, source registry and loaders for the health-system research build."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "outputs"

# Every non-derived value in the outputs traces to one of these.
SOURCES = {
    "compendium_systems": {
        "url": "https://www.ahrq.gov/sites/default/files/wysiwyg/chsp/compendium/chsp-compendium-2023-rev.xlsx",
        "file": "chsp-compendium-2023-rev.xlsx",
        "as_of": "AHRQ Compendium 2023 (system file rev. 2025-09); systems as of end-2023",
    },
    "compendium_hospitals": {
        "url": "https://www.ahrq.gov/sites/default/files/wysiwyg/chsp/compendium/chsp-hospital-linkage-2023.xlsx",
        "file": "chsp-hospital-linkage-2023.xlsx",
        "as_of": "AHRQ Compendium 2023 hospital linkage; hospitals as of end-2023",
    },
    "compendium_techdoc": {
        "url": "https://www.ahrq.gov/sites/default/files/wysiwyg/chsp/compendium/2023-compendium-techdoc-rev.pdf",
        "file": "2023-compendium-techdoc-rev.pdf",
    },
    "hospital_linkage_techdoc": {
        "url": "https://www.ahrq.gov/sites/default/files/wysiwyg/chsp/compendium/2023-hospital-linkage-techdoc.pdf",
        "file": "2023-hospital-linkage-techdoc.pdf",
    },
    "hcris_fy2024": {
        "url": "https://data.cms.gov/sites/default/files/2026-09/e85544f7-57ef-477e-9640-313ac0aac400/CostReport_2024_Final.csv",
        "file": "CostReport_2024_Final.csv",
        "as_of": "CMS Hospital Provider Cost Report FY2024 (periods beginning 2023-10-01..2024-09-30); file modified 2026-09-29",
    },
}

COMPENDIUM_EDITION = "2023 (rev. 2025-09)"

# sys_ownership / hos_ownership codes. The hospital-linkage tech doc lists 2=public and
# 3=church; the system tech doc and the data itself (code 2 = Ascension, AdventHealth,
# CHRISTUS...; code 3 = county/authority hospitals) show 2=church, 3=public.
OWNERSHIP = {1: "nonprofit", 2: "church-operated", 3: "public/government", 4: "other (undocumented)", 5: "for-profit"}
NONPROFIT_CODES = {1, 2}
# No sys_ownership code; its only HCRIS-coded hospital is nonprofit (code 1).
NONPROFIT_OVERRIDES = {"HSI00001176": "University of Miami Health System"}


def raw(key: str) -> Path:
    return RAW / SOURCES[key]["file"]


def load_systems() -> pd.DataFrame:
    return pd.read_excel(raw("compendium_systems"), dtype={"health_sys_id": str})


def load_hospitals() -> pd.DataFrame:
    return pd.read_excel(raw("compendium_hospitals"), dtype={"ccn": str, "health_sys_id": str})


def nonprofit_system_ids(systems: pd.DataFrame) -> set:
    ids = set(systems.loc[systems.sys_ownership.isin(NONPROFIT_CODES), "health_sys_id"])
    return ids | set(NONPROFIT_OVERRIDES)
