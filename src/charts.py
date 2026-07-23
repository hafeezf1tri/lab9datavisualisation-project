from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pycountry

from src.config import (
    COLOR_SEQUENCE,
    CONTINUOUS_SCALE,
    COUNTRY_OVERRIDES,
    DIVERGING_SCALE,
    GALAXY,
    GENERAL_MIN_GROUP_SIZE,
    MILKY_WAY,
    PLOTLY_TEMPLATE,
    SKY,
    UNIVERSE,
    VENUS,
)
from src.metrics import grouped_metrics


def annual_trend(frame: pd.DataFrame, metric: str) -> go.Figure:
    labels = {
        "total_gross": "Total gross", "estimated_profit": "Estimated profit",
        "movie_count": "Movie count", "median_roi": "Median ROI",
    }
    grouped = frame.groupby("release_year", observed=True).agg(
        total_gross=("gross", "sum"), estimated_profit=("estimated_profit", "sum"),
        movie_count=("movie_id", "nunique"), median_roi=("roi_pct", "median"),
        valid_financial_count=("has_valid_financials", "sum"),
    ).reset_index()
    fig = px.line(
        grouped, x="release_year", y=metric, markers=True,
        hover_data={"movie_count": True, "valid_financial_count": True},
        labels={"release_year": "Release year", metric: labels[metric]},
        color_discrete_sequence=[COLOR_SEQUENCE[0]], template=PLOTLY_TEMPLATE,
    )
    fig.update_layout(title=f"Annual {labels[metric].lower()}", hovermode="x unified")
    return fig


def genre_bar(frame: pd.DataFrame, metric: str, selected: str | None = None) -> go.Figure:
    data = grouped_metrics(frame, "genre").dropna(subset=[metric]).sort_values(metric)
    colors = [COLOR_SEQUENCE[1] if g == selected else COLOR_SEQUENCE[0] for g in data["genre"]]
    fig = go.Figure(go.Bar(
        x=data[metric], y=data["genre"], orientation="h", marker_color=colors,
        customdata=np.stack([data["genre"], data["movie_count"], data["valid_financial_count"]], axis=-1)
        if len(data) else None,
        hovertemplate="%{y}<br>Value: %{x:,.2f}<br>Movies: %{customdata[1]:,.0f}"
        "<br>Valid financials: %{customdata[2]:,.0f}<extra></extra>",
    ))
    fig.update_layout(template=PLOTLY_TEMPLATE, title="Genre comparison", xaxis_title=metric.replace("_", " ").title())
    return fig


def budget_gross_scatter(frame: pd.DataFrame) -> go.Figure:
    data = frame.loc[frame["has_valid_financials"]].copy()
    fig = px.scatter(
        data, x="budget", y="gross", color="genre", size="votes",
        size_max=28, log_x=True, log_y=True, render_mode="webgl",
        custom_data=["movie_id", "name", "company", "estimated_profit", "roi_pct", "score", "votes"],
        color_discrete_sequence=COLOR_SEQUENCE, template=PLOTLY_TEMPLATE,
        labels={"budget": "Budget (USD, log)", "gross": "Gross (USD, log)"},
    )
    fig.update_traces(
        hovertemplate="<b>%{customdata[1]}</b><br>Budget: $%{x:,.0f}<br>Gross: $%{y:,.0f}"
        "<br>Company: %{customdata[2]}<br>Estimated profit: $%{customdata[3]:,.0f}"
        "<br>ROI: %{customdata[4]:,.1f}%<br>Score: %{customdata[5]:.1f}"
        "<br>Votes: %{customdata[6]:,.0f}<extra></extra>"
    )
    fig.update_layout(title="Budget versus gross (box/lasso points to filter detail)")
    return fig


