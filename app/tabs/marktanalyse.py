"""
Tab — Marktanalyse: Markt-Einblicke mit Fokus auf Homeoffice-Stellen.

Hilft bei der Frage: 'Wo lohnt es sich, sich auf Homeoffice-Stellen zu bewerben?'
- Welche Arbeitgeber stellen tatsächlich Remote ein?
- Welche Rollen haben die höchste Homeoffice-Quote?
- Welche Skills werden in Remote-Jobs gefragt?
- In welchen Städten gibt's am meisten Remote-Stellen?
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from src.utils import format_number
from src.remote_filter import filter_remote_jobs


# Konsistente Farben
COLOR_REMOTE = "#10b981"
COLOR_NEUTRAL = "#6366f1"
COLOR_MUTED = "#9ca3af"


def _empty_chart(message: str = "Keine Daten"):
    fig = px.bar(pd.DataFrame({"x": [], "y": []}), x="x", y="y")
    fig.add_annotation(
        text=message, xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=14, color="gray"),
    )
    fig.update_layout(
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        height=260, margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def _clean_chart_layout(fig, height: int = 350):
    """Einheitliches Styling für alle Charts."""
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=height,
        showlegend=False,
        xaxis_title="",
        yaxis_title="",
    )
    return fig


def render(jobs: pd.DataFrame, skills: pd.DataFrame):
    """Rendert den Marktanalyse-Tab."""

    df = jobs.copy()

    if df.empty:
        st.warning("Keine Daten verfügbar.")
        return

    skills_df = skills[skills["job_id"].isin(df["job_id"])].copy()

    # ─────────────────────────────────────────────────────────────────
    # FILTER (oben, alle leer als Default)
    # ─────────────────────────────────────────────────────────────────
    st.markdown("##### 🔍 Filter (optional)")

    f1, f2, f3 = st.columns([2, 2, 1])

    with f1:
        all_roles = sorted(df["role_group"].dropna().unique().tolist())
        # Default: alle außer "Other" (Other ist Rest-Kategorie)
        default_roles = [r for r in all_roles if r != "Other"]
        selected_roles = st.multiselect(
            "Rolle",
            options=all_roles,
            default=default_roles,
            placeholder="Alle Rollen",
            key="m_roles",
            help="'Other' = Jobs ohne klare Data-Klassifikation. "
                 "Standardmäßig ausgeblendet.",
        )

    with f2:
        all_cities = sorted(
            df[df["job_city"] != "Unbekannt"]["job_city"].dropna().unique().tolist()
        )
        selected_cities = st.multiselect(
            "Stadt",
            options=all_cities,
            default=[],
            placeholder="Alle Städte",
            key="m_cities",
        )

    with f3:
        remote_only = st.toggle(
            "🏠 Nur Remote/Homeoffice",
            value=False,
            key="m_remote_only",
        )

    # Filter anwenden
    if selected_roles:
        df = df[df["role_group"].isin(selected_roles)]
    if selected_cities:
        df = df[df["job_city"].isin(selected_cities)]
    if remote_only:
        df = filter_remote_jobs(df)

    if df.empty:
        st.warning("Keine Jobs für die Filterauswahl.")
        return

    skills_df = skills_df[skills_df["job_id"].isin(df["job_id"])].copy()

    # Live-Erkennung: berechnet is_remote_now auf den aktuellen Daten neu,
    # damit auch Updates an REMOTE_PATTERNS sofort wirken
    remote_filtered = filter_remote_jobs(df)
    remote_job_ids = set(remote_filtered["job_id"]) if not remote_filtered.empty else set()
    df["is_remote_now"] = df["job_id"].isin(remote_job_ids)

    st.markdown("")

    # ─────────────────────────────────────────────────────────────────
    # KEY-METRICS – Homeoffice-Fokus
    # ─────────────────────────────────────────────────────────────────
    total = len(df)
    remote_count = int(df["is_remote_now"].sum())
    pure_remote = int((df["remote_type"] == "Remote").sum())
    junior_remote = int(((df["is_junior"] == 1) & (df["is_remote_now"])).sum())
    fresh_count = 0
    if "job_posted_at_datetime_utc" in df.columns:
        try:
            dts = pd.to_datetime(df["job_posted_at_datetime_utc"], errors="coerce", utc=True)
            cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=7)
            fresh_count = int((dts >= cutoff).sum())
        except Exception:
            pass

    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("📋 Stellen gesamt", format_number(total))
    with m2:
        share = remote_count / max(total, 1) * 100
        st.metric("🏠 Mit Homeoffice", format_number(remote_count),
                  f"{share:.0f}%", help="Inkl. Remote, Hybrid und 'mobiles Arbeiten'")
    with m3:
        st.metric("🌍 Vollständig Remote", format_number(pure_remote))
    with m4:
        st.metric("🎓 Junior + Remote", format_number(junior_remote))
    with m5:
        st.metric("🆕 Neu (≤ 7 Tage)", format_number(fresh_count))

    st.markdown("---")

    # ─────────────────────────────────────────────────────────────────
    # CHART 1: Homeoffice-Quote pro Rolle (Hauptchart!)
    # ─────────────────────────────────────────────────────────────────
    st.markdown("#### 🏠 Homeoffice-Quote nach Rolle")
    st.caption("Welche Rollen bieten am häufigsten Remote-/Homeoffice-Optionen? "
               "Höhere Werte = bessere Chancen für deine Suche.")

    role_remote = (
        df.groupby("role_group")
        .agg(
            total=("job_id", "count"),
            remote=("is_remote_now", "sum"),
        )
        .reset_index()
    )
    role_remote = role_remote[role_remote["total"] >= 5]  # Mindestens 5 Jobs für Aussagekraft
    role_remote["remote_pct"] = (role_remote["remote"] / role_remote["total"] * 100).round(0)
    role_remote = role_remote.sort_values("remote_pct", ascending=True)

    if role_remote.empty:
        st.info("Zu wenig Daten pro Rolle für aussagekräftige Quote.")
    else:
        fig = px.bar(
            role_remote,
            x="remote_pct",
            y="role_group",
            orientation="h",
            text="remote_pct",
            color="remote_pct",
            color_continuous_scale=[(0, COLOR_MUTED), (1, COLOR_REMOTE)],
            range_color=(0, 100),
            labels={"remote_pct": "Homeoffice-Quote %", "role_group": "Rolle"},
            hover_data={"total": True, "remote": True, "remote_pct": False},
        )
        fig.update_traces(
            texttemplate="%{text}%",
            textposition="outside",
        )
        _clean_chart_layout(fig, height=max(280, len(role_remote) * 38 + 60))
        fig.update_layout(coloraxis_showscale=False, xaxis_range=[0, 110])
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # ─────────────────────────────────────────────────────────────────
    # CHART 2: Top-Arbeitgeber für Homeoffice
    # ─────────────────────────────────────────────────────────────────
    st.markdown("#### 🏢 Top-Arbeitgeber für Homeoffice")
    st.caption("Wer stellt tatsächlich Remote ein? Hier siehst du die Firmen mit "
               "den meisten Homeoffice-Stellen im Datensatz.")

    remote_jobs = df[df["is_remote_now"] == True]  # noqa: E712
    employer_remote = (
        remote_jobs[
            remote_jobs["employer_name"].notna() & (remote_jobs["employer_name"] != "")
        ]
        ["employer_name"]
        .value_counts()
        .head(15)
        .reset_index()
    )
    employer_remote.columns = ["Arbeitgeber", "Homeoffice-Stellen"]
    employer_remote = employer_remote.sort_values("Homeoffice-Stellen", ascending=True)

    if employer_remote.empty:
        st.info("Keine Homeoffice-Stellen mit Arbeitgeber-Info gefunden.")
    else:
        fig = px.bar(
            employer_remote,
            x="Homeoffice-Stellen",
            y="Arbeitgeber",
            orientation="h",
            text="Homeoffice-Stellen",
        )
        fig.update_traces(marker_color=COLOR_REMOTE, textposition="outside")
        _clean_chart_layout(fig, height=max(380, len(employer_remote) * 28 + 80))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # ─────────────────────────────────────────────────────────────────
    # CHART 3: Top-Skills in Homeoffice-Jobs (vs. Markt insgesamt)
    # ─────────────────────────────────────────────────────────────────
    st.markdown("#### 🛠️ Welche Skills werden für Homeoffice-Jobs gesucht?")
    st.caption("Vergleich: Skill-Häufigkeit in Remote-Stellen vs. im Gesamtmarkt. "
               "Skills mit grünem Balken werden überdurchschnittlich oft remote gesucht.")

    if not skills_df.empty:
        # Skills aus Remote-Jobs
        remote_job_ids = set(remote_jobs["job_id"])
        remote_skills = skills_df[skills_df["job_id"].isin(remote_job_ids)]

        if not remote_skills.empty and not skills_df.empty:
            # Top 15 Skills im Gesamtmarkt
            top_skills = skills_df["skill"].value_counts().head(15).index.tolist()

            n_total_jobs = df["job_id"].nunique()
            n_remote_jobs = max(remote_jobs["job_id"].nunique(), 1)

            comparison_data = []
            for skill in top_skills:
                total_count = (skills_df["skill"] == skill).sum()
                remote_count = (remote_skills["skill"] == skill).sum()
                # Anteile: in welchem % der Remote-Jobs taucht der Skill auf?
                total_pct = total_count / n_total_jobs * 100
                remote_pct = remote_count / n_remote_jobs * 100
                comparison_data.append({
                    "Skill": skill,
                    "Im Gesamtmarkt %": round(total_pct, 1),
                    "In Remote-Jobs %": round(remote_pct, 1),
                })

            comp_df = pd.DataFrame(comparison_data).sort_values(
                "In Remote-Jobs %", ascending=True
            )

            # Long-Format für gruppierten Bar-Chart
            comp_long = comp_df.melt(
                id_vars=["Skill"],
                value_vars=["Im Gesamtmarkt %", "In Remote-Jobs %"],
                var_name="Kategorie",
                value_name="Anteil",
            )

            fig = px.bar(
                comp_long,
                x="Anteil",
                y="Skill",
                color="Kategorie",
                orientation="h",
                barmode="group",
                color_discrete_map={
                    "Im Gesamtmarkt %": COLOR_MUTED,
                    "In Remote-Jobs %": COLOR_REMOTE,
                },
            )
            fig.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                height=max(380, len(top_skills) * 30 + 100),
                xaxis_title="Anteil in % der Stellen",
                yaxis_title="",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                ),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Zu wenig Remote-Jobs für Skill-Vergleich.")
    else:
        st.info("Keine Skill-Daten verfügbar.")

    st.markdown("---")

    # ─────────────────────────────────────────────────────────────────
    # CHART 4: Top-Städte mit Homeoffice-Optionen
    # ─────────────────────────────────────────────────────────────────
    st.markdown("#### 📍 Top-Städte für Homeoffice-Jobs")
    st.caption("Welche Städte haben den größten Markt für Homeoffice-Stellen? "
               "(Auch bei 'Hybrid'-Stellen relevant: gelegentlich vor Ort.)")

    city_remote = (
        remote_jobs[remote_jobs["job_city"] != "Unbekannt"]
        .groupby("job_city")
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
        .head(15)
        .sort_values("count", ascending=True)
    )

    if city_remote.empty:
        st.info("Keine Stadt-Informationen für Homeoffice-Stellen.")
    else:
        fig = px.bar(
            city_remote,
            x="count",
            y="job_city",
            orientation="h",
            text="count",
        )
        fig.update_traces(marker_color=COLOR_NEUTRAL, textposition="outside")
        _clean_chart_layout(fig, height=max(380, len(city_remote) * 28 + 80))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # ─────────────────────────────────────────────────────────────────
    # Datenquellen (kompakt)
    # ─────────────────────────────────────────────────────────────────
    if "source" in df.columns:
        with st.expander("📡 Datenquellen"):
            source_counts = (
                df.groupby("source")
                .agg(
                    total=("job_id", "count"),
                    remote=("is_remote_now", "sum"),
                )
                .reset_index()
            )
            source_counts["Homeoffice-Quote"] = (
                source_counts["remote"] / source_counts["total"] * 100
            ).round(0).astype(int).astype(str) + "%"
            source_counts.columns = ["Quelle", "Jobs gesamt", "Davon Homeoffice", "Homeoffice-Quote"]
            st.dataframe(source_counts, hide_index=True, use_container_width=False)
