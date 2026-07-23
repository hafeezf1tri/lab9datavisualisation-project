import streamlit as st

from src.app_context import configure_page, get_context, selection_scope
from src.charts import annual_trend, genre_bar
from src.insights import generate_insight_evidence
from src.metrics import calculate_kpis, grouped_metrics
from src.state import custom_value, selection_points, set_selection
from src.ui import compact_number, render_caveats, render_kpis, render_quality_summary

configure_page("Executive Overview")
st.title("Executive Overview")
st.write(
    "Monitor historical performance and identify segments that warrant deeper investigation."
)
ctx = get_context()
if ctx is None:
    st.stop()
if ctx.filtered.empty:
    st.warning("No movies match the active filters and selections. Reset or broaden the scope.")
    st.stop()

render_kpis(calculate_kpis(ctx.filtered))

message_data = selection_scope(ctx, {"selected_genre", "selected_company", "selected_director", "selected_movie_id"})
genres = grouped_metrics(message_data, "genre")
eligible = genres.loc[genres["valid_financial_count"].ge(20)].dropna(subset=["median_roi", "loss_rate"])
if not eligible.empty:
    opportunity = eligible.nlargest(1, "median_roi").iloc[0]
    warning = eligible.nlargest(1, "loss_rate").iloc[0]
    col1, col2 = st.columns(2)
    col1.success(
        f"Opportunity to investigate: **{opportunity['genre']}** has the highest median ROI "
        f"({opportunity['median_roi']:.1f}%) among {int(opportunity['valid_financial_count'])} "
        "financially complete films in scope."
    )
    col2.warning(
        f"Risk to investigate: **{warning['genre']}** has the highest loss-making rate "
        f"({warning['loss_rate']:.1f}%) among {int(warning['valid_financial_count'])} "
        "financially complete films in scope."
    )

trend_metric = st.selectbox(
    "Annual trend metric",
    ["total_gross", "estimated_profit", "movie_count", "median_roi"],
    format_func=lambda x: x.replace("_", " ").title(),
)
st.plotly_chart(
    annual_trend(ctx.filtered, trend_metric), width="stretch",
    config={"displaylogo": False},
)

left, right = st.columns([3, 1])
bar_metric = left.selectbox(
    "Genre comparison metric",
    ["total_gross", "estimated_profit", "median_roi", "profitable_rate", "movie_count"],
    format_func=lambda x: x.replace("_", " ").title(),
)
genre_options = sorted(message_data["genre"].unique())
fallback = right.selectbox(
    "Select genre (event fallback)", ["All genres", *genre_options],
    index=(genre_options.index(ctx.selections["selected_genre"]) + 1)
    if ctx.selections["selected_genre"] in genre_options else 0,
)
fallback_value = None if fallback == "All genres" else fallback
if fallback_value != ctx.selections["selected_genre"]:
    set_selection("selected_genre", fallback_value)
    st.rerun()

event = st.plotly_chart(
    genre_bar(message_data, bar_metric, ctx.selections["selected_genre"]),
    width="stretch", key="overview_genre_bar", on_select="rerun",
    selection_mode="points", config={"displaylogo": False},
)
points = selection_points(event)
if points:
    value = custom_value(points[0], 0) or points[0].get("y")
    if value and set_selection("selected_genre", value):
        st.rerun()

with st.expander("Evidence-based insights"):
    evidence = generate_insight_evidence(ctx.filtered)
    gross = evidence.get("highest_total_gross_genre")
    if gross:
        st.write(
            f"• {gross['genre']} contributes {gross['contribution_pct']:.1f}% of gross "
            f"in the visible scope ({compact_number(gross['total_gross'], True)})."
        )
    selected_genre = ctx.selections.get("selected_genre")
    company = evidence.get("highest_gross_company_by_genre", {}).get(selected_genre)
    if company:
        st.write(
            f"• Within {selected_genre}, {company['company']} has the highest total gross "
            f"({compact_number(company['total_gross'], True)}) in the visible scope."
        )
    corr = evidence.get("budget_gross_spearman", {})
    if corr.get("coefficient") is not None:
        st.write(
            f"• Budget and gross have a Spearman correlation of "
            f"{corr['coefficient']:.3f} across {corr['sample_size']:,} valid films. "
            "This is an association, not evidence of causation."
        )
    coverage = evidence.get("financial_coverage", {})
    st.write(
        f"• Financial calculations cover {coverage.get('valid_financial_count', 0):,} of "
        f"{coverage.get('movie_count', 0):,} visible movies "
        f"({coverage.get('coverage_pct', 0):.1f}%)."
    )

render_quality_summary(ctx.quality)
render_caveats()
