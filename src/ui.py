from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from src.filters import describe_filters
from src.state import initialise_state, reset_all, selections


def compact_number(value: float | None, currency: bool = False) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    sign = "-" if value < 0 else ""
    number = abs(float(value))
    for divisor, suffix in [(1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")]:
        if number >= divisor:
            text = f"{number / divisor:.1f}{suffix}"
            return f"{sign}${text}" if currency else f"{sign}{text}"
    text = f"{number:,.0f}"
    return f"{sign}${text}" if currency else f"{sign}{text}"


def format_pct(value: float | None) -> str:
    return "N/A" if value is None or pd.isna(value) else f"{value:,.1f}%"


def render_kpis(kpis: dict[str, Any]) -> None:
    columns = st.columns(4)
    yoy = kpis.get("gross_yoy_pct")
    columns[0].metric(
        "Total gross revenue", compact_number(kpis.get("total_gross"), True),
        delta=format_pct(yoy) if yoy is not None else None,
        help="Box-office gross, not money retained by a studio.",
    )
    columns[1].metric(
        "Estimated profit", compact_number(kpis.get("estimated_profit"), True),
        help="Gross minus budget; not actual net profit.",
    )
    columns[2].metric(
        "Median ROI", format_pct(kpis.get("median_roi")),
        help=f"Based on {kpis.get('valid_financial_count', 0):,} movies with valid budget and gross.",
    )
    columns[3].metric(
        "Profitable-film rate", format_pct(kpis.get("profitable_rate")),
        help="Share of financially complete movies where gross exceeds budget.",
    )


def render_scope(filters: dict, frame: pd.DataFrame) -> None:
    selected = selections()
    scope_text = describe_filters(filters, selected)
    if selected.get("selected_movie_id"):
        movie_name = (
            frame.iloc[0]["name"]
            if not frame.empty and "name" in frame.columns
            else selected["selected_movie_id"]
        )
        scope_text += f" | Selected movie: {movie_name}"
    col1, col2 = st.columns([5, 1])
    col1.caption(
        f"**Active scope:** {scope_text}  \n"
        f"**Visible:** {len(frame):,} movies | "
        f"{int(frame['has_valid_financials'].sum()):,} with valid financials"
    )
    if col2.button("Reset filters & selection", width="stretch"):
        reset_all()
        st.rerun()


def render_caveats() -> None:
    with st.expander("Definitions and interpretation limits"):
        st.markdown(
            """
- Gross is box-office revenue, not studio revenue.
- Estimated profit is `gross − budget`; it excludes marketing, distribution,
  revenue sharing, taxes, streaming, and home-media income.
- Dollar values are historical and not adjusted for inflation.
- Correlation is not causation. This historical sample is not the current film market.
- Movies without both a positive budget and gross are excluded from profitability metrics.
"""
        )


def render_quality_summary(quality: dict) -> None:
    with st.expander("Data-quality summary"):
        cols = st.columns(4)
        cols[0].metric("Source rows", f"{quality.get('source_row_count', 0):,}")
        cols[1].metric("Cleaned rows", f"{quality.get('cleaned_row_count', 0):,}")
        cols[2].metric("Exact duplicates removed", f"{quality.get('exact_duplicates_removed', 0):,}")
        cols[3].metric("Financial coverage", f"{quality.get('valid_budget_and_gross_count', 0):,}")
        st.caption(
            f"Suspected duplicates retained: {quality.get('suspected_duplicate_count', 0):,} · "
            f"Failed date parses: {quality.get('failed_date_parses', 0):,} · "
            f"Prepared: {quality.get('preparation_timestamp', 'Unknown')}"
        )


def build_sidebar(frame: pd.DataFrame) -> dict:
    initialise_state()
    st.sidebar.header("Global filters")
    years = frame["release_year"].dropna().astype(int)
    min_year, max_year = int(years.min()), int(years.max())
    current = st.session_state.get("filter_year_range", (min_year, max_year))
    current = (max(min_year, int(current[0])), min(max_year, int(current[1])))
    year_range = st.sidebar.slider(
        "Release year", min_year, max_year, current, key="filter_year_range"
    )
    genres = st.sidebar.multiselect(
        "Genre", sorted(frame["genre"].dropna().unique()), key="filter_genres"
    )
    countries = st.sidebar.multiselect(
        "Country", sorted(frame["country"].dropna().unique()), key="filter_countries"
    )

    broad = frame.loc[frame["release_year"].between(*year_range)]
    if genres:
        broad = broad.loc[broad["genre"].isin(genres)]
    if countries:
        broad = broad.loc[broad["country"].isin(countries)]
    company_options = sorted(broad["company"].dropna().unique())
    existing_companies = [
        value for value in st.session_state.get("filter_companies", [])
        if value in company_options
    ]
    if existing_companies != st.session_state.get("filter_companies", []):
        st.session_state["filter_companies"] = existing_companies
    companies = st.sidebar.multiselect(
        "Production company", company_options, key="filter_companies"
    )
    ratings = st.sidebar.multiselect(
        "Content rating", sorted(frame["rating"].dropna().unique()), key="filter_ratings"
    )
    bands = st.sidebar.multiselect(
        "Budget band",
        ["Low budget", "Lower-middle", "Upper-middle", "High budget", "Unknown"],
        key="filter_budget_bands",
    )
    score_values = frame["score"].dropna()
    score_default = (float(score_values.min()), float(score_values.max()))
    score_range_value = st.sidebar.slider(
        "Audience score", 0.0, 10.0,
        st.session_state.get("filter_score_range", score_default), 0.1,
        key="filter_score_range",
    )
    score_range = None if score_range_value == score_default else score_range_value
    min_votes = st.sidebar.number_input(
        "Minimum vote count", min_value=0, value=0, step=1000, key="filter_min_votes"
    )
    exclude_unknown = st.sidebar.toggle(
        "Exclude Unknown categories", value=False, key="filter_exclude_unknown"
    )
    return {
        "year_range": year_range, "genres": genres, "countries": countries,
        "companies": companies, "ratings": ratings, "budget_bands": bands,
        "score_range": score_range, "min_votes": min_votes,
        "exclude_unknown": exclude_unknown,
    }
