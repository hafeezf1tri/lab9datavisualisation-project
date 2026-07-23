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

# Nadhira's space-inspired visual system.
VENUS = "#BAD6EB"
GALAXY = "#081F5C"
UNIVERSE = "#7096D1"
PLANETARY = "#334EAC"
MILKY_WAY = "#FFF9F0"
SKY = "#D0E3FF"
METEOR = "#F7F2EB"

COLOR_SEQUENCE = [UNIVERSE, VENUS, PLANETARY, SKY, METEOR]
CONTINUOUS_SCALE = [PLANETARY, UNIVERSE, VENUS, SKY]
DIVERGING_SCALE = [PLANETARY, UNIVERSE, GALAXY, VENUS, SKY]
PLOTLY_TEMPLATE = {
    "layout": {
        "paper_bgcolor": GALAXY,
        "plot_bgcolor": GALAXY,
        "font": {"color": MILKY_WAY, "family": "Arial, sans-serif"},
        "title": {"font": {"color": MILKY_WAY}},
        "colorway": COLOR_SEQUENCE,
        "hoverlabel": {
            "bgcolor": GALAXY,
            "bordercolor": VENUS,
            "font": {"color": MILKY_WAY},
        },
        "legend": {
            "bgcolor": "rgba(8,31,92,0.72)",
            "bordercolor": UNIVERSE,
            "borderwidth": 1,
        },
        "xaxis": {
            "gridcolor": "rgba(112,150,209,0.28)",
            "linecolor": UNIVERSE,
            "zerolinecolor": VENUS,
        },
        "yaxis": {
            "gridcolor": "rgba(112,150,209,0.28)",
            "linecolor": UNIVERSE,
            "zerolinecolor": VENUS,
        },
        "geo": {
            "bgcolor": GALAXY,
            "landcolor": GALAXY,
            "lakecolor": GALAXY,
            "countrycolor": UNIVERSE,
            "coastlinecolor": VENUS,
        },
    }
}

APP_CSS = f"""
<style>
:root {{
    --primary: {VENUS};
    --background: {GALAXY};
    --accent: {UNIVERSE};
    --planetary: {PLANETARY};
    --foreground: {MILKY_WAY};
    --sky: {SKY};
    --meteor: {METEOR};
}}

[data-testid="stAppViewContainer"] {{
    background:
        radial-gradient(circle at 92% 8%, rgba(112, 150, 209, 0.18), transparent 27rem),
        linear-gradient(145deg, {GALAXY} 0%, {GALAXY} 72%, rgba(51, 78, 172, 0.72) 145%);
}}

[data-testid="stHeader"] {{
    background: rgba(8, 31, 92, 0.82);
}}

[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {GALAXY} 0%, {PLANETARY} 150%);
    border-right: 1px solid rgba(186, 214, 235, 0.42);
}}

[data-testid="stMetric"] {{
    background: linear-gradient(
        135deg,
        rgba(112, 150, 209, 0.18),
        rgba(51, 78, 172, 0.30)
    );
    border: 1px solid rgba(186, 214, 235, 0.58);
    border-radius: 0.85rem;
    padding: 1rem;
    box-shadow: 0 0.5rem 1.5rem rgba(8, 31, 92, 0.28);
}}

[data-testid="stMetricLabel"] {{
    color: {SKY};
}}

[data-testid="stMetricValue"] {{
    color: {MILKY_WAY};
}}

.stButton > button,
.stDownloadButton > button {{
    color: {MILKY_WAY};
    background: linear-gradient(110deg, {VENUS} -45%, {UNIVERSE} 48%, {PLANETARY} 112%);
    border: 1px solid {VENUS};
    border-radius: 0.65rem;
    font-weight: 650;
}}

.stButton > button:hover,
.stDownloadButton > button:hover {{
    color: {MILKY_WAY};
    border-color: {SKY};
    box-shadow: 0 0 0 0.16rem rgba(186, 214, 235, 0.22);
}}

a {{
    color: {VENUS};
}}

[data-baseweb="tab-highlight"] {{
    background-color: {VENUS};
}}

[data-testid="stCaptionContainer"],
.stCaption {{
    color: {SKY};
}}

[data-testid="stExpander"] {{
    border-color: rgba(112, 150, 209, 0.52);
    background: rgba(8, 31, 92, 0.22);
}}

hr {{
    border-color: rgba(112, 150, 209, 0.42);
}}
</style>
"""

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