def roi_box(frame: pd.DataFrame, include_extremes: bool) -> go.Figure:
    valid_counts = frame.groupby("genre")["roi_pct"].count()
    allowed = valid_counts[valid_counts.ge(GENERAL_MIN_GROUP_SIZE)].index
    data = frame.loc[frame["genre"].isin(allowed) & frame["roi_pct"].notna()].copy()
    if not include_extremes and not data.empty:
        low, high = data["roi_pct"].quantile([0.01, 0.99])
        data["display_roi"] = data["roi_pct"].clip(low, high)
    else:
        data["display_roi"] = data["roi_pct"]
    order = data.groupby("genre")["roi_pct"].median().sort_values().index.tolist()
    return px.box(
        data, x="genre", y="display_roi", category_orders={"genre": order},
        custom_data=["name", "roi_pct", "movie_id"], points="outliers" if include_extremes else False,
        color="genre", color_discrete_sequence=COLOR_SEQUENCE, template=PLOTLY_TEMPLATE,
        labels={"display_roi": "ROI (%)", "genre": "Genre"},
        title="ROI distribution by genre",
    )


def genre_decade_heatmap(frame: pd.DataFrame, metric: str):
    import altair as alt

    agg_names = {
        "median_roi": ("roi_pct", "median"), "total_gross": ("gross", "sum"),
        "median_gross": ("gross", "median"), "movie_count": ("movie_id", "nunique"),
        "profitable_rate": ("is_profitable", "mean"),
    }
    value_col, agg = agg_names[metric]
    data = frame.dropna(subset=["release_decade"]).groupby(
        ["genre", "release_decade"], observed=True
    ).agg(value=(value_col, agg), sample_size=("movie_id", "nunique"),
          valid_financial_count=("has_valid_financials", "sum")).reset_index()
    if metric == "profitable_rate":
        data["value"] *= 100
    if metric in ("median_roi", "profitable_rate"):
        data.loc[data["valid_financial_count"].lt(GENERAL_MIN_GROUP_SIZE), "value"] = np.nan
    data["decade"] = data["release_decade"].astype(int).astype(str) + "s"
    selection = alt.selection_point(fields=["genre", "decade"], name="heat_select")
    chart = (
        alt.Chart(data)
        .mark_rect()
        .encode(
            x=alt.X("decade:N", title="Release decade"),
            y=alt.Y("genre:N", title="Genre"),
            color=alt.Color(
                "value:Q",
                scale=alt.Scale(range=CONTINUOUS_SCALE),
                title=metric.replace("_", " "),
            ),
            tooltip=[
                "genre:N",
                "decade:N",
                alt.Tooltip("value:Q", format=",.2f"),
                "sample_size:Q",
                "valid_financial_count:Q",
            ],
            opacity=alt.condition(selection, alt.value(1.0), alt.value(0.72)),
        )
        .add_params(selection)
        .properties(title="Genre by decade heatmap", height=max(280, data["genre"].nunique() * 24))
    )
    return _style_altair(chart)


def country_iso(name: str) -> str | None:
    if name in COUNTRY_OVERRIDES:
        return COUNTRY_OVERRIDES[name]
    try:
        return pycountry.countries.lookup(name).alpha_3
    except LookupError:
        return None


def country_map(frame: pd.DataFrame, metric: str) -> go.Figure:
    data = grouped_metrics(frame, "country")
    data["iso3"] = data["country"].map(country_iso)
    data = data.dropna(subset=["iso3", metric])
    fig = px.choropleth(
        data, locations="iso3", color=metric, hover_name="country",
        custom_data=["country", "movie_count", "valid_financial_count"],
        color_continuous_scale=CONTINUOUS_SCALE, template=PLOTLY_TEMPLATE,
        title="Production country", labels={metric: metric.replace("_", " ").title()},
    )
    fig.update_traces(
        hovertemplate="<b>%{customdata[0]}</b><br>Value: %{z:,.2f}"
        "<br>Movies: %{customdata[1]:,.0f}<br>Valid financials: %{customdata[2]:,.0f}<extra></extra>"
    )
    return fig


