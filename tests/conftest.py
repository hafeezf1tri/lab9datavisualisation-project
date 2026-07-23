from __future__ import annotations

import pandas as pd
import pytest


@pytest.fixture
def raw_movies() -> pd.DataFrame:
    rows = []
    for i in range(12):
        rows.append({
            "name": f"Movie {i}",
            "rating": "R",
            "genre": "Drama" if i < 6 else "Comedy",
            "year": 2000 + i,
            "released": f"January 1, {2000 + i} (United States)" if i != 1 else "bad date",
            "score": 5.0 + i / 10,
            "votes": 1000 + i,
            "director": f"Director {i % 3}",
            "writer": "Writer",
            "star": "Star",
            "country": "United States",
            "budget": float(10 + i),
            "gross": float(20 + 2 * i),
            "company": f"Company {i % 2}",
            "runtime": 90.0 + i,
        })
    return pd.DataFrame(rows)
