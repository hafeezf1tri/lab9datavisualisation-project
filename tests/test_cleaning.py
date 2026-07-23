import pandas as pd
import pytest

from src.data_cleaning import SchemaValidationError, clean_movies, validate_schema


def test_required_column_validation(raw_movies):
    validate_schema(raw_movies)
    with pytest.raises(SchemaValidationError, match="gross"):
        validate_schema(raw_movies.drop(columns=["gross"]))


def test_numeric_rules_and_date_fallback(raw_movies):
    raw_movies["gross"] = raw_movies["gross"].astype(object)
    raw_movies.loc[0, "budget"] = 0
    raw_movies.loc[1, "budget"] = -5
    raw_movies.loc[2, "gross"] = "not-a-number"
    raw_movies.loc[3, "score"] = 12
    result = clean_movies(raw_movies)
    assert result.data.loc[0, "budget"] != result.data.loc[0, "budget"]
    assert pd.isna(result.data.loc[1, "budget"])
    assert pd.isna(result.data.loc[2, "gross"])
    assert pd.isna(result.data.loc[3, "score"])
    assert result.data.loc[1, "release_year"] == 2001
    assert bool(result.data.loc[1, "date_parse_failed"])


def test_duplicate_removal_and_unique_ids(raw_movies):
    duplicated = pd.concat([raw_movies, raw_movies.iloc[[0]]], ignore_index=True)
    result = clean_movies(duplicated)
    assert len(result.data) == len(raw_movies)
    assert result.audit["exact_duplicates_removed"] == 1
    assert result.data["movie_id"].is_unique


def test_financial_calculations_and_null_profitable(raw_movies):
    raw_movies.loc[0, ["budget", "gross"]] = [10.0, 25.0]
    raw_movies.loc[1, "budget"] = 0
    result = clean_movies(raw_movies).data
    assert result.loc[0, "estimated_profit"] == 15.0
    assert result.loc[0, "roi_pct"] == 150.0
    assert bool(result.loc[0, "is_profitable"])
    assert pd.isna(result.loc[1, "roi_pct"])
    assert pd.isna(result.loc[1, "is_profitable"])


def test_budget_bands_and_anomalies(raw_movies):
    result = clean_movies(raw_movies).data
    assert result.loc[result["has_valid_budget"], "budget_band"].ne("Unknown").all()
    assert set(result["anomaly_category"]).issubset(
        {"High-budget underperformer", "Breakout success", "Typical", "Unknown"}
    )
