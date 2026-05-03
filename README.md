# 📊 Data Job Market Germany

> Multi-Source ETL-Pipeline und interaktives Dashboard zur Analyse des deutschen Data-Jobmarkts — mit Fokus auf Homeoffice-Stellen.

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-336791?logo=postgresql&logoColor=white)](https://neon.tech)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 🎯 Worum geht's?

Wer einen Data-Job in Deutschland sucht, steht vor einem Datenproblem: Stellenangebote sind über LinkedIn, Indeed, StepStone, Arbeitsagentur und unzählige andere Plattformen verteilt. Eine **systematische Marktübersicht** existiert nicht.

Dieses Projekt löst das mit einer kompletten Datenpipeline:

- **Sammelt** Stellenangebote aus zwei kostenlosen APIs (Bundesagentur für Arbeit + Adzuna)
- **Bereinigt** und reichert sie an (Stadt-Extraktion, Skill-Detection, Junior/Remote-Klassifikation)
- **Speichert** in PostgreSQL (Neon Cloud) — optional, lokales CSV reicht auch
- **Visualisiert** in einem Streamlit-Dashboard mit Filter, Suche und Markt-Insights

**Zielgruppe:** Berufseinsteiger:innen und erfahrene Data-Profis, die einen **Homeoffice-Job in Deutschland** suchen — und wissen wollen, wo die besten Chancen liegen.

---

## 🌐 Live-Demo

> 🔗 **[jobmarket-de.streamlit.app](https://jobmarket-de.streamlit.app)** _(Link nach Deployment hier eintragen)_

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
| 🗄️ **Optional Postgres** | Cloud-DB-Backend mit normalisiertem Schema (Neon) |
| 📓 **Jupyter-Notebooks** | 4 dokumentierte Notebooks zum Pipeline-Workflow und Markt-Insights |

---

## 🏗️ Architektur

```
┌──────────────────────┐    ┌──────────────────────┐    ┌──────────────────────┐
│  Multi-Source-APIs   │ →  │   ETL & Cleaning     │ →  │  PostgreSQL (Neon)   │
│                      │    │                      │    │                      │
│  • Arbeitsagentur    │    │  • Dedup über job_id │    │  • jobs              │
│  • Adzuna            │    │  • Stadt-Extraktion  │    │  • skills            │
│                      │    │  • Skill-Extraktion  │    │  • job_skills        │
│   → UnifiedJob       │    │  • Rollen-Cluster    │    │                      │
│                      │    │  • Remote-Detection  │    │   → Streamlit-App    │
└──────────────────────┘    └──────────────────────┘    └──────────────────────┘
```

### Projektstruktur

```
job-market-analyzer/
├── app/                    # Streamlit-Dashboard
│   ├── main.py             # Entry-Point
│   ├── tabs/               # 3 Tabs: Marktanalyse, Jobsuche, Methodik
│   └── components/         # Wiederverwendbare Plotly-Charts
├── src/                    # Pipeline-Code
│   ├── sources/            # API-Clients (abstract base + concrete)
│   ├── collect_jobs.py     # Multi-Source Collector
│   ├── clean_jobs.py       # ETL + Feature Engineering
│   ├── extract_skills.py   # Skill-Detection mit Regex
│   ├── load_to_postgres.py # ETL nach Neon
│   ├── geo.py              # Stadt → Region Lookup
│   └── remote_filter.py    # Live Remote-Erkennung
├── sql/                    # Schema + Analysis-Queries
├── notebooks/              # 4 Jupyter-Notebooks
└── data/                   # CSVs (raw + processed)
```

---

## 🚀 Quick Start

### 1. Setup

```bash
# Repository klonen
git clone https://github.com/<DEIN-USERNAME>/job-market-analyzer.git
cd job-market-analyzer

# Virtuelles Environment
python -m venv .venv
source .venv/bin/activate          # Linux/Mac
# .venv\Scripts\activate            # Windows

# Dependencies
pip install -r requirements.txt
```

### 2. Konfiguration

```bash
# .env-Datei aus Template anlegen
cp .env.example .env
```

Die Datei `.env` ausfüllen:

```env
# Adzuna (kostenlos auf https://developer.adzuna.com)
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
# Daten sammeln (5–10 min, holt 5.000+ Jobs)
python -m src.collect_jobs

# Bereinigen
python -m src.clean_jobs

# Skills extrahieren
python -m src.extract_skills

# Optional: in Postgres laden
python -m src.load_to_postgres --truncate
```

### 4. Dashboard starten

```bash
streamlit run app/main.py
```

→ Öffnet sich auf <http://localhost:8501>

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
jobs        (job_id, job_title, employer_name, job_city, role_group, ...)   -- Faktentabelle
skills      (skill_id, skill, category)                                     -- Lookup
job_skills  (job_id, skill_id)                                              -- m:n-Bridge
```

Beispiel-Queries in [`sql/analysis_queries.sql`](sql/analysis_queries.sql) — mit Window Functions, CTEs und JOINs.

---

## ⚠️ Limitationen

- **Cross-Source-Duplikate:** Dieselbe Stelle auf LinkedIn (via Adzuna) und Arbeitsagentur haben unterschiedliche IDs.
- **Snapshot-Daten:** Manche Anzeigen sind beim Klick auf den Job-Link möglicherweise schon abgelaufen.
- **Heuristische Klassifikation:** Rollen-Erkennung basiert auf Schlüsselwörtern, kein ML.
- **Skill-Liste manuell gepflegt:** Neue Tools (z.B. Polars, DuckDB) müssen ergänzt werden.

---

## 🗺️ Roadmap

- [ ] Streamlit Cloud Deployment
- [ ] GitHub Actions für tägliche Daten-Updates
- [ ] Salary-Prediction-Modell mit scikit-learn
- [ ] TF-IDF basierte automatische Skill-Discovery
- [ ] Cross-Source-Deduplizierung über (Title + Employer)-Hashing

---

## 📜 Lizenz

MIT — siehe [LICENSE](LICENSE)

## 👤 Autor

**Michael** — Portfolio-Projekt im Rahmen der Weiterbildung zum Data Analyst.

[GitHub](https://github.com/) · [LinkedIn](https://linkedin.com)
