"""
ETL: Lädt die bereinigten Jobs und Skills aus den CSVs nach PostgreSQL.

Der Loader ist idempotent – er nutzt INSERT ... ON CONFLICT (UPSERT),
sodass mehrfache Ausführung keine Duplikate erzeugt.

Voraussetzungen:
    1. PostgreSQL läuft (lokal oder remote)
    2. Datenbank existiert (z.B. CREATE DATABASE jobmarket;)
    3. Schema wurde angelegt: psql -d jobmarket -f sql/create_tables.sql
    4. Verbindungsdaten in .env gesetzt (siehe .env.example)

Ausführung:
    python -m src.load_to_postgres

Optional:
    python -m src.load_to_postgres --truncate    # Tabellen vorher leeren
"""

import argparse
import ast
import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError, ProgrammingError

from src.config import PROCESSED_DIR, EXPORT_DIR


load_dotenv()


def _get_config(key: str, default: str = "") -> str:
    """Liest Config aus st.secrets ODER Umgebungsvariable.

    Streamlit Cloud → st.secrets, Lokal → .env via os.getenv.
    Funktioniert auch außerhalb von Streamlit (CLI-Skripte).
    """
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return os.getenv(key, default)


def get_engine() -> Engine:
    """Baut eine SQLAlchemy-Engine aus Umgebungsvariablen oder st.secrets.

    Unterstützt sowohl lokale Postgres als auch Cloud-Provider wie Neon
    (per SSL). Setze POSTGRES_SSLMODE=require für Cloud-Verbindungen.
    """
    host = _get_config("POSTGRES_HOST", "localhost")
    port = _get_config("POSTGRES_PORT", "5432")
    db   = _get_config("POSTGRES_DB", "jobmarket")
    user = _get_config("POSTGRES_USER", "postgres")
    pw   = _get_config("POSTGRES_PASSWORD", "")
    sslmode = _get_config("POSTGRES_SSLMODE", "")

    url = f"postgresql+psycopg2://{user}:{pw}@{host}:{port}/{db}"

    connect_args = {}
    if sslmode:
        connect_args["sslmode"] = sslmode
    # Auto-Erkennung: Neon-Hosts haben "neon.tech" im Namen
    elif "neon.tech" in host:
        connect_args["sslmode"] = "require"

    return create_engine(url, pool_pre_ping=True, connect_args=connect_args)


def parse_skills_field(value) -> list[str]:
    """Konvertiert das skills_found-Feld (CSV-String) in eine Liste."""
    if pd.isna(value) or value == "" or value == "[]":
        return []
    if isinstance(value, list):
        return value
    try:
        parsed = ast.literal_eval(str(value))
        return parsed if isinstance(parsed, list) else []
    except (ValueError, SyntaxError):
        return []


def ensure_schema_up_to_date(engine: Engine) -> None:
    """Führt nötige Schema-Migrationen aus.

    Idempotent — kann beliebig oft aufgerufen werden.
    Prüft Spalten und fügt sie hinzu, falls sie fehlen.
    """
    migrations = [
        # (Spalte existiert nicht? → Migration ausführen)
        ("source", "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS source VARCHAR(50);"),
    ]
    with engine.begin() as conn:
        for column_name, migration_sql in migrations:
            check = conn.execute(text(f"""
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'jobs' AND column_name = '{column_name}';
            """)).fetchone()
            if not check:
                print(f"🔧 Migration: ergänze Spalte '{column_name}' ...")
                conn.execute(text(migration_sql))


def truncate_tables(engine: Engine) -> None:
    """Leert alle Tabellen (CASCADE wegen Foreign Keys)."""
    print("⚠️  Leere alle Tabellen ...")
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE job_skills, skills, jobs RESTART IDENTITY CASCADE;"))
    print("   Tabellen geleert.")