def small_multiples(frame: pd.DataFrame, metric: str):
    import altair as alt

    top = frame.groupby("genre")["movie_id"].nunique().nlargest(6).index
    data = frame.loc[frame["genre"].isin(top)].groupby(
        ["genre", "release_year"], observed=True
    ).agg(
        total_gross=("gross", "sum"), movie_count=("movie_id", "nunique"),
        median_roi=("roi_pct", "median"), valid_financial_count=("has_valid_financials", "sum"),
    ).reset_index()
    if metric == "median_roi":
        data.loc[data["valid_financial_count"].lt(GENERAL_MIN_GROUP_SIZE), metric] = np.nan
    chart = (
        alt.Chart(data)
        .mark_line(
            color=VENUS,
            point={"filled": True, "fill": SKY, "stroke": UNIVERSE},
        )
        .encode(
            x=alt.X("release_year:Q", title="Year"),
            y=alt.Y(f"{metric}:Q", title=metric.replace("_", " ")),
            tooltip=["genre:N", "release_year:Q", alt.Tooltip(f"{metric}:Q", format=",.2f"), "movie_count:Q"],
        )
        .facet("genre:N", columns=3, title="Top-six genre trends")
        .resolve_scale(y="shared")
    )
    return _style_altair(chart)


def performance_treemap(frame: pd.DataFrame) -> go.Figure:
    data = frame.loc[frame["gross"].notna() & frame["genre"].ne("Unknown") & frame["company"].ne("Unknown")].copy()
    return px.treemap(
        data, path=["genre", "company", "name"], values="gross", color="roi_pct",
        color_continuous_scale=DIVERGING_SCALE, color_continuous_midpoint=0,
        custom_data=["movie_id", "genre", "company", "name"],
        template=PLOTLY_TEMPLATE, title="Gross hierarchy: genre → company → movie",
    )


def company_ranking(frame: pd.DataFrame, selected: str | None = None) -> go.Figure:
    data = grouped_metrics(frame, "company").dropna(subset=["median_roi"])
    data = data.nlargest(20, "total_gross").sort_values("total_gross")
    colors = [COLOR_SEQUENCE[1] if x == selected else COLOR_SEQUENCE[0] for x in data["company"]]
    fig = go.Figure(go.Bar(
        x=data["total_gross"], y=data["company"], orientation="h", marker_color=colors,
        customdata=np.stack([data["company"], data["movie_count"], data["median_roi"]], axis=-1)
        if len(data) else None,
        hovertemplate="%{y}<br>Total gross: $%{x:,.0f}<br>Movies: %{customdata[1]}"
        "<br>Median ROI: %{customdata[2]:.1f}%<extra></extra>",
    ))
    fig.update_layout(template=PLOTLY_TEMPLATE, title="Companies in current scope", height=550)
    return fig


def movie_comparison(frame: pd.DataFrame, movie_id: str) -> go.Figure:
    movie = frame.loc[frame["movie_id"].eq(movie_id)].iloc[0]
    genre = frame.loc[frame["genre"].eq(movie["genre"])]
    measures = ["budget", "gross", "roi_pct", "score"]
    rows = []
    for measure in measures:
        values = genre[measure].dropna()
        percentile = (
            float(values.le(movie[measure]).mean() * 100)
            if pd.notna(movie[measure]) and not values.empty
            else np.nan
        )
        rows.append({"measure": measure, "value": percentile, "comparison": movie["name"]})
        rows.append({"measure": measure, "value": 50.0, "comparison": f"{movie['genre']} median"})
    return px.bar(
        pd.DataFrame(rows), x="measure", y="value", color="comparison", barmode="group",
        color_discrete_sequence=COLOR_SEQUENCE, template=PLOTLY_TEMPLATE,
        labels={"value": "Percentile within genre", "measure": "Measure"},
        title="Selected movie percentile versus genre median",
    )


def _style_altair(chart):
    return (
        chart.configure(background=GALAXY)
        .configure_axis(
            domainColor=UNIVERSE,
            gridColor=UNIVERSE,
            gridOpacity=0.24,
            labelColor=MILKY_WAY,
            tickColor=UNIVERSE,
            titleColor=SKY,
        )
        .configure_header(labelColor=MILKY_WAY, titleColor=SKY)
        .configure_legend(
            labelColor=MILKY_WAY,
            titleColor=SKY,
            strokeColor=UNIVERSE,
            fillColor=GALAXY,
        )
        .configure_title(color=MILKY_WAY)
        .configure_view(stroke=UNIVERSE)
    )
