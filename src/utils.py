"""
Zentrale Utility-Funktionen für das Job Market Analyzer Dashboard.

Bietet gecachte Daten-Loader für alle Streamlit-Pages und
gemeinsame Helper-Funktionen.

Backend-Switch:
    Wenn die Umgebungsvariable USE_POSTGRES=true gesetzt ist und Postgres
    erreichbar ist, werden die Daten aus der DB geladen. Sonst aus CSVs.
    Standard: CSV (funktioniert ohne DB-Setup).
"""

import os
from pathlib import Path

import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
EXPORT_DIR = BASE_DIR / "data" / "exports"


def _get_config(key: str, default: str = "") -> str:
    """Liest Konfiguration aus st.secrets ODER Umgebungsvariable.

    Auf Streamlit Cloud kommt die Config über st.secrets.
    Lokal über .env (via os.getenv).
    """
    # Erst st.secrets versuchen (Streamlit Cloud)
    try:
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    # Fallback: Umgebungsvariable
    return os.getenv(key, default)


USE_POSTGRES = _get_config("USE_POSTGRES", "false").lower() == "true"


def _try_postgres_engine():
    """Versucht eine Postgres-Engine zu bauen. Bei Fehler: None zurückgeben."""
    if not USE_POSTGRES:
        return None
    try:
        from src.load_to_postgres import get_engine
        engine = get_engine()
        # Kurzer Verbindungstest
        with engine.connect() as conn:
            from sqlalchemy import text
            conn.execute(text("SELECT 1"))
        return engine
    except Exception as e:
        st.warning(
            f"⚠️ Postgres nicht erreichbar ({e.__class__.__name__}). "
            "Falle zurück auf CSV."
        )
        return None



@st.cache_data(ttl=3600)
def load_jobs() -> pd.DataFrame:
    """Lädt die bereinigten Jobs als DataFrame (gecacht für 1 Stunde).

    Liest aus Postgres wenn USE_POSTGRES=true, sonst aus CSV.
    """
    engine = _try_postgres_engine()
    if engine is not None:
        df = pd.read_sql("SELECT * FROM jobs", engine)
        if "job_posted_at_utc" in df.columns:
            df = df.rename(columns={"job_posted_at_utc": "job_posted_at_datetime_utc"})
        return df

    path = PROCESSED_DIR / "jobs_cleaned.csv"
    if not path.exists():
        st.error(
            f"Datei nicht gefunden: {path}\n\n"
            "Bitte zuerst die Pipeline ausführen:\n"
            "1. `python -m src.collect_jobs`\n"
            "2. `python -m src.clean_jobs`\n"
            "3. `python -m src.extract_skills`"
        )
        st.stop()

    df = pd.read_csv(path)

    # Datumsfelder parsen
    if "job_posted_at_datetime_utc" in df.columns:
        df["job_posted_at_datetime_utc"] = pd.to_datetime(
            df["job_posted_at_datetime_utc"], errors="coerce", utc=True
        )

    return df


@st.cache_data(ttl=3600)
def load_skills() -> pd.DataFrame:
    """Lädt die normalisierte Skill-Tabelle (gecacht für 1 Stunde)."""
    engine = _try_postgres_engine()
    if engine is not None:
        df = pd.read_sql("SELECT * FROM v_jobs_with_skills WHERE skill_name IS NOT NULL", engine)
        return df.rename(columns={"skill_name": "skill"})

    path = EXPORT_DIR / "job_skills.csv"
    if not path.exists():
        st.error(
            f"Datei nicht gefunden: {path}\n\n"
            "Bitte zuerst `python -m src.extract_skills` ausführen."
        )
        st.stop()

    return pd.read_csv(path)


@st.cache_data(ttl=3600)
def load_jobs_with_skills() -> pd.DataFrame:
    """Lädt Jobs inklusive ihrer Skill-Listen (gecacht für 1 Stunde)."""
    path = EXPORT_DIR / "jobs_with_skills.csv"
    if not path.exists():
        st.error(
            f"Datei nicht gefunden: {path}\n\n"
            "Bitte zuerst `python -m src.extract_skills` ausführen."
        )
        st.stop()

    return pd.read_csv(path)


def kpi_metrics(jobs: pd.DataFrame, skills: pd.DataFrame) -> dict:
    """Berechnet die wichtigsten KPIs für Header-Metriken."""
    return {
        "total_jobs": len(jobs),
        "unique_employers": jobs["employer_name"].nunique() if "employer_name" in jobs.columns else 0,
        "junior_jobs": int(jobs["is_junior"].sum()) if "is_junior" in jobs.columns else 0,
        "remote_jobs": int((jobs["remote_type"] == "Remote").sum()) if "remote_type" in jobs.columns else 0,
        "unique_skills": skills["skill"].nunique() if not skills.empty else 0,
        "skill_mentions": len(skills),
    }


def format_number(n: int) -> str:
    """Formatiert Zahlen mit Tausender-Trennzeichen (deutsches Format)."""
    return f"{n:,}".replace(",", ".")
