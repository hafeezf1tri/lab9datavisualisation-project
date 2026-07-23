"""Validated, traceable preparation of the Movie Industry CSV."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from src.config import CATEGORY_COLUMNS, REQUIRED_COLUMNS, UNKNOWN


class SchemaValidationError(ValueError):
    """Raised when the source file does not satisfy the dataset contract."""


@dataclass
class CleaningResult:
    data: pd.DataFrame
    audit: dict[str, Any]


def normalise_column_name(value: str) -> str:
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower())).strip("_")


def validate_schema(frame: pd.DataFrame) -> None:
    missing = sorted(REQUIRED_COLUMNS.difference(frame.columns))
    if missing:
        raise SchemaValidationError(
            "The movie CSV is missing required columns: " + ", ".join(missing)
        )


def _clean_category(series: pd.Series) -> pd.Series:
    cleaned = series.astype("string").str.strip().str.replace(r"\s+", " ", regex=True)
    return cleaned.replace({"": pd.NA, "<NA>": pd.NA, "nan": pd.NA}).fillna(UNKNOWN)


def _stable_id(name: str, year: object, row: int) -> str:
    token = f"{str(name).strip().casefold()}|{year}|{row}"
    return hashlib.sha1(token.encode("utf-8")).hexdigest()[:16]


def add_calculated_attributes(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Add all record-level analytical attributes in one auditable function."""
    df = frame.copy()
    df["has_valid_budget"] = df["budget"].notna() & df["budget"].gt(0)
    df["has_valid_gross"] = df["gross"].notna() & df["gross"].gt(0)
    df["has_valid_financials"] = df["has_valid_budget"] & df["has_valid_gross"]

    valid = df["has_valid_financials"]
    df["estimated_profit"] = (df["gross"] - df["budget"]).where(valid)
    df["roi_pct"] = (((df["gross"] - df["budget"]) / df["budget"]) * 100).where(valid)
    df["gross_budget_ratio"] = (df["gross"] / df["budget"]).where(valid)
    df["is_profitable"] = pd.Series(pd.NA, index=df.index, dtype="boolean")
    df.loc[valid, "is_profitable"] = df.loc[valid, "estimated_profit"].gt(0)

    df["release_decade"] = (
        (df["release_year"] // 10) * 10
    ).astype("Int64")
    df["release_month"] = df["released_date"].dt.month.astype("Int64")
    df["release_month_name"] = df["released_date"].dt.month_name().fillna(UNKNOWN)
    df["release_period_label"] = df["release_decade"].map(
        lambda x: f"{int(x)}s" if pd.notna(x) else UNKNOWN
    )

    df["score_band"] = pd.cut(
        df["score"],
        bins=[-np.inf, 5, 6.5, 7.5, np.inf],
        labels=["Low", "Moderate", "Good", "Excellent"],
        right=False,
    ).astype("string").fillna(UNKNOWN)

    budget_labels = ["Low budget", "Lower-middle", "Upper-middle", "High budget"]
    df["budget_band"] = pd.Series(UNKNOWN, index=df.index, dtype="string")
    budget_thresholds: list[float] = []
    budget_valid = df.loc[df["has_valid_budget"], "budget"]
    if not budget_valid.empty:
        try:
            bands, edges = pd.qcut(
                budget_valid, q=4, labels=budget_labels, retbins=True, duplicates="drop"
            )
            actual_labels = budget_labels[: len(edges) - 1]
            if len(actual_labels) != len(bands.cat.categories):
                bands = pd.qcut(budget_valid, q=4, labels=False, duplicates="drop")
                bands = bands.map(lambda x: actual_labels[int(x)] if pd.notna(x) else UNKNOWN)
            df.loc[budget_valid.index, "budget_band"] = bands.astype("string")
            budget_thresholds = [float(x) for x in edges]
        except (ValueError, IndexError):
            df.loc[budget_valid.index, "budget_band"] = "Low budget"

    conditions = [
        df["roi_pct"].lt(0), df["roi_pct"].ge(0) & df["roi_pct"].lt(100),
        df["roi_pct"].ge(100) & df["roi_pct"].lt(300),
        df["roi_pct"].ge(300) & df["roi_pct"].lt(700), df["roi_pct"].ge(700),
    ]
    df["performance_category"] = np.select(
        conditions,
        ["Loss-making", "Low return", "Moderate return", "High return", "Exceptional return"],
        default=UNKNOWN,
    )

    financial = df.loc[valid]
    budget_q25 = budget_q75 = roi_q75 = np.nan
    df["anomaly_category"] = UNKNOWN
    if not financial.empty:
        budget_q25, budget_q75 = financial["budget"].quantile([0.25, 0.75])
        roi_q75 = financial["roi_pct"].quantile(0.75)
        df.loc[valid, "anomaly_category"] = "Typical"
        df.loc[
            valid & df["budget"].ge(budget_q75) & df["roi_pct"].lt(0),
            "anomaly_category",
        ] = "High-budget underperformer"
        df.loc[
            valid & df["budget"].le(budget_q25) & df["roi_pct"].ge(roi_q75),
            "anomaly_category",
        ] = "Breakout success"

    metadata = {
        "budget_band_edges": budget_thresholds,
        "anomaly_thresholds": {
            "budget_q25": None if pd.isna(budget_q25) else float(budget_q25),
            "budget_q75": None if pd.isna(budget_q75) else float(budget_q75),
            "roi_q75": None if pd.isna(roi_q75) else float(roi_q75),
        },
    }
    return df, metadata


def clean_movies(raw: pd.DataFrame) -> CleaningResult:
    if raw.empty:
        raise ValueError("The movie CSV is empty.")
    df = raw.copy()
    df.columns = [normalise_column_name(c) for c in df.columns]
    validate_schema(df)
    source_rows = len(df)
    df.insert(0, "source_row_number", np.arange(1, len(df) + 1))

    duplicate_columns = [c for c in df.columns if c != "source_row_number"]
    duplicate_mask = df.duplicated(subset=duplicate_columns, keep="first")
    exact_duplicates = int(duplicate_mask.sum())
    df = df.loc[~duplicate_mask].copy()

    invalid: dict[str, int] = {}
    for col in ["budget", "gross", "score", "votes", "runtime", "year"]:
        original_nonempty = df[col].notna() & df[col].astype(str).str.strip().ne("")
        converted = pd.to_numeric(df[col], errors="coerce")
        invalid[f"{col}_non_numeric"] = int((original_nonempty & converted.isna()).sum())
        df[col] = converted

    for col in ("budget", "gross", "runtime"):
        bad = df[col].notna() & df[col].le(0)
        invalid[f"{col}_non_positive"] = int(bad.sum())
        df.loc[bad, col] = np.nan
    bad_score = df["score"].notna() & ~df["score"].between(0, 10)
    invalid["score_out_of_range"] = int(bad_score.sum())
    df.loc[bad_score, "score"] = np.nan
    bad_votes = df["votes"].notna() & df["votes"].lt(0)
    invalid["votes_negative"] = int(bad_votes.sum())
    df.loc[bad_votes, "votes"] = np.nan

    for col in CATEGORY_COLUMNS:
        df[f"{col}_was_missing"] = df[col].isna() | df[col].astype(str).str.strip().eq("")
        df[col] = _clean_category(df[col])
    df["name"] = _clean_category(df["name"])

    release_text = df["released"].astype("string").str.replace(
        r"\s*\([^)]*\)\s*$", "", regex=True
    )
    df["released_date"] = pd.to_datetime(release_text, errors="coerce", format="mixed")
    df["date_parse_failed"] = df["released"].notna() & df["released_date"].isna()
    parsed_year = df["released_date"].dt.year.astype("Int64")
    source_year = df["year"].round().astype("Int64")
    df["release_year"] = parsed_year.fillna(source_year)

    title_key = df["name"].str.casefold().str.replace(r"[^a-z0-9]+", "", regex=True)
    duplicate_key = pd.DataFrame({
        "title": title_key,
        "year": df["release_year"],
        "company": df["company"].str.casefold(),
        "director": df["director"].str.casefold(),
    })
    df["suspected_duplicate"] = duplicate_key.duplicated(keep=False)
    df["movie_id"] = [
        _stable_id(name, year, int(row))
        for name, year, row in zip(df["name"], df["release_year"], df["source_row_number"])
    ]

    df, metadata = add_calculated_attributes(df)
    audit = {
        "source_row_count": source_rows,
        "cleaned_row_count": len(df),
        "exact_duplicates_removed": exact_duplicates,
        "invalid_values_converted_to_missing": invalid,
        **metadata,
    }
    return CleaningResult(df.reset_index(drop=True), audit)
