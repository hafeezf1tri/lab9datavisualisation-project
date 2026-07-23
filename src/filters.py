from __future__ import annotations

from typing import Any

import pandas as pd

DEFAULT_FILTERS: dict[str, Any] = {
    "year_range": None, "genres": [], "countries": [], "companies": [],
    "ratings": [], "budget_bands": [], "score_range": None, "min_votes": 0,
    "exclude_unknown": False,
}


def apply_filters(
    frame: pd.DataFrame,
    filters: dict[str, Any] | None = None,
    selections: dict[str, Any] | None = None,
) -> pd.DataFrame:
    filters = {**DEFAULT_FILTERS, **(filters or {})}
    selections = selections or {}
    mask = pd.Series(True, index=frame.index)
    years = filters["year_range"]
    if years is not None:
        mask &= frame["release_year"].between(years[0], years[1])
    for key, column in [
        ("genres", "genre"), ("countries", "country"), ("companies", "company"),
        ("ratings", "rating"), ("budget_bands", "budget_band"),
    ]:
        values = filters.get(key) or []
        if values:
            mask &= frame[column].isin(values)
    score_range = filters.get("score_range")
    if score_range is not None:
        mask &= frame["score"].between(score_range[0], score_range[1])
    if filters.get("min_votes", 0):
        mask &= frame["votes"].fillna(0).ge(filters["min_votes"])
    if filters.get("exclude_unknown"):
        for column in ["genre", "country", "company", "rating"]:
            mask &= frame[column].ne("Unknown")
    for state_key, column in [
        ("selected_genre", "genre"), ("selected_country", "country"),
        ("selected_company", "company"), ("selected_director", "director"),
        ("selected_movie_id", "movie_id"),
    ]:
        value = selections.get(state_key)
        if value:
            mask &= frame[column].eq(value)
    return frame.loc[mask].copy()


def describe_filters(filters: dict[str, Any], selections: dict[str, Any]) -> str:
    parts: list[str] = []
    if filters.get("year_range"):
        parts.append(f"Years {filters['year_range'][0]}-{filters['year_range'][1]}")
    for key, label in [
        ("genres", "Genres"), ("countries", "Countries"), ("companies", "Companies"),
        ("ratings", "Ratings"), ("budget_bands", "Budget bands"),
    ]:
        if filters.get(key):
            parts.append(f"{label}: {', '.join(map(str, filters[key]))}")
    if filters.get("score_range"):
        parts.append(
            f"Score {filters['score_range'][0]:.1f}-{filters['score_range'][1]:.1f}"
        )
    if filters.get("min_votes"):
        parts.append(f"Votes >= {filters['min_votes']:,}")
    if filters.get("exclude_unknown"):
        parts.append("Unknown categories excluded")
    for key, label in [
        ("selected_genre", "Selected genre"), ("selected_country", "Selected country"),
        ("selected_company", "Selected company"), ("selected_director", "Selected director"),
    ]:
        if selections.get(key):
            parts.append(f"{label}: {selections[key]}")
    return " | ".join(parts) if parts else "All records"
