"""
Tab — Methodik: Pipeline, Datenquellen, Cleaning, Klassifikation.

Erklärt das Projekt aus technischer Sicht — wichtig für:
- Recruiter, die das Projekt verstehen wollen
- Selbst-Dokumentation für später
"""

import pandas as pd
import streamlit as st


def _section_card(title: str, body_html: str, icon: str = "📋"):
    """Renderiert eine Sektion als Card."""
    return f"""
    <div style="
        background: rgba(99, 102, 241, 0.04);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 16px;
    ">
        <h3 style="margin: 0 0 12px 0; font-size: 1.1em; color: #a5b4fc;">
            {icon}  {title}
        </h3>
        <div style="color: #cbd5e1; font-size: 0.95em; line-height: 1.6;">
            {body_html}
        </div>
    </div>
    """


def render(jobs: pd.DataFrame, skills: pd.DataFrame):
    """Rendert den Methodik-Tab."""

    # ─────────────────────────────────────────────────────────────────
    # Intro
    # ─────────────────────────────────────────────────────────────────
    st.markdown("### 🛠️ Methodik & Pipeline")
    st.caption(
        "Wie das Dashboard funktioniert — von Datensammlung bis Visualisierung."
    )

    st.markdown("")

    # ─────────────────────────────────────────────────────────────────
    # Pipeline-Übersicht (visual)
    # ─────────────────────────────────────────────────────────────────
    pipeline_html = """
    <div style="
        display: flex;
        gap: 12px;
        align-items: stretch;
        flex-wrap: wrap;
        margin: 20px 0;
    ">
        <div style="flex:1; min-width:180px; background:rgba(16,185,129,0.08);
                    border:1px solid rgba(16,185,129,0.3); border-radius:10px;
                    padding:16px; text-align:center;">
            <div style="font-size:1.6em; margin-bottom:4px;">📡</div>
            <div style="font-weight:600; color:#34d399; margin-bottom:6px;">1. Collect</div>
            <div style="font-size:0.85em; color:#94a3b8;">
                Multi-Source-APIs<br>
                <em>Arbeitsagentur + Adzuna</em>
            </div>
        </div>
        <div style="display:flex; align-items:center; color:#6366f1; font-size:1.5em;">→</div>
        <div style="flex:1; min-width:180px; background:rgba(99,102,241,0.08);
                    border:1px solid rgba(99,102,241,0.3); border-radius:10px;
                    padding:16px; text-align:center;">
            <div style="font-size:1.6em; margin-bottom:4px;">🧹</div>
            <div style="font-weight:600; color:#a5b4fc; margin-bottom:6px;">2. Clean</div>
            <div style="font-size:0.85em; color:#94a3b8;">
                ETL & Feature-Engineering<br>
                <em>Dedup, Stadt, Skills, Klassifikation</em>
            </div>
        </div>
        <div style="display:flex; align-items:center; color:#6366f1; font-size:1.5em;">→</div>
        <div style="flex:1; min-width:180px; background:rgba(245,158,11,0.08);
                    border:1px solid rgba(245,158,11,0.3); border-radius:10px;
                    padding:16px; text-align:center;">
            <div style="font-size:1.6em; margin-bottom:4px;">💾</div>
            <div style="font-weight:600; color:#fbbf24; margin-bottom:6px;">3. Store</div>
            <div style="font-size:0.85em; color:#94a3b8;">
                PostgreSQL (Neon Cloud)<br>
                <em>jobs · skills · job_skills</em>
            </div>
        </div>
        <div style="display:flex; align-items:center; color:#6366f1; font-size:1.5em;">→</div>
        <div style="flex:1; min-width:180px; background:rgba(236,72,153,0.08);
                    border:1px solid rgba(236,72,153,0.3); border-radius:10px;
                    padding:16px; text-align:center;">
            <div style="font-size:1.6em; margin-bottom:4px;">📊</div>
            <div style="font-weight:600; color:#f472b6; margin-bottom:6px;">4. Visualize</div>
            <div style="font-size:0.85em; color:#94a3b8;">
                Streamlit Dashboard<br>
                <em>Plotly, Multi-Tab, Live-Filter</em>
            </div>
        </div>
    </div>
    """
    if hasattr(st, "html"):
        st.html(pipeline_html)
    else:
        st.markdown(pipeline_html, unsafe_allow_html=True)

    st.markdown("")

    # ─────────────────────────────────────────────────────────────────
    # Live-Statistiken
    # ─────────────────────────────────────────────────────────────────
    st.markdown("##### 📈 Aktuelle Datenbasis")

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.metric("📋 Jobs", f"{len(jobs):,}".replace(",", "."))
    with s2:
        st.metric("🛠️ Eindeutige Skills",
                  skills["skill"].nunique() if not skills.empty else 0)
    with s3:
        st.metric("🔗 Skill-Erwähnungen", f"{len(skills):,}".replace(",", ".") if not skills.empty else 0)
    with s4:
        if "source" in jobs.columns:
            st.metric("📡 Datenquellen", jobs["source"].nunique())

    if not jobs.empty and "job_posted_at_datetime_utc" in jobs.columns:
        try:
            dts = pd.to_datetime(
                jobs["job_posted_at_datetime_utc"], errors="coerce", utc=True
            )
            newest = dts.max()
            oldest = dts.min()
            if pd.notna(newest) and pd.notna(oldest):
                st.caption(
                    f"📅 Zeitspanne der Anzeigen: "
                    f"**{oldest.strftime('%d.%m.%Y')}** bis **{newest.strftime('%d.%m.%Y')}**"
                )
        except Exception:
            pass

    st.markdown("---")

    # ─────────────────────────────────────────────────────────────────
    # Sektion: Datenquellen
    # ─────────────────────────────────────────────────────────────────
    st.markdown("##### 📡 Datenquellen")

    sources_html = """
    <div style="display:flex; gap:16px; flex-wrap:wrap; margin: 16px 0;">
        <div style="flex:1; min-width:280px; background:rgba(30,41,59,0.4);
                    border-left:4px solid #10b981; border-radius:8px;
                    padding:16px 20px;">
            <h4 style="margin:0 0 8px 0; color:#34d399;">🏛️ Bundesagentur für Arbeit</h4>
            <p style="margin:0; color:#cbd5e1; font-size:0.9em; line-height:1.5;">
                Größte Stellendatenbank Deutschlands.
                Offizielle staatliche Quelle, kostenlos und unbegrenzt nutzbar.
                Über 1 Mio. aktive Stellen aus klassischen Branchen
                (Industrie, Verwaltung, Gesundheitswesen).
            </p>
            <p style="margin:8px 0 0 0; font-size:0.85em; color:#64748b;">
                <code style="background:#1e293b; padding:1px 6px; border-radius:4px;">jobsuche-service/pc/v4/app/jobs</code>
            </p>
        </div>
        <div style="flex:1; min-width:280px; background:rgba(30,41,59,0.4);
                    border-left:4px solid #f59e0b; border-radius:8px;
                    padding:16px 20px;">
            <h4 style="margin:0 0 8px 0; color:#fbbf24;">🌐 Adzuna</h4>
            <p style="margin:0; color:#cbd5e1; font-size:0.9em; line-height:1.5;">
                Globaler Job-Aggregator.
                Sammelt Stellen von LinkedIn, Indeed, StepStone, Monster
                und Firmen-Websites. Stärkere Tech-/Startup-Coverage als
                Arbeitsagentur. 250 API-Calls/Tag im Free-Tier.
            </p>
            <p style="margin:8px 0 0 0; font-size:0.85em; color:#64748b;">
                <code style="background:#1e293b; padding:1px 6px; border-radius:4px;">api.adzuna.com/v1/api/jobs/de</code>
            </p>
        </div>
    </div>
    """
    if hasattr(st, "html"):
        st.html(sources_html)
    else:
        st.markdown(sources_html, unsafe_allow_html=True)

    st.info(
        "💡 **Warum beide Quellen?** Sie ergänzen sich: Arbeitsagentur deckt den klassischen "
        "deutschen Arbeitsmarkt ab, Adzuna den Tech-/Digitalbereich. Das vermeidet "
        "Verzerrungen durch eine einzige Datenquelle."
    )

    st.markdown("")

    # ─────────────────────────────────────────────────────────────────
    # Sektion: Cleaning & Feature-Engineering
    # ─────────────────────────────────────────────────────────────────
    st.markdown("##### 🧹 Cleaning & Feature-Engineering")

    cleaning_steps = [
        ("🆔", "Deduplizierung", "Eindeutige `job_id` pro Quelle (verhindert "
         "Mehrfach-Anzeigen derselben Stelle)."),
        ("🏙️", "Stadt-Extraktion", "Aus 3 Feldern kombiniert: `job_city`, "
         "`job_location`, sowie Regex-Suche im ersten Beschreibungsabsatz nach "
         "deutschen Großstädten."),
        ("💼", "Rollen-Klassifikation", "Title + erste 500 Zeichen Description werden "
         "auf 30+ deutsche/englische Begriffe geprüft "
         "(`Data Analyst`, `BI-Berater`, `Reporting`, `KPI`, `Snowflake`, "
         "`Process Mining` etc.). Engineer-Stellen mit Maschinenbau-Bezug "
         "werden ausgeschlossen."),
        ("🏠", "Remote-Erkennung", "Live-Regex über Title + Description mit "
         "14 Patterns: `remote`, `homeoffice`, `mobiles arbeiten`, `hybrid`, "
         "`ortsunabhängig`, `telearbeit` etc. – kombiniert mit dem `is_remote`-"
         "Flag der API."),
        ("🛠️", "Skill-Extraktion", "Wortgrenzen-basiertes Regex-Matching für "
         "30+ Tools (Python, SQL, Tableau, dbt etc.) – verhindert False Positives "
         "wie 'git' in 'digital'. Synonym-Mapping: `powerbi`→`power bi`."),
        ("🎓", "Junior-Erkennung", "Keyword-Matching für `junior`, `entry level`, "
         "`trainee`, `berufseinstieg`, `absolvent`, `werkstudent`."),
    ]

    for icon, name, desc in cleaning_steps:
        st.markdown(
            f"**{icon} {name}**  \n"
            f"<span style='color:#94a3b8; font-size:0.92em;'>{desc}</span>",
            unsafe_allow_html=True,
        )
        st.markdown("")

    st.markdown("---")

    # ─────────────────────────────────────────────────────────────────
    # Sektion: Datenbank-Schema
    # ─────────────────────────────────────────────────────────────────
    st.markdown("##### 💾 Datenbank-Schema")

    schema_md = """
    Optionales PostgreSQL-Backend (Neon Cloud) mit normalisiertem Schema:

    | Tabelle | Funktion |
    |---|---|
    | `jobs` | Faktentabelle: 1 Zeile pro Stelle (Titel, Arbeitgeber, Stadt, Score, Datum, Source) |
    | `skills` | Lookup: 1 Zeile pro eindeutigem Skill (Python, SQL, ...) |
    | `job_skills` | m:n-Bridge: Welcher Job nennt welche Skills? |

    **Vorteile:** Schnelle Abfragen über Window Functions, CTEs und Joins; persistente Speicherung;
    Multi-User-fähig wenn das Dashboard öffentlich gehostet wird.
    """
    st.markdown(schema_md)

    st.markdown("---")

    # ─────────────────────────────────────────────────────────────────
    # Sektion: Limitationen & Honest View
    # ─────────────────────────────────────────────────────────────────
    st.markdown("##### ⚠️ Limitationen")

    st.markdown(
        """
        - **Cross-Source-Duplikate:** Dieselbe Stelle auf LinkedIn (via Adzuna) und Arbeitsagentur
          haben unterschiedliche IDs und werden derzeit nicht zusammengeführt.
        - **Stellenanzeige-Snapshot:** Die Daten sind ein Snapshot zum Zeitpunkt der Sammlung.
          Manche Anzeigen sind beim Klicken auf "Zur Anzeige" möglicherweise schon abgelaufen.
        - **Klassifikation auf Heuristiken:** Rollen-Erkennung basiert auf Schlüsselwörtern,
          kein ML. Etwa 30% der Jobs landen in der Restkategorie "Other".
        - **Salary-Daten unzuverlässig:** Nur ein Bruchteil der Anzeigen enthält strukturierte
          Gehaltsangaben. Die Werte werden hier deshalb nicht zentral ausgewertet.
        - **Skill-Liste manuell gepflegt:** Es werden nur Skills erkannt, die in einer
          definierten Liste stehen. Neue Tools (z.B. Polars, DuckDB) müssten ergänzt werden.
        """
    )

    st.markdown("---")

    # ─────────────────────────────────────────────────────────────────
    # Sektion: Tech-Stack
    # ─────────────────────────────────────────────────────────────────
    st.markdown("##### 🔧 Tech-Stack")

    stack_html = """
    <div style="display:flex; flex-wrap:wrap; gap:8px; margin:12px 0;">
        <span style="background:rgba(59,130,246,0.15); color:#93c5fd;
                     padding:5px 12px; border-radius:8px; font-size:0.85em;">
            🐍 Python 3.12
        </span>
        <span style="background:rgba(59,130,246,0.15); color:#93c5fd;
                     padding:5px 12px; border-radius:8px; font-size:0.85em;">
            📦 pandas
        </span>
        <span style="background:rgba(236,72,153,0.15); color:#f9a8d4;
                     padding:5px 12px; border-radius:8px; font-size:0.85em;">
            🎨 Streamlit
        </span>
        <span style="background:rgba(236,72,153,0.15); color:#f9a8d4;
                     padding:5px 12px; border-radius:8px; font-size:0.85em;">
            📊 Plotly
        </span>
        <span style="background:rgba(245,158,11,0.15); color:#fbbf24;
                     padding:5px 12px; border-radius:8px; font-size:0.85em;">
            🐘 PostgreSQL
        </span>
        <span style="background:rgba(245,158,11,0.15); color:#fbbf24;
                     padding:5px 12px; border-radius:8px; font-size:0.85em;">
            ☁️ Neon Cloud
        </span>
        <span style="background:rgba(16,185,129,0.15); color:#6ee7b7;
                     padding:5px 12px; border-radius:8px; font-size:0.85em;">
            🌐 REST APIs
        </span>
        <span style="background:rgba(99,102,241,0.15); color:#a5b4fc;
                     padding:5px 12px; border-radius:8px; font-size:0.85em;">
            🔗 SQLAlchemy
        </span>
    </div>
    """
    if hasattr(st, "html"):
        st.html(stack_html)
    else:
        st.markdown(stack_html, unsafe_allow_html=True)

    st.markdown("---")

    # ─────────────────────────────────────────────────────────────────
    # Repository
    # ─────────────────────────────────────────────────────────────────
    st.markdown("##### 🔗 Repository")
    st.markdown(
        "<a href='https://github.com/l1ghty34r/job-market-analyzer' "
        "target='_blank' style='color:#a5b4fc;'>"
        "GitHub: l1ghty34r/job-market-analyzer →</a>",
        unsafe_allow_html=True,
    )
    st.caption("Portfolio-Projekt im Rahmen der Weiterbildung zum Data Analyst.")
