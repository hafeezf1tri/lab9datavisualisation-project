from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_CANDIDATES = (ROOT / "data" / "raw" / "movies.csv", ROOT / "movies.csv")
PROCESSED_DIR = ROOT / "data" / "processed"
CLEAN_DATA_PATH = PROCESSED_DIR / "movies_clean.parquet"
QUALITY_PATH = PROCESSED_DIR / "data_quality_summary.json"
EVIDENCE_PATH = PROCESSED_DIR / "insight_evidence.json"

REQUIRED_COLUMNS = {
    "name", "rating", "genre", "year", "released", "score", "votes",
    "director", "writer", "star", "country", "budget", "gross", "company",
    "runtime",
}
CATEGORY_COLUMNS = ["genre", "rating", "country", "company", "director", "writer", "star"]
NUMERIC_COLUMNS = ["budget", "gross", "score", "votes", "runtime", "year"]
GENERAL_MIN_GROUP_SIZE = 10
MESSAGE_MIN_GROUP_SIZE = 20
UNKNOWN = "Unknown"
PLOTLY_TEMPLATE = "plotly_white"
COLOR_SEQUENCE = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9", "#D55E00", "#F0E442"]

COUNTRY_OVERRIDES = {
    "United States": "USA", "United Kingdom": "GBR", "South Korea": "KOR",
    "West Germany": "DEU", "Soviet Union": "RUS", "Yugoslavia": "SRB",
    "Czechoslovakia": "CZE", "Hong Kong": "HKG", "Taiwan": "TWN",
    "Iran": "IRN", "Russia": "RUS", "Vietnam": "VNM", "Bolivia": "BOL",
}


def find_raw_data() -> Path:
    for path in RAW_DATA_CANDIDATES:
        if path.exists():
            return path
    return RAW_DATA_CANDIDATES[0]
