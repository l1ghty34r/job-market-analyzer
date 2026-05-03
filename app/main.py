"""
Data Job Market Analyzer Germany — Single-Page Dashboard.

Tab-basierte Navigation, kein Sidebar-Menü. Die App hat 3 Tabs:
  1. 📊 Marktanalyse — Markt-Übersicht
  2. 🔎 Jobsuche    — Personalisierte Jobsuche
  3. 📚 Methodik    — Pipeline & Limitationen

Run:
    streamlit run app/main.py
"""

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.utils import load_jobs, load_skills, load_jobs_with_skills  # noqa: E402
from app.tabs import marktanalyse, jobsuche, methodik  # noqa: E402


# ─────────────────────────────────────────────────────────────────────
# Page-Konfiguration
# ─────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Data Job Market DE",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    /* ─── Sidebar ausblenden ─────────────────────────────────────── */
    [data-testid="stSidebarCollapsedControl"] { display: none; }
    section[data-testid="stSidebar"] { display: none; }

    /* ─── Hauptbereich ───────────────────────────────────────────── */
    .block-container {
        padding-top: 2.5rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }

    /* ─── Typografie ─────────────────────────────────────────────── */
    h1 {
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }
    h2, h3, h4, h5 {
        font-weight: 600 !important;
        letter-spacing: -0.01em;
    }

    /* ─── Tab-Navigation (Radio als Pills) ───────────────────────── */
    div[role="radiogroup"] {
        gap: 6px;
        padding: 4px;
        background: rgba(30, 41, 59, 0.5);
        border-radius: 12px;
        display: inline-flex;
    }
    div[role="radiogroup"] > label {
        background: transparent;
        padding: 10px 22px;
        border-radius: 8px;
        margin: 0;
        cursor: pointer;
        transition: all 0.18s ease;
        color: #94a3b8;
        font-weight: 500;
    }
    div[role="radiogroup"] > label:hover {
        background: rgba(129, 140, 248, 0.1);
        color: #c7d2fe;
    }
    div[role="radiogroup"] > label[data-checked="true"] {
        background: rgba(129, 140, 248, 0.18);
        color: #c7d2fe;
        font-weight: 600;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    div[role="radiogroup"] > label > div:first-child {
        display: none;
    }

    /* ─── Buttons ────────────────────────────────────────────────── */
    .stButton button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.18s ease;
        border: 1px solid rgba(129, 140, 248, 0.3);
    }
    .stButton button:hover {
        border-color: #818cf8;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(129, 140, 248, 0.15);
    }

    /* ─── Inputs polieren ────────────────────────────────────────── */
    .stTextInput input,
    .stMultiSelect div[data-baseweb="select"],
    .stSelectbox div[data-baseweb="select"] {
        border-radius: 8px;
        transition: border-color 0.15s ease;
    }
    .stTextInput input:focus {
        border-color: #818cf8;
    }

    /* ─── Metric-Cards eleganter ─────────────────────────────────── */
    [data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(129, 140, 248, 0.15);
        border-radius: 12px;
        padding: 16px 20px;
        transition: all 0.2s ease;
    }
    [data-testid="stMetric"]:hover {
        border-color: rgba(129, 140, 248, 0.4);
        background: rgba(30, 41, 59, 0.6);
    }
    [data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
        font-size: 0.85em !important;
    }
    [data-testid="stMetricValue"] {
        color: #e2e8f0 !important;
        font-weight: 700 !important;
    }

    /* ─── Info-Boxen / Datenstand-Bar ────────────────────────────── */
    div[data-testid="stAlert"] {
        border-radius: 10px;
        border: 1px solid rgba(129, 140, 248, 0.2);
        background: rgba(30, 41, 59, 0.5);
    }

    /* ─── Pillen-Filter (st.pills) ───────────────────────────────── */
    button[kind="pillsButton"],
    button[data-baseweb="button"][kind="pills"] {
        border-radius: 8px !important;
        transition: all 0.15s ease !important;
    }

    /* ─── Expander ───────────────────────────────────────────────── */
    [data-testid="stExpander"] {
        border-radius: 10px;
        border-color: rgba(129, 140, 248, 0.15) !important;
    }
    [data-testid="stExpander"] summary {
        font-weight: 500;
        color: #c7d2fe;
    }

    /* ─── Dataframes / Tables ────────────────────────────────────── */
    div[data-testid="stDataFrame"] {
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid rgba(129, 140, 248, 0.15);
    }

    /* ─── Toggle-Switches ────────────────────────────────────────── */
    div[data-baseweb="checkbox"][role="checkbox"] {
        border-radius: 4px;
    }

    /* ─── Captions ───────────────────────────────────────────────── */
    .stCaption, [data-testid="stCaptionContainer"] {
        color: #94a3b8 !important;
    }

    /* ─── Horizontale Trennlinien ────────────────────────────────── */
    hr {
        border-color: rgba(129, 140, 248, 0.15) !important;
        margin: 1.5rem 0 !important;
    }

    /* ─── Popover (Aktualisieren-Menü) ───────────────────────────── */
    div[data-testid="stPopoverBody"] {
        background: rgba(15, 23, 42, 0.95);
        border-radius: 12px;
    }

    /* ─── Scrollbar ──────────────────────────────────────────────── */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    ::-webkit-scrollbar-track {
        background: rgba(30, 41, 59, 0.3);
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(129, 140, 248, 0.3);
        border-radius: 5px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(129, 140, 248, 0.5);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────────────
# Helper: Pipeline-Schritt im UI ausführen
# ─────────────────────────────────────────────────────────────────────
def run_pipeline_step(name: str, cmd: list[str], log_placeholder) -> bool:
    """Führt einen Pipeline-Schritt aus, loggt live in das Streamlit-UI."""
    log_placeholder.markdown(f"▶ **{name}** läuft …")
    try:
        # WICHTIG: encoding="utf-8" und PYTHONIOENCODING erzwingen UTF-8 auch
        # auf Windows, sonst crashen Subprocess-Prints mit Sonderzeichen
        # (Pfeile, Emojis, Umlaute) auf cp1252-Konsolen.
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        result = subprocess.run(
            cmd,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=600,
        )
        if result.returncode == 0:
            log_placeholder.success(f"✅ {name} fertig")
            return True
        log_placeholder.error(
            f"❌ {name} fehlgeschlagen (Exit {result.returncode})\n\n"
            f"```\n{(result.stderr or result.stdout)[-800:]}\n```"
        )
        return False
    except subprocess.TimeoutExpired:
        log_placeholder.error(f"⏱️ {name} dauert zu lange (>10min) – Abbruch.")
        return False
    except Exception as e:
        log_placeholder.error(f"❌ {name} crashed: {e}")
        return False


def run_full_pipeline(skip_collect: bool, to_postgres: bool, truncate: bool) -> None:
    """Führt die komplette Pipeline aus, mit Live-Status im UI."""
    python = sys.executable

    with st.status("🔄 Pipeline läuft…", expanded=True) as status:
        steps_ok = True

        if not skip_collect:
            step1 = st.empty()
            ok = run_pipeline_step(
                "1/4  Daten von APIs holen",
                [python, "-m", "src.collect_jobs"],
                step1,
            )
            steps_ok = steps_ok and ok
        else:
            st.markdown("⏭️  Schritt 1 (Collect) übersprungen")

        if steps_ok:
            step2 = st.empty()
            ok = run_pipeline_step(
                "2/4  Daten bereinigen",
                [python, "-m", "src.clean_jobs"],
                step2,
            )
            steps_ok = steps_ok and ok

        if steps_ok:
            step3 = st.empty()
            ok = run_pipeline_step(
                "3/4  Skills extrahieren",
                [python, "-m", "src.extract_skills"],
                step3,
            )
            steps_ok = steps_ok and ok

        if steps_ok and to_postgres:
            cmd = [python, "-m", "src.load_to_postgres"]
            if truncate:
                cmd.append("--truncate")
            step4 = st.empty()
            ok = run_pipeline_step(
                "4/4  PostgreSQL aktualisieren",
                cmd,
                step4,
            )
            steps_ok = steps_ok and ok
        elif not to_postgres:
            st.markdown("⏭️  Schritt 4 (PostgreSQL) übersprungen")

        if steps_ok:
            status.update(label="✅ Pipeline abgeschlossen", state="complete")
        else:
            status.update(label="❌ Pipeline fehlgeschlagen", state="error")

    # Cache leeren, damit neue Daten geladen werden
    if steps_ok:
        st.cache_data.clear()
        st.success("Daten aktualisiert! Lade die Seite neu, um die neuen Daten zu sehen.")
        if st.button("🔄 Seite neu laden"):
            st.rerun()


# ─────────────────────────────────────────────────────────────────────
# Header mit Aktualisieren-Menü
# ─────────────────────────────────────────────────────────────────────
header_l, header_r = st.columns([5, 1])

with header_l:
    st.title("📊 Data Job Market Germany")
    st.caption(
        "Multi-Source Analyse des deutschen Data-Jobmarkts. "
        "Quellen: Bundesagentur für Arbeit · Adzuna."
    )

with header_r:
    st.markdown("<div style='height:36px;'></div>", unsafe_allow_html=True)
    with st.popover("🔄 Aktualisieren", use_container_width=True):
        st.markdown("##### Daten aktualisieren")
        st.caption("Sammelt neue Jobs und aktualisiert das Dashboard.")

        skip_collect = st.checkbox(
            "Ohne API-Sammlung (nur cleaning)",
            value=False,
            help="Verarbeitet vorhandene Rohdaten neu, ohne neue API-Calls.",
            key="upd_skip_collect",
        )
        use_postgres_now = os.getenv("USE_POSTGRES", "").lower() == "true"
        to_postgres = st.checkbox(
            "PostgreSQL aktualisieren",
            value=use_postgres_now,
            help="Daten zusätzlich in Neon-DB schreiben.",
            key="upd_to_postgres",
        )
        truncate = st.checkbox(
            "Tabellen vorher leeren",
            value=True,
            help="Alte DB-Daten ersetzen (empfohlen).",
            key="upd_truncate",
            disabled=not to_postgres,
        )

        if st.button("Jetzt starten", type="primary",
                      use_container_width=True, key="run_pipeline_btn"):
            run_full_pipeline(skip_collect, to_postgres, truncate)

        st.divider()
        if st.button("Nur Cache leeren", use_container_width=True,
                      key="cache_clear_btn",
                      help="Lädt CSVs/Postgres neu, ohne Pipeline."):
            st.cache_data.clear()
            st.rerun()


# ─────────────────────────────────────────────────────────────────────
# Daten laden
# ─────────────────────────────────────────────────────────────────────
jobs = load_jobs()
skills = load_skills()
jobs_with_skills = load_jobs_with_skills()


# ─────────────────────────────────────────────────────────────────────
# Datenstand-Bar
# ─────────────────────────────────────────────────────────────────────
backend = "PostgreSQL" if os.getenv("USE_POSTGRES", "").lower() == "true" else "CSV"

csv_path = ROOT / "data" / "processed" / "jobs_cleaned.csv"
last_update = "?"
if csv_path.exists():
    try:
        ts = datetime.fromtimestamp(csv_path.stat().st_mtime)
        last_update = ts.strftime("%d.%m.%Y %H:%M")
    except Exception:
        pass

source_summary = ""
if "source" in jobs.columns and not jobs.empty:
    src_counts = jobs["source"].value_counts()
    source_summary = " · ".join(f"{src}: {cnt}" for src, cnt in src_counts.items())

st.info(
    f"📊 **{len(jobs):,} Jobs** geladen "
    f"&nbsp;·&nbsp; Backend: **{backend}** "
    f"&nbsp;·&nbsp; Letzte Aktualisierung: **{last_update}** "
    + (f"&nbsp;·&nbsp; Quellen: {source_summary}" if source_summary else "")
)


# ─────────────────────────────────────────────────────────────────────
# Tab-Navigation mit st.radio (state-persistent!)
# ─────────────────────────────────────────────────────────────────────
TAB_LABELS = ["📊  Marktanalyse", "🔎  Jobsuche", "📚  Methodik"]

selected_tab = st.radio(
    "Navigation",
    options=TAB_LABELS,
    horizontal=True,
    label_visibility="collapsed",
    key="active_tab",
)

st.markdown("<hr style='margin-top:0;margin-bottom:1.5rem;'>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────
# Tab-Inhalt
# ─────────────────────────────────────────────────────────────────────
if selected_tab == TAB_LABELS[0]:
    marktanalyse.render(jobs, skills)
elif selected_tab == TAB_LABELS[1]:
    jobsuche.render(jobs_with_skills)
else:
    methodik.render(jobs, skills)


# ─────────────────────────────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "Built with Python · pandas · Streamlit · Plotly · PostgreSQL  ·  "
    "Daten via Bundesagentur für Arbeit & Adzuna."
)