def load_jobs(engine: Engine, jobs_df: pd.DataFrame) -> int:
    """
    Lädt Jobs in die jobs-Tabelle. UPSERT auf job_id (Primary Key).
    Returns: Anzahl betroffener Zeilen.
    """
    # Spalten-Mapping: CSV-Spalte → DB-Spalte
    column_map = {
        "job_id": "job_id",
        "job_title": "job_title",
        "employer_name": "employer_name",
        "job_employment_type": "job_employment_type",
        "job_apply_link": "job_apply_link",
        "job_description": "job_description",
        "job_is_remote": "job_is_remote",
        "job_posted_at": "job_posted_at",
        "job_posted_at_datetime_utc": "job_posted_at_utc",
        "job_location": "job_location",
        "job_city": "job_city",
        "job_state": "job_state",
        "job_country": "job_country",
        "salary_min": "salary_min",
        "salary_max": "salary_max",
        "salary_avg": "salary_avg",
        "job_salary_period": "salary_period",
        "search_term": "search_term",
        "is_junior": "is_junior",
        "remote_type": "remote_type",
        "role_group": "role_group",
        "source": "source",
    }

    # Nur vorhandene Spalten verwenden
    available = {csv_col: db_col for csv_col, db_col in column_map.items()
                 if csv_col in jobs_df.columns}

    df = jobs_df[list(available.keys())].rename(columns=available).copy()

    # Datetime-Spalten sauber parsen (verhindert "NaN ist double" Fehler)
    for dt_col in ("job_posted_at_utc",):
        if dt_col in df.columns:
            df[dt_col] = pd.to_datetime(df[dt_col], errors="coerce", utc=True)
            # NaT → None (psycopg2 versteht None als SQL NULL)
            df[dt_col] = df[dt_col].astype(object).where(df[dt_col].notna(), None)

    # Boolean-Spalte sauber konvertieren
    if "job_is_remote" in df.columns:
        df["job_is_remote"] = df["job_is_remote"].map(
            lambda x: True if str(x).lower() == "true" else
                      False if str(x).lower() == "false" else None
        )

    # NaN → None für alle anderen Spalten (Float NaN würde sonst als 'nan' landen)
    df = df.astype(object).where(pd.notna(df), None)

    # UPSERT-Statement: bei Konflikt auf job_id → Werte aktualisieren
    columns = list(df.columns)
    placeholders = ", ".join(f":{c}" for c in columns)
    update_clause = ", ".join(f"{c} = EXCLUDED.{c}" for c in columns if c != "job_id")

    sql = text(f"""
        INSERT INTO jobs ({', '.join(columns)})
        VALUES ({placeholders})
        ON CONFLICT (job_id) DO UPDATE SET {update_clause};
    """)

    rows = df.to_dict(orient="records")
    with engine.begin() as conn:
        conn.execute(sql, rows)
    return len(rows)


def load_skills_and_relations(engine: Engine, jobs_with_skills_df: pd.DataFrame) -> tuple[int, int]:
    """
    Lädt eindeutige Skills und die m:n-Beziehungen.
    Returns: (Anzahl Skills, Anzahl Job-Skill-Verknüpfungen)
    """
    # Skills aus skills_found extrahieren
    jobs_with_skills_df["skills_list"] = jobs_with_skills_df["skills_found"].apply(parse_skills_field)

    all_skills = set()
    for skills_list in jobs_with_skills_df["skills_list"]:
        all_skills.update(skills_list)

    # 1. Skills upserten (eindeutig)
    skills_data = [{"skill_name": s} for s in sorted(all_skills)]
    if skills_data:
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO skills (skill_name)
                    VALUES (:skill_name)
                    ON CONFLICT (skill_name) DO NOTHING;
                """),
                skills_data,
            )

    # 2. Skill-IDs für die Bridge-Tabelle holen
    with engine.begin() as conn:
        skill_id_map = dict(
            conn.execute(text("SELECT skill_name, skill_id FROM skills")).all()
        )

    # 3. Bridge-Daten aufbauen: (job_id, skill_id) Tupel
    bridge_rows = []
    for _, row in jobs_with_skills_df.iterrows():
        job_id = row["job_id"]
        for skill_name in row["skills_list"]:
            skill_id = skill_id_map.get(skill_name)
            if skill_id is not None:
                bridge_rows.append({"job_id": job_id, "skill_id": skill_id})

    if bridge_rows:
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO job_skills (job_id, skill_id)
                    VALUES (:job_id, :skill_id)
                    ON CONFLICT (job_id, skill_id) DO NOTHING;
                """),
                bridge_rows,
            )

    return len(skills_data), len(bridge_rows)


