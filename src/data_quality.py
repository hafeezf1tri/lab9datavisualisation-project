from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd

OUTLIER_COLUMNS = ["budget", "gross", "estimated_profit", "roi_pct", "runtime", "votes"]


def add_outlier_flags(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    df = frame.copy()
    counts: dict[str, int] = {}
    for col in OUTLIER_COLUMNS:
        valid = df[col].dropna()
        flag = pd.Series(False, index=df.index)
        if len(valid) >= 4:
            q1, q3 = valid.quantile([0.25, 0.75])
            iqr = q3 - q1
            if iqr > 0:
                flag = df[col].lt(q1 - 1.5 * iqr) | df[col].gt(q3 + 1.5 * iqr)
        key = f"{col}_outlier"
        df[key] = flag.fillna(False)
        counts[col] = int(df[key].sum())
    return df, counts


def build_quality_summary(
    frame: pd.DataFrame, audit: dict[str, Any], outlier_counts: dict[str, int]
) -> dict[str, Any]:
    missing = {}
    for col in frame.columns:
        count = int(frame[col].isna().sum())
        missing[col] = {
            "count": count,
            "percentage": round(count / len(frame) * 100, 2) if len(frame) else 0.0,
        }
    years = frame["release_year"].dropna()
    return {
        **audit,
        "suspected_duplicate_count": int(frame["suspected_duplicate"].sum()),
        "missing_by_column": missing,
        "failed_date_parses": int(frame["date_parse_failed"].sum()),
        "valid_budget_count": int(frame["has_valid_budget"].sum()),
        "valid_gross_count": int(frame["has_valid_gross"].sum()),
        "valid_budget_and_gross_count": int(frame["has_valid_financials"].sum()),
        "outlier_count_by_measure": outlier_counts,
        "minimum_release_year": int(years.min()) if not years.empty else None,
        "maximum_release_year": int(years.max()) if not years.empty else None,
        "preparation_timestamp": datetime.now(timezone.utc).isoformat(),
    }
