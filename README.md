# 📊 Data Job Market Germany

> Multi-Source ETL-Pipeline und interaktives Dashboard zur Analyse des deutschen Data-Jobmarkts — mit Fokus auf Homeoffice-Stellen.

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-336791?logo=postgresql&logoColor=white)](https://neon.tech)
[![GitHub Actions](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF?logo=github-actions&logoColor=white)](https://github.com/features/actions)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

🌐 **Live-Demo:** [data-job-market-de.streamlit.app](https://data-job-market-de.streamlit.app)

---

## 🎯 Worum geht's?

Wer einen Data-Job in Deutschland sucht, steht vor einem Datenproblem: Stellenangebote sind über LinkedIn, Indeed, StepStone, Arbeitsagentur und unzählige andere Plattformen verteilt. Eine **systematische Marktübersicht** existiert nicht.

Dieses Projekt löst das mit einer kompletten Datenpipeline:

- **Sammelt** Stellenangebote aus zwei kostenlosen APIs (Bundesagentur für Arbeit + Adzuna)
- **Bereinigt** und reichert sie an (Stadt-Extraktion, Skill-Detection, Junior/Remote-Klassifikation)
- **Speichert** in PostgreSQL (Neon Cloud) — optional, lokales CSV reicht auch
- **Visualisiert** in einem Streamlit-Dashboard mit Filter, Suche und Markt-Insights
- **Aktualisiert** sich täglich automatisch über GitHub Actions

**Zielgruppe:** Berufseinsteiger:innen und erfahrene Data-Profis, die einen **Homeoffice-Job in Deutschland** suchen — und wissen wollen, wo die besten Chancen liegen.

---

## ✨ Features

| Feature | Beschreibung |
|---|---|
| 🔄 **Multi-Source-Pipeline** | Bundesagentur für Arbeit + Adzuna mit einheitlichem Schema |
| 🏠 **Homeoffice-Erkennung** | 14 Regex-Patterns für deutsche und englische Begriffe (`mobiles Arbeiten`, `Homeoffice`, `ortsunabhängig`, ...) |
| 🛠️ **Skill-Extraktion** | Wortgrenzen-basiertes Matching mit Synonym-Mapping (z.B. `powerbi` → `power bi`) |
| 💼 **Rollen-Klassifikation** | 12 Cluster (Data Analyst, Scientist, Engineer, BI, ML, Reporting, ...) |
| 📊 **Markt-Analyse** | Homeoffice-Quote pro Rolle, Top-Arbeitgeber, Skill-Heatmaps |
| 🔍 **Job-Suche** | Filterbar nach Rolle, Stadt, Remote, Junior-Level, Skills |
| 🚀 **CI/CD** | GitHub Actions Pipeline läuft täglich um 4 Uhr morgens automatisch |
| 🔁 **Live-Pipeline-Trigger** | Cloud-App kann GitHub Actions on-demand auslösen mit Auto-Polling |
| 🗄️ **PostgreSQL-Backend** | Schema-Auto-Migration bei jedem Lauf |
| 📓 **Jupyter-Notebooks** | 4 dokumentierte Notebooks zum Pipeline-Workflow und Markt-Insights |

---

## 🏗️ Architektur

```
┌────────────────────┐     ┌──────────────────────┐     ┌──────────────────────┐
│ Multi-Source-APIs  │  →  │ ETL & Cleaning       │  →  │ PostgreSQL (Neon)    │
│                    │     │                      │     │                      │
│ • Arbeitsagentur   │     │ • Dedup über job_id  │     │ • jobs               │
│ • Adzuna           │     │ • Stadt-Extraktion   │     │ • skills             │
│                    │     │ • Skill-Extraktion   │     │ • job_skills         │
│  → UnifiedJob      │     │ • Rollen-Cluster     │     │                      │
│                    │     │ • Remote-Detection   │     │  ↓                   │
└────────────────────┘     └──────────────────────┘     └──────────────────────┘
         ↑                                                          ↓
         │                                                ┌──────────────────────┐
         │                                                │ Streamlit Dashboard  │
         │                                                │ (auf Streamlit Cloud)│
         │                                                └──────────────────────┘
         │                                                          ↑
         │ ┌────────────────────────┐                              │
         └─│ GitHub Actions         │──────────────────────────────┘
           │ (täglich + on-demand)  │   triggers via API
           └────────────────────────┘
```

### Projektstruktur

```
job-market-analyzer/
├── .github/workflows/
│   └── update-data.yml      # CI/CD: tägliche Pipeline + manueller Trigger
├── app/                     # Streamlit-Dashboard
│   ├── main.py              # Entry-Point, Cloud/Lokal-Detection
│   ├── tabs/                # 3 Tabs: Jobsuche, Marktanalyse, Methodik
│   └── components/          # Wiederverwendbare Plotly-Charts
├── src/                     # Pipeline-Code
│   ├── sources/             # API-Clients (abstract base + concrete)
│   ├── collect_jobs.py      # Multi-Source Collector
│   ├── clean_jobs.py        # ETL + Feature Engineering
│   ├── extract_skills.py    # Skill-Detection mit Regex
│   ├── load_to_postgres.py  # ETL nach Neon + Schema-Migration
│   ├── geo.py               # Stadt → Region Lookup
│   └── remote_filter.py     # Live Remote-Erkennung (3-fach-Sicherheit)
├── sql/                     # Schema + Analysis-Queries
├── notebooks/               # 4 Jupyter-Notebooks
├── .streamlit/
│   └── config.toml          # Modernes dunkles Theme
└── data/                    # CSVs (raw + processed) — gitignored
```

---

## 🚀 Quick Start

### 1. Setup

```bash
git clone https://github.com/l1ghty34r/job-market-analyzer.git
cd job-market-analyzer

python -m venv .venv
.venv\Scripts\activate              # Windows
# source .venv/bin/activate         # Linux/Mac

pip install -r requirements.txt
```

### 2. Konfiguration

```bash
cp .env.example .env
```

Die `.env`-Datei ausfüllen:

```env
# Adzuna (kostenlos: https://developer.adzuna.com)
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key

# Optional: PostgreSQL (Neon Cloud)
USE_POSTGRES=false
POSTGRES_HOST=ep-xxx.eu-central-1.aws.neon.tech
POSTGRES_PORT=5432
POSTGRES_DB=jobmarket
POSTGRES_USER=...
POSTGRES_PASSWORD=...
```

> **Bundesagentur für Arbeit** braucht keine eigenen Credentials — die nutzt einen öffentlichen API-Key.

### 3. Pipeline ausführen

```bash
python -m src.collect_jobs           # Daten sammeln (5–10 min)
python -m src.clean_jobs             # Bereinigen
python -m src.extract_skills         # Skills extrahieren
python -m src.load_to_postgres --truncate   # Optional: in Postgres laden
```

### 4. Dashboard starten

```bash
streamlit run app/main.py
```

→ <http://localhost:8501>

---

## ☁️ Streamlit Cloud Deployment

Vollständige Anleitung in [`DEPLOYMENT.md`](DEPLOYMENT.md). Die Kurzfassung:

1. Repo public auf GitHub pushen
2. Auf [streamlit.io/cloud](https://streamlit.io/cloud) neue App erstellen
3. **Secrets** im TOML-Format eintragen (Adzuna-Keys + Postgres + GitHub-Token)
4. Deploy

Die App ist dann **Cloud-bewusst:** Sie erkennt automatisch ob sie auf Streamlit Cloud läuft und triggert dort GitHub Actions statt lokaler Subprocess-Aufrufe.

---

## 🔁 Automatische Daten-Updates

Der GitHub Actions Workflow (`.github/workflows/update-data.yml`) läuft:

- **Täglich** um 3 Uhr UTC (4 Uhr deutsche Zeit) automatisch
- **On-demand** über den Aktualisieren-Button im Dashboard

Pipeline-Steps:
1. Collect Jobs (Multi-Source)
2. Clean & Feature-Engineering
3. Extract Skills
4. Load to PostgreSQL (mit Auto-Schema-Migration)

Die Streamlit-App pollt nach Trigger automatisch den Workflow-Status und lädt nach Abschluss die neuen Daten.

---

## 📓 Jupyter-Notebooks

Vier Notebooks dokumentieren den Workflow und die Erkenntnisse:

| # | Notebook | Was es zeigt |
|---|---|---|
| 01 | [`data_collection`](notebooks/01_data_collection.ipynb) | Multi-Source-API-Architektur, Quellen-Vergleich |
| 02 | [`cleaning`](notebooks/02_cleaning.ipynb) | pandas-ETL, Regex-basiertes Feature Engineering |
| 03 | [`skill_extraction`](notebooks/03_skill_extraction.ipynb) | Top-Skills, Co-Occurrence-Matrix, Skill × Rolle |
| 04 | [`analysis`](notebooks/04_analysis.ipynb) | Finale Markt-Insights für die Homeoffice-Suche |

```bash
jupyter notebook notebooks/
```

---

## 🛠️ Tech-Stack

**Backend:**
- Python 3.12
- pandas, numpy — ETL & Datenverarbeitung
- requests — API-Clients
- SQLAlchemy + psycopg2 — Postgres-Anbindung

**Frontend:**
- Streamlit ≥ 1.40 — Dashboard-Framework
- Plotly — interaktive Charts

**Datenhaltung:**
- CSV (lokal, default)
- PostgreSQL bei [Neon](https://neon.tech) (Cloud, optional)

**CI/CD:**
- GitHub Actions — täglicher Workflow + on-demand Trigger
- Streamlit Cloud — kostenloses App-Hosting

**APIs:**
- [Bundesagentur für Arbeit Jobsuche-API](https://jobsuche.api.bund.dev) — kostenlos, unbegrenzt
- [Adzuna API](https://developer.adzuna.com) — kostenlos, 250 Calls/Tag

---

## 📊 Beispiel-Insights

Aus der Analyse von **5.000+ deutschen Data-Stellen**:

- ~12 % aller Data-Stellen bieten explizit Homeoffice/Remote an
- **Data Scientist** und **Analytics Engineer** haben die höchsten Remote-Quoten
- **SQL + Python + Excel** sind in 80 %+ der Junior-Stellen gefordert
- Berufseinsteiger:innen sind im Homeoffice-Markt **nicht systematisch benachteiligt**
- Top-Städte für Remote-Stellen: Berlin, München, Hamburg

→ Vollständige Auswertung im [Analyse-Notebook](notebooks/04_analysis.ipynb)

---

## 📋 Datenbank-Schema (optional)

Wenn `USE_POSTGRES=true`:

```sql
jobs        (job_id, job_title, employer_name, job_city,
             role_group, source, ...)        -- Faktentabelle
skills      (skill_id, skill_name)           -- Lookup
job_skills  (job_id, skill_id)               -- m:n-Bridge
```

Schema wird beim Loader-Lauf automatisch migriert (z.B. fehlende Spalten ergänzt). Beispiel-Queries in [`sql/analysis_queries.sql`](sql/analysis_queries.sql) — mit Window Functions, CTEs und JOINs.

---

## ⚠️ Limitationen

- **Cross-Source-Duplikate:** Dieselbe Stelle auf LinkedIn (via Adzuna) und Arbeitsagentur haben unterschiedliche IDs.
- **Snapshot-Daten:** Manche Anzeigen sind beim Klick auf den Job-Link möglicherweise schon abgelaufen.
- **Heuristische Klassifikation:** Rollen-Erkennung basiert auf Schlüsselwörtern, kein ML.
- **Skill-Liste manuell gepflegt:** Neue Tools (z.B. Polars, DuckDB) müssen ergänzt werden.

---

## 👤 Autor

**Michael Winkels** ([@l1ghty34r](https://github.com/l1ghty34r)) 
