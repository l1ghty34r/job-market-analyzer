"""
Bereinigt und reichert die Roh-Jobdaten an (Multi-Source: Arbeitsagentur, Adzuna).

Schritte:
1. Auswahl relevanter Spalten
2. Schema-Migration für Legacy-Daten
3. Deduplizierung über job_id
4. Bereinigung von Textfeldern
5. Stadt-Extraktion (aus location, description als Fallback)
6. Salary-Extraktion (aus salary_string und description)
7. Feature-Engineering: is_junior, remote_type, role_group
8. Speicherung als data/processed/jobs_cleaned.csv
"""

import re
from pathlib import Path

import pandas as pd

from src.config import RAW_DIR, PROCESSED_DIR


JUNIOR_KEYWORDS = [
    "junior", "entry level", "graduate", "trainee",
    "berufseinstieg", "absolvent", "einsteiger",
]

REMOTE_KEYWORDS = [
    # Englisch
    "remote", "fully remote", "100% remote", "remote work",
    "home office", "home-office", "homeoffice",
    "mobile work", "work from home", "wfh",
    # Deutsch
    "mobiles arbeiten", "mobile arbeit", "mobile-work",
    "homeoffice-möglichkeit", "home-office-möglichkeit",
    "ortsunabhängig", "ortsungebunden", "ortsflexibel",
    "von zuhause", "von zu hause", "im home-office",
    "tele-arbeit", "telearbeit",
    # Hybrid-Varianten (zählen für unseren "Remote/Homeoffice"-Filter mit)
    "hybrid", "hybrides arbeiten", "hybride arbeit",
    "flexible arbeitsorte", "flexibler arbeitsort",
]

PURE_REMOTE_KEYWORDS = [
    "fully remote", "100% remote", "remote-first", "remote first",
    "vollremote", "voll remote", "komplett remote",
    "ortsunabhängig", "work from anywhere",
]

# Größte deutsche Städte für Fallback-Erkennung in Beschreibungen
GERMAN_CITIES = [
    "Berlin", "Hamburg", "München", "Köln", "Frankfurt am Main", "Frankfurt",
    "Stuttgart", "Düsseldorf", "Leipzig", "Dortmund", "Essen", "Bremen",
    "Dresden", "Hannover", "Nürnberg", "Duisburg", "Bochum", "Wuppertal",
    "Bielefeld", "Bonn", "Münster", "Karlsruhe", "Mannheim", "Augsburg",
    "Wiesbaden", "Mönchengladbach", "Gelsenkirchen", "Aachen", "Braunschweig",
    "Kiel", "Chemnitz", "Halle", "Magdeburg", "Freiburg", "Krefeld",
    "Mainz", "Lübeck", "Erfurt", "Oberhausen", "Rostock", "Kassel",
    "Hagen", "Saarbrücken", "Potsdam", "Heidelberg", "Regensburg",
    "Darmstadt", "Würzburg", "Göttingen", "Wolfsburg", "Ingolstadt",
    "Ulm", "Heilbronn", "Pforzheim", "Offenbach", "Bottrop", "Fürth",
    "Reutlingen", "Bremerhaven", "Koblenz", "Bergisch Gladbach", "Trier",
    "Recklinghausen", "Erlangen", "Jena", "Salzgitter", "Siegen", "Hildesheim",
    "Cottbus", "Osnabrück", "Solingen",
]


def get_latest_raw_file() -> Path:
    """Findet die zu verwendende Roh-CSV.

    Priorität:
    1. jobs_raw_master.csv (akkumulierte Daten aller Läufe)
    2. Neueste jobs_raw_<timestamp>.csv als Fallback
    """
    master_file = RAW_DIR / "jobs_raw_master.csv"
    if master_file.exists():
        return master_file

    files = sorted(RAW_DIR.glob("jobs_raw_2*.csv"))
    if not files:
        raise FileNotFoundError("Keine Rohdaten-Datei gefunden.")
    return files[-1]


def classify_junior(text: str) -> int:
    """1 wenn Junior/Trainee/Berufseinstieg im Text, sonst 0."""
    text = str(text).lower()
    return int(any(keyword in text for keyword in JUNIOR_KEYWORDS))


