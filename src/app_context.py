from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st

from src.config import CLEAN_DATA_PATH
from src.data_loader import load_movies, load_quality
from src.filters import apply_filters
from src.state import selections
from src.ui import build_sidebar, render_scope


@dataclass
class AppContext:
    all_data: pd.DataFrame
    base: pd.DataFrame
    filtered: pd.DataFrame
    filters: dict
    selections: dict
    quality: dict


def configure_page(title: str) -> None:
    st.set_page_config(
        page_title=f"{title} · Movie Industry Dashboard",
        page_icon="🎬", layout="wide",
    )


def get_context() -> AppContext | None:
    if not CLEAN_DATA_PATH.exists():
        st.error(
            "Prepared data is not available. Place `movies.csv` at the project root "
            "or in `data/raw/`, then run `python scripts/prepare_data.py`."
        )
        return None
    try:
        data = load_movies()
        quality = load_quality()
    except (OSError, ValueError, ImportError) as exc:
        st.error(f"Could not load the prepared data: {exc}")
        return None
    filters = build_sidebar(data)
    selected = selections()
    base = apply_filters(data, filters)
    filtered = apply_filters(data, filters, selected)
    render_scope(filters, filtered)
    return AppContext(data, base, filtered, filters, selected, quality)


def selection_scope(context: AppContext, omit: set[str] | None = None) -> pd.DataFrame:
    selected = context.selections.copy()
    for key in omit or set():
        selected[key] = None
    return apply_filters(context.all_data, context.filters, selected)
