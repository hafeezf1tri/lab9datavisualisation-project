import streamlit as st

from src.app_context import configure_page, get_context, selection_scope
from src.charts import (
    budget_gross_scatter,
    country_map,
    genre_decade_heatmap,
    performance_treemap,
    roi_box,
    small_multiples,
)
from src.state import custom_value, selection_points, set_selection
from src.ui import render_caveats

configure_page("Exploratory Analysis")
st.title("Exploratory Analysis")
st.write("Investigate financial relationships, distributions, geography, time, and hierarchy.")
ctx = get_context()
if ctx is None:
    st.stop()
if ctx.filtered.empty:
    st.warning("No movies match the active filters and selections.")
    st.stop()

tab_relationship, tab_patterns, tab_hierarchy = st.tabs(
    ["Relationship & distribution", "Time & geography", "Hierarchy & records"]
)

with tab_relationship:
    scatter_scope = selection_scope(ctx, {"selected_movie_id"})
    event = st.plotly_chart(
        budget_gross_scatter(scatter_scope), width="stretch",
        key="explore_scatter", on_select="rerun",
        selection_mode=("points", "box", "lasso"), config={"displaylogo": False},
    )
    points = selection_points(event)
    if points:
        ids = [custom_value(point, 0) for point in points if custom_value(point, 0)]
        if ids and ids != st.session_state.get("brushed_movie_ids"):
            st.session_state["brushed_movie_ids"] = ids
            if len(ids) == 1:
                set_selection("selected_movie_id", ids[0], clear_children=False)
            st.rerun()
    elif st.button("Clear brushed points"):
        st.session_state["brushed_movie_ids"] = []
        st.session_state["selected_movie_id"] = None
        st.rerun()

    include_extremes = st.toggle("Include extreme ROI outliers", value=False)
    st.plotly_chart(
        roi_box(scatter_scope, include_extremes), width="stretch",
        config={"displaylogo": False},
    )
    if not include_extremes:
        st.caption(
            "Display values are capped at the 1st and 99th percentiles for readability; "
            "raw ROI values remain unchanged in the data and export."
        )

with tab_patterns:
    heat_metric = st.selectbox(
        "Heatmap metric",
        ["median_roi", "total_gross", "median_gross", "movie_count", "profitable_rate"],
        format_func=lambda x: x.replace("_", " ").title(),
    )
    heat_event = st.altair_chart(
        genre_decade_heatmap(ctx.filtered, heat_metric), width="stretch",
        key="genre_decade_heatmap", on_select="rerun",
    )
    try:
        heat_selection = heat_event.selection.get("heat_select", {})
        picked_genres = heat_selection.get("genre", [])
        picked_decades = heat_selection.get("decade", [])
        heat_changed = False
        if picked_genres:
            heat_changed = set_selection("selected_genre", picked_genres[0])
        if picked_decades:
            start = int(str(picked_decades[0])[:4])
            new_range = (
                max(start, int(ctx.all_data["release_year"].min())),
                min(start + 9, int(ctx.all_data["release_year"].max())),
            )
            if tuple(st.session_state.get("filter_year_range", ())) != new_range:
                st.session_state["filter_year_range"] = new_range
                heat_changed = True
        if heat_changed:
            st.rerun()
    except (AttributeError, KeyError, TypeError, ValueError):
        pass
    h1, h2 = st.columns(2)
    genre_pick = h1.selectbox(
        "Heatmap genre selection (fallback)", ["Keep current", *sorted(ctx.base["genre"].unique())]
    )
    decades = sorted(ctx.base["release_decade"].dropna().astype(int).unique())
    decade_pick = h2.selectbox(
        "Heatmap decade selection (fallback)", ["Keep current", *[f"{x}s" for x in decades]]
    )
    if st.button("Apply heatmap selection"):
        if genre_pick != "Keep current":
            set_selection("selected_genre", genre_pick)
        if decade_pick != "Keep current":
            start = int(decade_pick[:4])
            st.session_state["filter_year_range"] = (
                max(start, int(ctx.all_data["release_year"].min())),
                min(start + 9, int(ctx.all_data["release_year"].max())),
            )
        st.rerun()

    map_metric = st.selectbox(
        "Map metric", ["total_gross", "movie_count", "median_roi", "average_score"],
        format_func=lambda x: x.replace("_", " ").title(),
    )
    map_scope = selection_scope(ctx, {"selected_country", "selected_movie_id"})
    map_event = st.plotly_chart(
        country_map(map_scope, map_metric), width="stretch",
        key="country_map", on_select="rerun", selection_mode="points",
        config={"displaylogo": False},
    )
    map_points = selection_points(map_event)
    if map_points:
        country = custom_value(map_points[0], 0)
        if country and set_selection("selected_country", country, clear_children=False):
            st.rerun()
    country_options = sorted(map_scope["country"].unique())
    current_country = ctx.selections.get("selected_country")
    country_pick = st.selectbox(
        "Select country (event fallback)", ["All countries", *country_options],
        index=country_options.index(current_country) + 1 if current_country in country_options else 0,
    )
    new_country = None if country_pick == "All countries" else country_pick
    if new_country != current_country:
        set_selection("selected_country", new_country, clear_children=False)
        st.rerun()

    small_metric = st.selectbox(
        "Small-multiple metric", ["total_gross", "movie_count", "median_roi"],
        format_func=lambda x: x.replace("_", " ").title(),
    )
    st.altair_chart(small_multiples(ctx.filtered, small_metric), width="stretch")