def classify_remote_type(job_is_remote, text: str) -> str:
    """Klassifiziert die Arbeitsform.

    Returns: 'Remote' / 'Hybrid' / 'Remote/Hybrid erwähnt' / 'Onsite/Unknown'

    Erkennt auch deutsche Begriffe wie 'mobiles Arbeiten', 'Homeoffice',
    'ortsunabhängig' etc.
    """
    text = str(text).lower()
    is_remote = str(job_is_remote).lower() == "true"

    # API-Flag: explizit Remote
    if is_remote:
        if "hybrid" in text:
            return "Hybrid"
        return "Remote"

    # Im Text nach 'pure remote'-Indikatoren suchen
    if any(kw in text for kw in PURE_REMOTE_KEYWORDS):
        return "Remote"

    # 'Hybrid' explizit erwähnt?
    if "hybrid" in text:
        return "Hybrid"

    # Andere Remote-/Homeoffice-Hinweise (mobiles Arbeiten, Homeoffice etc.)
    if any(kw in text for kw in REMOTE_KEYWORDS):
        return "Remote/Hybrid erwähnt"

    return "Onsite/Unknown"


def detect_remote_friendly(text: str) -> bool:
    """Erkennt ob der Job-Text Remote/Homeoffice/mobiles Arbeiten erwähnt.

    Wird für den 'Remote/Homeoffice'-Filter verwendet (lockerer als
    classify_remote_type, fängt alle Hinweise ein).
    """
    text = str(text).lower()
    return any(kw in text for kw in REMOTE_KEYWORDS)


def assign_role_group(title: str, description: str = "") -> str:
    """Gruppiert Job-Titel in Rollen-Cluster.

    Sehr breite Erkennung für Data/Analytics-Jobs - inklusive deutscher
    Bezeichnungen und unscharfer Treffer im Titel UND in der Beschreibung.
    """
    title_lower = str(title).lower()
    text_lower = title_lower + " " + str(description)[:500].lower()

    # === Klassische Rollen (spezifischer zuerst) ===
    if "data analyst" in title_lower or "datenanalyst" in title_lower:
        return "Data Analyst"
    if "data scientist" in title_lower or "datenwissenschaftler" in title_lower:
        return "Data Scientist"
    if "data engineer" in title_lower or "dateningenieur" in title_lower:
        return "Data Engineer"
    if ("business intelligence" in title_lower or "bi analyst" in title_lower
            or "bi-analyst" in title_lower or "bi developer" in title_lower
            or "bi entwickler" in title_lower or "bi-entwickler" in title_lower
            or "bi-spezialist" in title_lower or "bi spezialist" in title_lower
            or "bi-berater" in title_lower or "bi berater" in title_lower
            or "bi consultant" in title_lower):
        return "BI Analyst"
    if ("machine learning engineer" in title_lower or "ml engineer" in title_lower
            or "ml-engineer" in title_lower):
        return "ML Engineer"
    if "analytics engineer" in title_lower:
        return "Analytics Engineer"

    # === Erweiterte Erkennung im Titel ===
    if "reporting" in title_lower:
        return "Reporting Analyst"
    if "controller" in title_lower and (
        "analytic" in text_lower or "data" in text_lower
        or " bi " in text_lower or "reporting" in text_lower
        or "auswertung" in text_lower
    ):
        return "Analytics Controller"
    if "kpi" in title_lower or "performance analyst" in title_lower:
        return "Performance Analyst"
    if "statistik" in title_lower or "statistician" in title_lower:
        return "Statistiker"
    if "operations research" in title_lower or "or analyst" in title_lower:
        return "Operations Research"

    # === HARTE AUSSCHLÜSSE: Engineer-Titel die NICHT Data sind ===
    # (Maschinenbau, E-Technik, Bauwesen, etc.)
    excluded_engineer_kinds = [
        "commercial engineer", "mechanical engineer", "thermal engineer",
        "industrial engineer", "electrical engineer", "civil engineer",
        "chemical engineer", "vehicle", "automotive engineer", "aerospace engineer",
        "process engineer", "manufacturing engineer", "production engineer",
        "quality engineer", "test engineer", "design engineer",
        "maschinenbauingenieur", "elektroingenieur", "verfahrensingenieur",
        "konstruktionsingenieur", "fertigungsingenieur",
    ]
    if any(kind in title_lower for kind in excluded_engineer_kinds):
        return "Other"

    # === Sehr breite Heuristik im Titel (Data-Begriffe) ===
    en_terms = [
        "data ", " data", "analyst", "analytics", "analytic",
        "machine learning", "deep learning", " ai ", "ai-", "ai/",
        "artificial intelligence", "data science", " bi ", "bi-",
        "data engineer", "data scientist", "data architect",
        "etl", "data warehouse", "datawarehouse", "data lake",
        "data platform", "data pipeline", "data ops", "dataops",
        "process mining", "business analysis", "business analyst",
        "genai", "gen-ai", "gen ai", "llm engineer", "nlp ",
        "snowflake", "databricks", "tableau", "power bi", "powerbi",
        " sac ", "sap analytics", "looker",
    ]
    de_terms = [
        "daten", "analyse", "analytisch", "auswertung",
        "berichtswesen", "kennzahl", "datenmanagement",
        "datenwissenschaft", "stochastik",
        "künstliche intelligenz", "kuenstliche intelligenz",
        "ki-", "ki/", "ki ", "datenbank-administrator",
        "datenbankadministrator", "dwh", " bi-", " bi ",
    ]
    padded_title = f" {title_lower} "
    if any(term in padded_title for term in en_terms + de_terms):
        return "Other Data/Analytics"

    # === Cloud/DevOps NUR mit Data-Bezug ===
    if "cloud engineer" in title_lower or "cloud architect" in title_lower:
        if any(t in text_lower for t in ["data", "analytics", "warehouse",
                                          "snowflake", "databricks", "etl",
                                          "pipeline", "lake"]):
            return "Other Data/Analytics"

    if "devops" in title_lower:
        if any(t in text_lower for t in ["data", "analytics", "ml", "ai",
                                          "dataops", "machine learning"]):
            return "Other Data/Analytics"

    # === Letzter Versuch: Description durchsuchen ===
    if any(term in text_lower for term in [
        "data analyst", "data scientist", "datenanalyse", "datenanalyst",
        "business intelligence", "machine learning",
    ]):
        return "Other Data/Analytics"

    return "Other"


