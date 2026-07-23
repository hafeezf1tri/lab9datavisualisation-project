import streamlit as st

from src.app_context import configure_page
from src.config import CLEAN_DATA_PATH, find_raw_data
from src.data_loader import load_movies, load_quality
from src.ui import render_caveats, render_quality_summary

configure_page("Home")

st.title("🎬 Movie Industry Financial Performance and Audience Reception Dashboard")
st.write(
    "A connected analytical tool for exploring historical financial outcomes, "
    "audience reception, categories, regions, and individual movies."
)

if not CLEAN_DATA_PATH.exists():
    raw = find_raw_data()
    if raw.exists():
        st.warning(
            f"Found `{raw.name}`, but the analytical files have not been prepared yet."
        )
        st.code("python scripts/prepare_data.py\nstreamlit run app.py", language="powershell")
    else:
        st.error(
            "Movie data is missing. Download the Kaggle Movie Industry CSV and place it "
            "at `movies.csv` or `data/raw/movies.csv`, then run the preparation command."
        )
    st.stop()

data = load_movies()
quality = load_quality()
valid_date = data["released_date"].dropna()
update = (
    valid_date.max().strftime("%d %B %Y")
    if not valid_date.empty
    else str(int(data["release_year"].max()))
)
st.success(
    f"Ready: {len(data):,} cleaned movies, covering "
    f"{int(data['release_year'].min())}–{int(data['release_year'].max())}. "
    f"Latest release represented: {update}."
)

st.subheader("Choose an analytical view")
cols = st.columns(3)
cols[0].page_link("pages/1_Executive_Overview.py", label="Executive Overview", icon="📈")
cols[0].write("KPIs, annual performance, genre comparisons, risks and opportunities.")
cols[1].page_link("pages/2_Exploratory_Analysis.py", label="Exploratory Analysis", icon="🔎")
cols[1].write("Relationships, distributions, heatmap, map, small multiples, and treemap.")
cols[2].page_link("pages/3_Detailed_Investigation.py", label="Detailed Investigation", icon="🎞️")
cols[2].write("Genre → company → director → movie drill-down and benchmarks.")

render_quality_summary(quality)
render_caveats()

with st.expander("Business context and stakeholders"):
    st.markdown(
        """
This dashboard supports studio executives, producers, distribution managers, and
industry analysts who need to compare historical segments, investigate unusual
films, and move from industry-level patterns to individual records.

It is descriptive evidence for production-planning research. It does not predict
future success, and its historical associations should not be interpreted causally.
"""
    )