def main(truncate: bool = False) -> None:
    print("=" * 60)
    print("ETL: CSV -> PostgreSQL")
    print("=" * 60)

    # 1. Daten lesen
    jobs_path = PROCESSED_DIR / "jobs_cleaned.csv"
    skills_path = EXPORT_DIR / "jobs_with_skills.csv"

    if not jobs_path.exists():
        print(f"❌ Datei nicht gefunden: {jobs_path}")
        print("   Bitte zuerst die Pipeline ausführen:")
        print("   python -m src.collect_jobs && python -m src.clean_jobs")
        sys.exit(1)

    if not skills_path.exists():
        print(f"❌ Datei nicht gefunden: {skills_path}")
        print("   Bitte zuerst python -m src.extract_skills ausführen.")
        sys.exit(1)

    jobs_df = pd.read_csv(jobs_path)
    jobs_with_skills_df = pd.read_csv(skills_path)
    print(f"📂 Jobs: {len(jobs_df)} Zeilen")
    print(f"📂 Jobs mit Skills: {len(jobs_with_skills_df)} Zeilen")

    # 2. DB-Verbindung
    print("\n🔌 Verbinde mit PostgreSQL ...")
    engine = get_engine()
    try:
        with engine.connect() as conn:
            version = conn.execute(text("SELECT version();")).scalar()
            print(f"   Verbunden: {version[:60]}...")
    except OperationalError as e:
        print(f"❌ Verbindung fehlgeschlagen: {e}")
        print("\nMögliche Ursachen:")
        print("   - PostgreSQL läuft nicht")
        print("   - Falsche Credentials in .env")
        print("   - Datenbank existiert nicht (CREATE DATABASE jobmarket;)")
        sys.exit(1)

    # 3. Schema-Migrationen prüfen
    try:
        ensure_schema_up_to_date(engine)
    except Exception as e:
        print(f"⚠️  Schema-Migration übersprungen ({e})")

    # 4. Optional: Tabellen leeren
    if truncate:
        try:
            truncate_tables(engine)
        except ProgrammingError:
            print("❌ Tabellen existieren nicht. Bitte zuerst:")
            print("   psql -d jobmarket -f sql/create_tables.sql")
            sys.exit(1)

    # 4. Jobs laden
    print("\n📤 Lade Jobs ...")
    try:
        n_jobs = load_jobs(engine, jobs_df)
        print(f"   {n_jobs} Jobs geladen / aktualisiert.")
    except ProgrammingError as e:
        print(f"❌ Tabellen existieren nicht: {e}")
        print("   Bitte zuerst: psql -d jobmarket -f sql/create_tables.sql")
        sys.exit(1)

    # 5. Skills + Beziehungen laden
    print("\n📤 Lade Skills und Beziehungen ...")
    n_skills, n_relations = load_skills_and_relations(engine, jobs_with_skills_df)
    print(f"   {n_skills} Skills geladen.")
    print(f"   {n_relations} Job-Skill-Verknüpfungen geladen.")

    # 6. Validierung
    print("\n✅ Validierung:")
    with engine.connect() as conn:
        for table in ["jobs", "skills", "job_skills"]:
            count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            print(f"   {table}: {count} Zeilen")

    print("\n🎉 ETL erfolgreich abgeschlossen.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lädt CSV-Daten in Postgres.")
    parser.add_argument(
        "--truncate",
        action="store_true",
        help="Vor dem Laden alle Tabellen leeren.",
    )
    args = parser.parse_args()
    main(truncate=args.truncate)
