
from src.data_cleaning import clean_movies
from src.metrics import calculate_kpis, grouped_metrics


def test_kpis_on_known_fixture(raw_movies):
    frame = clean_movies(raw_movies.iloc[:2]).data
    expected_gross = raw_movies.iloc[:2]["gross"].sum()
    expected_profit = (raw_movies.iloc[:2]["gross"] - raw_movies.iloc[:2]["budget"]).sum()
    kpis = calculate_kpis(frame)
    assert kpis["total_gross"] == expected_gross
    assert kpis["estimated_profit"] == expected_profit
    assert kpis["movie_count"] == 2
    assert kpis["valid_financial_count"] == 2


def test_minimum_sample_size_enforcement(raw_movies):
    frame = clean_movies(raw_movies).data
    grouped = grouped_metrics(frame, "genre", minimum=10)
    assert grouped["median_roi"].isna().all()
    grouped = grouped_metrics(frame, "genre", minimum=1)
    assert grouped["median_roi"].notna().all()
