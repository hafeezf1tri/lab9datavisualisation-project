from src.data_cleaning import clean_movies
from src.data_quality import add_outlier_flags, build_quality_summary


def test_quality_summary_counts(raw_movies):
    raw_movies.loc[0, "budget"] = 0
    result = clean_movies(raw_movies)
    frame, outliers = add_outlier_flags(result.data)
    quality = build_quality_summary(frame, result.audit, outliers)
    assert quality["source_row_count"] == 12
    assert quality["cleaned_row_count"] == 12
    assert quality["valid_budget_count"] == 11
    assert quality["valid_budget_and_gross_count"] == 11
    assert quality["missing_by_column"]["budget"]["count"] == 1
