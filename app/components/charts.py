"""
Wiederverwendbare Chart-Helper auf Plotly-Basis.

Konsistente, klare Charts mit minimalem Boilerplate.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# Konsistente Farben
COLOR_REMOTE = "#10b981"   # grün
COLOR_HYBRID = "#3b82f6"   # blau
COLOR_ONSITE = "#9ca3af"   # grau
COLOR_PRIMARY = "#6366f1"  # indigo

REMOTE_COLOR_MAP = {
    "Remote": COLOR_REMOTE,
    "Hybrid": COLOR_HYBRID,
    "Remote/Hybrid erwähnt": "#a7f3d0",
    "Onsite/Unknown": COLOR_ONSITE,
}


def empty_chart(message: str = "Keine Daten") -> go.Figure:
    """Platzhalter-Chart für leere Datasets."""
    fig = go.Figure()
    fig.add_annotation(
        text=message, xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=14, color="gray"),
    )
    fig.update_layout(
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        height=250, margin=dict(l=0, r=0, t=0, b=0),
    )
    return fig


def horizontal_bar(
    df: pd.DataFrame,
    column: str,
    n: int = 10,
    title: str = "",
    color: str = COLOR_PRIMARY,
) -> go.Figure:
    """Top-N horizontale Balken."""
    if df.empty or column not in df.columns:
        return empty_chart()

    counts = df[column].value_counts().head(n).reset_index()
    counts.columns = [column, "count"]
    counts = counts.sort_values("count", ascending=True)

    fig = px.bar(
        counts, x="count", y=column, orientation="h",
        title=title, height=max(250, len(counts) * 30 + 80),
    )
    fig.update_traces(marker_color=color)
    fig.update_layout(
        margin=dict(l=10, r=10, t=40 if title else 10, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis_title="",
        yaxis_title="",
        showlegend=False,
    )
    return fig


def remote_breakdown_chart(jobs: pd.DataFrame) -> go.Figure:
    """Verteilung Remote/Hybrid/Onsite als horizontaler Bar."""
    if jobs.empty or "remote_type" not in jobs.columns:
        return empty_chart()

    counts = jobs["remote_type"].value_counts().reset_index()
    counts.columns = ["Arbeitsform", "Anzahl"]

    fig = px.bar(
        counts, x="Anzahl", y="Arbeitsform", orientation="h",
        color="Arbeitsform", color_discrete_map=REMOTE_COLOR_MAP,
        text="Anzahl", height=250,
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis_title="",
        yaxis_title="",
    )
    fig.update_traces(textposition="outside")
    return fig


def role_remote_stacked(jobs: pd.DataFrame) -> go.Figure:
    """Gestapelte Bars: Rollen × Arbeitsform."""
    if jobs.empty:
        return empty_chart()

    grouped = (
        jobs.groupby(["role_group", "remote_type"])
        .size()
        .reset_index(name="count")
    )
    fig = px.bar(
        grouped, x="role_group", y="count", color="remote_type",
        color_discrete_map=REMOTE_COLOR_MAP,
        labels={"count": "Anzahl Jobs", "role_group": "Rolle", "remote_type": "Arbeitsform"},
        height=350,
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def skills_heatmap(skills_df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    """Heatmap: Skills × Rollen."""
    if skills_df.empty:
        return empty_chart()

    pivot = (
        skills_df.groupby(["role_group", "skill"])
        .size()
        .reset_index(name="count")
        .pivot(index="skill", columns="role_group", values="count")
        .fillna(0)
    )
    pivot["total"] = pivot.sum(axis=1)
    pivot = pivot.sort_values("total", ascending=False).head(top_n).drop(columns="total")

    if pivot.empty:
        return empty_chart()

    fig = px.imshow(
        pivot.astype(int),
        color_continuous_scale="Blues",
        aspect="auto",
        text_auto=True,
        height=400,
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        coloraxis_showscale=False,
        xaxis_title="",
        yaxis_title="",
    )
    return fig
