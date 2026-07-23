"""Prepare the Kaggle Movie Industry CSV for the dashboard."""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import CLEAN_DATA_PATH, EVIDENCE_PATH, PROCESSED_DIR, find_raw_data  # noqa: E402
from src.data_cleaning import SchemaValidationError, clean_movies  # noqa: E402
from src.data_quality import add_outlier_flags, build_quality_summary  # noqa: E402
from src.insights import generate_insight_evidence  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
LOGGER = logging.getLogger(__name__)


def _json_default(value):
    if hasattr(value, "item"):
        return value.item()
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if pd.isna(value):
        return None
    return str(value)


def prepare(raw_path: Path | None = None) -> tuple[Path, Path, Path]:
    raw_path = raw_path or find_raw_data()
    if not raw_path.exists():
        raise FileNotFoundError(
            "Movie data not found. Place movies.csv in data/raw/movies.csv "
            f"or at {ROOT / 'movies.csv'}."
        )
    LOGGER.info("Reading %s", raw_path)
    try:
        raw = pd.read_csv(raw_path)
    except pd.errors.EmptyDataError as exc:
        raise ValueError(f"The CSV is empty: {raw_path}") from exc
    result = clean_movies(raw)
    cleaned, outlier_counts = add_outlier_flags(result.data)
    quality = build_quality_summary(cleaned, result.audit, outlier_counts)
    evidence = generate_insight_evidence(cleaned)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    cleaned.to_parquet(CLEAN_DATA_PATH, index=False)
    quality_path = PROCESSED_DIR / "data_quality_summary.json"
    with quality_path.open("w", encoding="utf-8") as handle:
        json.dump(quality, handle, indent=2, default=_json_default, allow_nan=False)
    with EVIDENCE_PATH.open("w", encoding="utf-8") as handle:
        json.dump(evidence, handle, indent=2, default=_json_default, allow_nan=False)
    LOGGER.info(
        "Prepared %s rows (%s valid financial records)", len(cleaned),
        int(cleaned["has_valid_financials"].sum()),
    )
    return CLEAN_DATA_PATH, quality_path, EVIDENCE_PATH


if __name__ == "__main__":
    try:
        outputs = prepare()
        print("Created:")
        for output in outputs:
            print(f"  {output}")
    except (FileNotFoundError, ValueError, SchemaValidationError) as exc:
        LOGGER.error("%s", exc)
        raise SystemExit(1) from exc
