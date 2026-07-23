from src.data_cleaning import clean_movies
from src.filters import apply_filters


def test_global_filters(raw_movies):
    frame = clean_movies(raw_movies).data
    result = apply_filters(
        frame,
        {
            "year_range": (2002, 2008),
            "genres": ["Drama"],
            "countries": ["United States"],
            "min_votes": 1000,
        },
    )
    assert result["release_year"].between(2002, 2008).all()
    assert result["genre"].eq("Drama").all()


def test_selection_filter(raw_movies):
    frame = clean_movies(raw_movies).data
    result = apply_filters(frame, selections={"selected_company": "Company 1"})
    assert result["company"].eq("Company 1").all()
