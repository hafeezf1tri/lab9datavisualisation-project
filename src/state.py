from __future__ import annotations

from typing import Any

import streamlit as st

SELECTION_KEYS = [
    "selected_genre", "selected_country", "selected_company",
    "selected_director", "selected_movie_id",
]
FILTER_WIDGET_KEYS = [
    "filter_year_range", "filter_genres", "filter_countries", "filter_companies",
    "filter_ratings", "filter_budget_bands", "filter_score_range",
    "filter_min_votes", "filter_exclude_unknown",
]


def initialise_state() -> None:
    for key in SELECTION_KEYS:
        st.session_state.setdefault(key, None)
    st.session_state.setdefault("brushed_movie_ids", [])


def selections() -> dict[str, Any]:
    return {key: st.session_state.get(key) for key in SELECTION_KEYS}


def set_selection(key: str, value: Any, clear_children: bool = True) -> bool:
    if value in ("", [], ()):
        value = None
    if st.session_state.get(key) == value:
        return False
    st.session_state[key] = value
    if clear_children:
        hierarchy = ["selected_genre", "selected_company", "selected_director", "selected_movie_id"]
        if key in hierarchy:
            for child in hierarchy[hierarchy.index(key) + 1 :]:
                st.session_state[child] = None
    return True


def reset_all() -> None:
    for key in FILTER_WIDGET_KEYS + SELECTION_KEYS + ["brushed_movie_ids"]:
        st.session_state.pop(key, None)


def selection_points(event: Any) -> list[dict]:
    if event is None:
        return []
    try:
        if hasattr(event, "selection"):
            selection = event.selection
        elif isinstance(event, dict):
            selection = event.get("selection", event)
        else:
            return []
        if hasattr(selection, "points"):
            return list(selection.points)
        return list(selection.get("points", []))
    except (AttributeError, TypeError):
        return []


def custom_value(point: dict, index: int = 0) -> Any:
    custom = point.get("customdata")
    if custom is None:
        return None
    if isinstance(custom, (list, tuple)):
        return custom[index] if len(custom) > index else None
    return custom if index == 0 else None
