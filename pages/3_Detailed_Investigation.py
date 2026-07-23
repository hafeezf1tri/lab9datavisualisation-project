import pandas as pd
import streamlit as st

from src.app_context import configure_page, get_context
from src.charts import company_ranking, movie_comparison
from src.filters import apply_filters
from src.metrics import benchmark_summary, calculate_kpis, grouped_metrics
from src.state import custom_value, selection_points, set_selection
from src.ui import format_pct, render_caveats, render_kpis

configure_page("Detailed Investigation")
st.title("Detailed Investigation")
st.write("Drill from genre to company to director to movie, with parent and overall benchmarks.")
ctx = get_context()
if ctx is None:
    st.stop()

genre_options = sorted(ctx.base["genre"].unique())
gcol, ccol, dcol, mcol = st.columns(4)
genre = gcol.selectbox(
    "1 · Genre", ["All genres", *genre_options],
    index=genre_options.index(ctx.selections["selected_genre"]) + 1
    if ctx.selections["selected_genre"] in genre_options else 0,
)
genre_value = None if genre == "All genres" else genre
if genre_value != ctx.selections["selected_genre"]:
    set_selection("selected_genre", genre_value)
    st.rerun()

genre_scope = apply_filters(
    ctx.all_data, ctx.filters,
    {**ctx.selections, "selected_genre": genre_value, "selected_company": None,
     "selected_director": None, "selected_movie_id": None},
)
company_options = sorted(genre_scope["company"].unique())
company = ccol.selectbox(
    "2 · Production company", ["All companies", *company_options],
    index=company_options.index(ctx.selections["selected_company"]) + 1
    if ctx.selections["selected_company"] in company_options else 0,
)
company_value = None if company == "All companies" else company
if company_value != ctx.selections["selected_company"]:
    set_selection("selected_company", company_value)
    st.rerun()

company_scope = genre_scope if not company_value else genre_scope.loc[genre_scope["company"].eq(company_value)]
director_options = sorted(company_scope["director"].unique())
director = dcol.selectbox(
    "3 · Director", ["All directors", *director_options],
    index=director_options.index(ctx.selections["selected_director"]) + 1
    if ctx.selections["selected_director"] in director_options else 0,
)
director_value = None if director == "All directors" else director
if director_value != ctx.selections["selected_director"]:
    set_selection("selected_director", director_value)
    st.rerun()

director_scope = company_scope if not director_value else company_scope.loc[
    company_scope["director"].eq(director_value)
]
movie_labels = {
    f"{row['name']} ({int(row['release_year']) if pd.notna(row['release_year']) else '?'})": row["movie_id"]
    for _, row in director_scope.sort_values("name").iterrows()
}
selected_movie = ctx.selections["selected_movie_id"]
selected_movie_label = next((k for k, v in movie_labels.items() if v == selected_movie), None)
movie = mcol.selectbox(
    "4 · Movie", ["All movies", *movie_labels],
    index=list(movie_labels).index(selected_movie_label) + 1 if selected_movie_label else 0,
)
movie_value = movie_labels.get(movie)
if movie_value != selected_movie:
    set_selection("selected_movie_id", movie_value, clear_children=False)
    st.rerun()

current = director_scope
level = "Genre"
parent = ctx.base
if genre_value:
    current = genre_scope
    level = genre_value
if company_value:
    parent, current, level = genre_scope, company_scope, company_value
if director_value:
    parent, current, level = company_scope, director_scope, director_value
if movie_value:
    parent = director_scope
    current = director_scope.loc[director_scope["movie_id"].eq(movie_value)]
    level = current.iloc[0]["name"] if not current.empty else "Movie"

st.caption(
    " › ".join(x for x in [genre_value, company_value, director_value,
                            level if movie_value else None] if x)
    or "All genres"
)
if current.empty:
    st.warning("No records are available at this drill level.")
    st.stop()

render_kpis(calculate_kpis(current))
summary = benchmark_summary(current, parent, ctx.all_data)
rows = []
for label, values in summary.items():
    rows.append({
        "Scope": label.title(), "Movies": values["movie_count"],
        "Valid financials": values["valid_financial_count"],
        "Total gross": values["total_gross"], "Median budget": values["median_budget"],
        "Median ROI (%)": values["median_roi"],
        "Profitable rate (%)": values["profitable_rate"],
        "Average score": values["average_score"],
    })
st.subheader(f"Benchmark: {level}")
st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

if genre_value:
    ranking_scope = genre_scope
    event = st.plotly_chart(
        company_ranking(ranking_scope, company_value), width="stretch",
        key="detail_company_ranking", on_select="rerun", selection_mode="points",
        config={"displaylogo": False},
    )
    points = selection_points(event)
    if points:
        selected_company = custom_value(points[0], 0) or points[0].get("y")
        if selected_company and set_selection("selected_company", selected_company):
            st.rerun()

if director_value:
    director_metrics = grouped_metrics(genre_scope, "director", minimum=1)
    selected_row = director_metrics.loc[director_metrics["director"].eq(director_value)]
    genre_roi = genre_scope["roi_pct"].median()
    if not selected_row.empty and pd.notna(selected_row.iloc[0]["median_roi"]):
        diff = selected_row.iloc[0]["median_roi"] - genre_roi
        st.info(
            f"{director_value}'s median ROI is {format_pct(diff)} versus the "
            f"{genre_value} median (descriptive historical comparison)."
        )

financial = current.loc[current["has_valid_financials"]]
if not financial.empty and not movie_value:
    left, right = st.columns(2)
    left.subheader("Top movies by ROI")
    left.dataframe(
        financial.nlargest(5, "roi_pct")[["name", "release_year", "roi_pct", "gross"]],
        hide_index=True, width="stretch",
    )
    right.subheader("Bottom movies by ROI")
    right.dataframe(
        financial.nsmallest(5, "roi_pct")[["name", "release_year", "roi_pct", "gross"]],
        hide_index=True, width="stretch",
    )

if movie_value and not current.empty:
    row = current.iloc[0]
    st.plotly_chart(movie_comparison(ctx.all_data, movie_value), width="stretch")
    st.subheader("Movie details on demand")
    genre_median = ctx.all_data.loc[ctx.all_data["genre"].eq(row["genre"]), "roi_pct"].median()
    detail_cols = [
        "name", "release_year", "released_date", "rating", "genre", "country", "company",
        "director", "writer", "star", "runtime", "score", "votes", "budget", "gross",
        "estimated_profit", "roi_pct", "gross_budget_ratio", "budget_band", "score_band",
        "performance_category", "anomaly_category", "has_valid_financials",
    ]
    detail = {key: row.get(key) for key in detail_cols}
    detail["difference_from_genre_median_roi"] = (
        row["roi_pct"] - genre_median if pd.notna(row["roi_pct"]) and pd.notna(genre_median) else None
    )
    st.json(detail, expanded=True)
    st.warning("Estimated profit is a simplified analytical measure, not actual net profit.")

render_caveats()
