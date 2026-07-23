from __future__ import annotations

import math
from typing import Any

import pandas as pd

from src.config import GENERAL_MIN_GROUP_SIZE


def _safe_float(value: object) -> float | None:
    try:
        number = float(value)
        return None if math.isnan(number) else number
    except (TypeError, ValueError):
        return None


def calculate_kpis(frame: pd.DataFrame) -> dict[str, Any]:
    financial = frame.loc[frame["has_valid_financials"]]
    gross = frame["gross"].dropna()
    years = sorted(frame["release_year"].dropna().astype(int).unique())
    yoy = None
    if len(years) >= 2:
        latest, previous = years[-1], years[-2]
        latest_total = frame.loc[frame["release_year"].eq(latest), "gross"].sum(min_count=1)
        previous_total = frame.loc[frame["release_year"].eq(previous), "gross"].sum(min_count=1)
        if pd.notna(latest_total) and pd.notna(previous_total) and previous_total:
            yoy = (latest_total / previous_total - 1) * 100
    return {
        "total_gross": _safe_float(gross.sum(min_count=1)),
        "estimated_profit": _safe_float(financial["estimated_profit"].sum(min_count=1)),
        "median_budget": _safe_float(frame["budget"].median()),
        "median_roi": _safe_float(financial["roi_pct"].median()),
        "profitable_rate": _safe_float(financial["is_profitable"].mean() * 100),
        "average_score": _safe_float(frame["score"].mean()),
        "movie_count": int(len(frame)),
        "valid_financial_count": int(len(financial)),
        "gross_yoy_pct": _safe_float(yoy),
    }


def grouped_metrics(
    frame: pd.DataFrame, group: str, minimum: int = GENERAL_MIN_GROUP_SIZE
) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    result = (
        frame.groupby(group, dropna=False, observed=True)
        .agg(
            movie_count=("movie_id", "nunique"),
            valid_financial_count=("has_valid_financials", "sum"),
            total_gross=("gross", "sum"),
            estimated_profit=("estimated_profit", "sum"),
            median_roi=("roi_pct", "median"),
            median_gross=("gross", "median"),
            median_budget=("budget", "median"),
            average_score=("score", "mean"),
            profitable_rate=("is_profitable", "mean"),
        )
        .reset_index()
    )
    result["profitable_rate"] *= 100
    result["loss_rate"] = 100 - result["profitable_rate"]
    insufficient = result["valid_financial_count"].lt(minimum)
    result.loc[insufficient, ["median_roi", "profitable_rate", "loss_rate"]] = pd.NA
    return result


def benchmark_summary(
    selected: pd.DataFrame, parent: pd.DataFrame, overall: pd.DataFrame
) -> dict[str, dict[str, Any]]:
    return {
        "selected": calculate_kpis(selected),
        "parent": calculate_kpis(parent),
        "overall": calculate_kpis(overall),
    }