def extract_city(job_city: str, job_location: str, description: str) -> str:
    """
    Extrahiert die Stadt aus mehreren Quellen.

    Priorität:
    1. job_city (falls nicht 'Unbekannt' oder leer)
    2. job_location (Teil vor '•' oder Komma)
    3. Erste deutsche Stadt, die im ersten Description-Abschnitt vorkommt
    """
    # 1. job_city
    city = str(job_city).strip()
    if city and city.lower() not in ("unbekannt", "nan", "deutschland", "beliebiger ort"):
        return city

    # 2. job_location: oft "Berlin   •   über Indeed"
    loc = str(job_location).strip()
    if loc:
        # Nur den Teil vor "•" oder dem Wort "über"
        loc_clean = re.split(r"[•·]|\büber\b", loc)[0].strip()
        # Wenn das ein konkreter Ort ist (nicht "Deutschland" oder "Beliebiger Ort")
        if loc_clean and loc_clean.lower() not in (
            "deutschland", "beliebiger ort", "germany", ""
        ):
            # Falls "Stadt, Bundesland" → nur Stadt
            if "," in loc_clean:
                loc_clean = loc_clean.split(",")[0].strip()
            return loc_clean

    # 3. Description: erste deutsche Stadt im Vorspann (erste 500 Zeichen)
    desc_start = str(description)[:500]
    for german_city in GERMAN_CITIES:
        # Wortgrenzen, damit "Bonn" nicht in "Abonnement" matcht
        pattern = r"\b" + re.escape(german_city) + r"\b"
        if re.search(pattern, desc_start, re.IGNORECASE):
            return german_city

    return "Unbekannt"


