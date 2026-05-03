from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
EXPORT_DIR = DATA_DIR / "exports"

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


# ----------------------------------------------------------------------------
# Datenbank-Konfiguration (optional, nur für Postgres-Demo)
# ----------------------------------------------------------------------------
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "database": os.getenv("POSTGRES_DB", "jobmarket"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", ""),
}


# ----------------------------------------------------------------------------
# ----------------------------------------------------------------------------
# Such-Konfiguration für die Job-APIs
# ----------------------------------------------------------------------------

SEARCH_TERMS = [
    # Kern-Rollen
    "data analyst",
    "data scientist",
    "data engineer",
    "business intelligence",
    "machine learning",
    "analytics engineer",
    # Junior-Varianten (separate Suchbegriffe finden mehr)
    "junior data analyst",
    # Verwandte Rollen, die oft auch zu Data-Profilen passen
    "bi analyst",
    "reporting analyst",
    "controller analytics",
]

# Berufsfeld-Filter für Arbeitsagentur (offizielle Klassifikation)
# Damit findet man auch Jobs, die "data" nicht im Titel haben
ARBEITSAGENTUR_BERUFSFELDER = [
    "Informatik, Information und Kommunikation",
    "Mathematik, Biologie, Chemie, Physik",
]

SKILL_KEYWORDS = [
    "python",
    "sql",
    "postgresql",
    "power bi",
    "tableau",
    "looker",
    "excel",
    "git",
    "aws",
    "azure",
    "gcp",
    "spark",
    "airflow",
    "docker",
    "kubernetes",
    "machine learning",
    "deep learning",
    "statistics",
    "etl",
    "dbt",
    "snowflake",
    "redshift",
    "bigquery",
    "databricks",
    "pandas",
    "numpy",
    "scikit-learn",
    "tensorflow",
    "pytorch",
    "streamlit",
    "ga4",
    "r",
    "scala",
]