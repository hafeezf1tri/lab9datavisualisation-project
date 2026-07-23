from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import CLEAN_DATA_PATH, EVIDENCE_PATH, QUALITY_PATH


@st.cache_data(show_spinner=False)
def load_movies(path: str | Path = CLEAN_DATA_PATH) -> pd.DataFrame:
    return pd.read_parquet(path)


@st.cache_data(show_spinner=False)
def load_json(path: str | Path) -> dict:
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def load_quality() -> dict:
    return load_json(QUALITY_PATH)


def load_evidence() -> dict:
    return load_json(EVIDENCE_PATH)