with tab_hierarchy:
    tree_scope = selection_scope(ctx, {"selected_movie_id"})
    tree_event = st.plotly_chart(
        performance_treemap(tree_scope), width="stretch",
        key="performance_treemap", on_select="rerun", selection_mode="points",
        config={"displaylogo": False},
    )
    tree_points = selection_points(tree_event)
    if tree_points:
        point = tree_points[0]
        path = str(point.get("id", "")).split("/")
        if len(path) == 1 and path[0]:
            changed = set_selection("selected_genre", path[0])
        elif len(path) == 2:
            changed = set_selection("selected_genre", path[0])
            changed = set_selection("selected_company", path[1]) or changed
        elif len(path) >= 3:
            match = tree_scope.loc[
                tree_scope["genre"].eq(path[0])
                & tree_scope["company"].eq(path[1])
                & tree_scope["name"].eq(path[-1])
            ]
            changed = (
                set_selection("selected_movie_id", match.iloc[0]["movie_id"], clear_children=False)
                if not match.empty else False
            )
        else:
            changed = False
        if changed:
            st.rerun()
    st.caption(
        "Treemap size is gross and colour is ROI. Use the linked controls below when a "
        "browser does not expose treemap click events."
    )
    query = st.text_input("Search movie title").strip()
    table_scope = tree_scope
    brushed = st.session_state.get("brushed_movie_ids", [])
    if brushed:
        table_scope = table_scope.loc[table_scope["movie_id"].isin(brushed)]
        st.info(f"Showing {len(table_scope):,} brushed movies.")
    if query:
        table_scope = table_scope.loc[
            table_scope["name"].str.contains(query, case=False, na=False, regex=False)
        ]
    columns = [
        "name", "release_year", "genre", "company", "country", "director", "budget",
        "gross", "estimated_profit", "roi_pct", "score", "votes", "runtime",
        "anomaly_category", "movie_id",
    ]
    display = table_scope[columns].sort_values("gross", ascending=False)
    st.dataframe(
        display, width="stretch", hide_index=True, height=440,
        column_config={"movie_id": None, "budget": st.column_config.NumberColumn(format="$%.0f"),
                       "gross": st.column_config.NumberColumn(format="$%.0f"),
                       "estimated_profit": st.column_config.NumberColumn(format="$%.0f"),
                       "roi_pct": st.column_config.NumberColumn(format="%.1f%%")},
    )
    st.download_button(
        "Download visible records (CSV)", display.to_csv(index=False).encode("utf-8"),
        file_name="movie_industry_filtered.csv", mime="text/csv",
    )
    movie_options = dict(zip(display["name"] + " (" + display["release_year"].astype(str) + ")", display["movie_id"]))
    selected_label = st.selectbox("Select movie for detail", ["None", *movie_options.keys()])
    chosen = movie_options.get(selected_label)
    if chosen and chosen != ctx.selections.get("selected_movie_id"):
        set_selection("selected_movie_id", chosen, clear_children=False)
        st.rerun()

render_caveats()