def extract_salary_from_text(text: str) -> tuple[float | None, float | None]:
    """
    Extrahiert min/max Jahresgehalt aus Text.

    Erkennt Muster wie:
    - 'EUR 45000 - 65000 per year'
    - '45.000 - 65.000 EUR'
    - '€45,000 - €65,000'
    """
    text = str(text)

    # Muster: Zahl - Zahl (mit optionalem EUR/€ und Tausender-Trennzeichen)
    patterns = [
        r"EUR\s*(\d{2,3}[.,]?\d{3})\s*[-–]\s*(\d{2,3}[.,]?\d{3})",
        r"€\s*(\d{2,3}[.,]?\d{3})\s*[-–]\s*€?\s*(\d{2,3}[.,]?\d{3})",
        r"(\d{2,3}[.,]?\d{3})\s*[-–]\s*(\d{2,3}[.,]?\d{3})\s*(?:EUR|€)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                min_val = float(match.group(1).replace(".", "").replace(",", ""))
                max_val = float(match.group(2).replace(".", "").replace(",", ""))
                # Plausibilitäts-Check: zwischen 20k und 250k Jahresgehalt
                if 20000 <= min_val <= 250000 and 20000 <= max_val <= 250000:
                    return min_val, max_val
            except ValueError:
                continue

    return None, None


def main() -> None:
    input_file = get_latest_raw_file()
    print(f"Verwende Rohdatei: {input_file}")

    df = pd.read_csv(input_file)
    print(f"Anzahl Datensätze in Rohdatei: {len(df)}")

    # Schema-Migration: Legacy-JSearch-Spalten auf UnifiedJob-Schema mappen
    # Legacy → Neu
    if "job_min_salary" in df.columns and "salary_min" not in df.columns:
        df = df.rename(columns={
            "job_min_salary": "salary_min",
            "job_max_salary": "salary_max",
            "job_salary_period": "salary_period",
        })
    elif "job_min_salary" in df.columns and "salary_min" in df.columns:
        # Beide Spalten existieren (nach Mehrfach-Sammlung) – fülle salary_min aus job_min_salary auf
        df["salary_min"] = df["salary_min"].combine_first(df["job_min_salary"])
        df["salary_max"] = df["salary_max"].combine_first(df["job_max_salary"])

    # source-Spalte für Legacy-Daten ohne Quelle ergänzen
    if "source" not in df.columns:
        df["source"] = "jsearch"  # Legacy-Daten kamen alle aus JSearch
    else:
        df["source"] = df["source"].fillna("jsearch")

    # Legacy: alte JSearch-Daten herausfiltern (Quelle wird nicht mehr genutzt)
    before = len(df)
    df = df[df["source"] != "jsearch"].copy()
    if before != len(df):
        print(f"Legacy-JSearch-Zeilen entfernt: {before - len(df)}")

    keep_cols = [
        "job_id", "job_title", "employer_name", "source",
        "job_employment_type", "job_apply_link", "job_description",
        "job_is_remote", "job_posted_at", "job_posted_at_datetime_utc",
        "job_location", "job_city", "job_state", "job_country",
        "salary_min", "salary_max", "salary_period",
        "job_salary_string",  # nur in alten Daten, für Salary-Text-Extraktion
        "search_term",
    ]
    available_cols = [col for col in keep_cols if col in df.columns]
    df = df[available_cols].copy()

    # Deduplizieren über job_id
    if "job_id" in df.columns:
        before = len(df)
        df = df.drop_duplicates(subset=["job_id"]).copy()
        print(f"Nach Deduplizierung: {len(df)} (entfernt: {before - len(df)})")

    # Textfelder bereinigen
    text_cols = [
        "job_title", "employer_name", "job_employment_type",
        "job_description", "job_location", "job_city", "job_state",
        "job_country", "job_salary_string", "search_term",
    ]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()

    # Verbesserte Stadt-Extraktion
    df["job_city"] = df.apply(
        lambda row: extract_city(
            row.get("job_city", ""),
            row.get("job_location", ""),
            row.get("job_description", ""),
        ),
        axis=1,
    )

    # Bundesland-Fallback
    if "job_state" in df.columns:
        df["job_state"] = df["job_state"].replace("", "Unbekannt")

    # Kombinierter Text NUR intern, nicht in Output speichern
    combined_text = (
        df.get("job_title", "").fillna("").astype(str) + " "
        + df.get("job_description", "").fillna("").astype(str)
    )

    # Feature-Engineering
    df["is_junior"] = combined_text.apply(classify_junior)
    df["remote_type"] = df.apply(
        lambda row: classify_remote_type(
            row.get("job_is_remote", ""),
            f"{row.get('job_title', '')} {row.get('job_description', '')}",
        ),
        axis=1,
    )
    # is_remote_friendly = Boolean-Flag für den Filter "Remote/Homeoffice"
    # Erkennt deutsche und englische Begriffe (Homeoffice, mobiles Arbeiten, etc.)
    df["is_remote_friendly"] = combined_text.apply(detect_remote_friendly)
    df["role_group"] = df.apply(
        lambda row: assign_role_group(
            row.get("job_title", ""),
            row.get("job_description", ""),
        ),
        axis=1,
    )

    # Datumsformat: einheitliches job_posted_at_datetime_utc bauen
    # Quellen liefern das Datum unterschiedlich:
    # - JSearch:        job_posted_at_datetime_utc (ISO-String)
    # - Arbeitsagentur: job_posted_at (z.B. "2026-04-29")
    # - Adzuna:         job_posted_at (ISO-String)
    if "job_posted_at_datetime_utc" not in df.columns:
        df["job_posted_at_datetime_utc"] = pd.NaT

    df["job_posted_at_datetime_utc"] = pd.to_datetime(
        df["job_posted_at_datetime_utc"], errors="coerce", utc=True
    )

    # Wo das Feld leer ist, aus job_posted_at parsen
    if "job_posted_at" in df.columns:
        fallback = pd.to_datetime(df["job_posted_at"], errors="coerce", utc=True)
        df["job_posted_at_datetime_utc"] = df["job_posted_at_datetime_utc"].fillna(
            fallback
        )

    # Salary-Felder zu Numbers konvertieren
    for col in ["salary_min", "salary_max"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Wenn min/max leer sind, aus Text extrahieren (description + ggf. Legacy-salary_string)
    salary_text_source = df.get("job_description", pd.Series("", index=df.index)).fillna("").astype(str)
    if "job_salary_string" in df.columns:
        salary_text_source = df["job_salary_string"].fillna("").astype(str) + " " + salary_text_source

    extracted = salary_text_source.apply(extract_salary_from_text)
    df["salary_min_extracted"] = [e[0] for e in extracted]
    df["salary_max_extracted"] = [e[1] for e in extracted]

    # Finale Werte: bevorzuge API-Wert, fallback auf extrahierten
    df["salary_min"] = df.get("salary_min").combine_first(df["salary_min_extracted"])
    df["salary_max"] = df.get("salary_max").combine_first(df["salary_max_extracted"])
    df["salary_avg"] = df[["salary_min", "salary_max"]].mean(axis=1)

    # Aufräumen: temporäre Extracted-Spalten entfernen
    df = df.drop(columns=["salary_min_extracted", "salary_max_extracted"])
    if "job_salary_string" in df.columns:
        df = df.drop(columns=["job_salary_string"])

    # Sortierung
    sort_cols = [c for c in ["job_posted_at_datetime_utc", "job_title"] if c in df.columns]
    if sort_cols:
        df = df.sort_values(sort_cols, ascending=[False] * len(sort_cols)).copy()

    output_file = PROCESSED_DIR / "jobs_cleaned.csv"
    df.to_csv(output_file, index=False)

    print("\n--- Cleaning abgeschlossen ---")
    print(f"Datei gespeichert: {output_file}")
    print(f"Anzahl Datensätze: {len(df)}")
    print("\nVerteilung role_group:")
    print(df["role_group"].value_counts(dropna=False))
    print("\nVerteilung remote_type:")
    print(df["remote_type"].value_counts(dropna=False))
    print("\nJunior-Verteilung:")
    print(df["is_junior"].value_counts(dropna=False))
    print(f"\nStädte erkannt (nicht 'Unbekannt'): "
          f"{(df['job_city'] != 'Unbekannt').sum()} / {len(df)}")
    print(f"Salary-Daten gefunden: {df['salary_avg'].notna().sum()} / {len(df)}")


if __name__ == "__main__":
    main()
