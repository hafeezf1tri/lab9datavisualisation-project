from __future__ import annotations

from typing import Any

import pandas as pd

from src.config import GENERAL_MIN_GROUP_SIZE, MESSAGE_MIN_GROUP_SIZE
from src.metrics import grouped_metrics


def _record(row: pd.Series, **extra: Any) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in row.to_dict().items():
        if pd.isna(value):
            result[key] = None
        else:
            result[key] = value.item() if hasattr(value, "item") else value
    result.update(extra)
    return result


def generate_insight_evidence(frame: pd.DataFrame) -> dict[str, Any]:
    evidence: dict[str, Any] = {}
    genres = grouped_metrics(frame, "genre", GENERAL_MIN_GROUP_SIZE)
    total_gross = frame["gross"].sum()
    if not genres.empty:
        top_gross = genres.sort_values("total_gross", ascending=False).iloc[0]
        evidence["highest_total_gross_genre"] = _record(
            top_gross,
            contribution_pct=float(top_gross["total_gross"] / total_gross * 100)
            if total_gross else None,
        )
        eligible = genres.loc[genres["valid_financial_count"].ge(MESSAGE_MIN_GROUP_SIZE)]
        if not eligible.empty:
            evidence["highest_median_roi_genre"] = _record(
                eligible.sort_values("median_roi", ascending=False).iloc[0]
            )
            evidence["highest_loss_rate_genre"] = _record(
                eligible.sort_values("loss_rate", ascending=False).iloc[0]
            )
        leaders: dict[str, dict[str, Any]] = {}
        for genre in genres["genre"]:
            genre_companies = grouped_metrics(
                frame.loc[frame["genre"].eq(genre)], "company", minimum=1
            )
            if not genre_companies.empty:
                leaders[str(genre)] = _record(
                    genre_companies.sort_values("total_gross", ascending=False).iloc[0]
                )
        evidence["highest_gross_company_by_genre"] = leaders

    yearly = frame.groupby("release_year", observed=True)["gross"].sum(min_count=1).dropna()
    if len(yearly) >= 2:
        yearly = yearly.sort_index()
        latest, previous = yearly.index[-1], yearly.index[-2]
        evidence["latest_year_gross_change"] = {
            "latest_year": int(latest), "previous_year": int(previous),
            "latest_gross": float(yearly.iloc[-1]), "previous_gross": float(yearly.iloc[-2]),
            "change_pct": float((yearly.iloc[-1] / yearly.iloc[-2] - 1) * 100)
            if yearly.iloc[-2] else None,
        }
    valid = frame.loc[frame["has_valid_financials"]]
    # Spearman's rho is Pearson correlation over ranks. Calculating it directly
    # avoids adding SciPy for one statistic.
    spearman = valid["budget"].rank(method="average").corr(
        valid["gross"].rank(method="average")
    ) if len(valid) > 1 else None
    evidence["budget_gross_spearman"] = {
        "coefficient": float(spearman) if spearman is not None else None,
        "sample_size": len(valid),
    }
    breakout = frame.loc[frame["anomaly_category"].eq("Breakout success")]
    if not breakout.empty:
        evidence["highest_roi_breakout"] = _record(
            breakout.sort_values("roi_pct", ascending=False).iloc[0]
        )
    under = frame.loc[frame["anomaly_category"].eq("High-budget underperformer")]
    if not under.empty:
        evidence["largest_high_budget_underperformer"] = _record(
            under.sort_values("estimated_profit").iloc[0]
        )
    countries = grouped_metrics(frame, "country", GENERAL_MIN_GROUP_SIZE)
    if not countries.empty:
        evidence["highest_total_gross_country"] = _record(
            countries.sort_values("total_gross", ascending=False).iloc[0]
        )
    evidence["financial_coverage"] = {
        "valid_financial_count": int(frame["has_valid_financials"].sum()),
        "movie_count": int(len(frame)),
        "coverage_pct": float(frame["has_valid_financials"].mean() * 100) if len(frame) else 0,
    }
    return evidence


def selected_genre_company_evidence(frame: pd.DataFrame, genre: str | None) -> dict | None:
    if not genre:
        return None
    subset = frame.loc[frame["genre"].eq(genre)]
    companies = grouped_metrics(subset, "company", GENERAL_MIN_GROUP_SIZE)
    if companies.empty:
        return None
    return _record(companies.sort_values("total_gross", ascending=False).iloc[0], genre=genre)
