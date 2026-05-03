# 📊 Data Job Market Germany

> End-to-End Datenpipeline und interaktives Dashboard zur Analyse des
> deutschen Data-Jobmarkts (Fokus: Remote/Hybrid).

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-336791?logo=postgresql&logoColor=white)](https://neon.tech)

------------------------------------------------------------------------

## 🎯 Overview

Dieses Projekt aggregiert und analysiert Data-Jobs aus Deutschland über
mehrere Quellen und stellt die Ergebnisse in einem interaktiven
Dashboard dar.

**Pipeline:** - Datensammlung über APIs (Bundesagentur für Arbeit +
Adzuna) - Cleaning & Feature Engineering (Skills, Rollen, Remote,
Junior) - Speicherung (CSV oder PostgreSQL) - Visualisierung in
Streamlit

🔗 **Live-Demo:** *Link hier einfügen*

------------------------------------------------------------------------

## ✨ Features

-   Multi-Source Job Aggregation (einheitliches Schema)
-   Regex-basierte Remote-Erkennung (DE/EN Keywords)
-   Skill-Extraktion mit Synonym-Mapping
-   Rollen-Klassifikation (Data Analyst, Scientist, BI, etc.)
-   Interaktives Dashboard (Filter, Suche, Marktanalyse)

------------------------------------------------------------------------

## 🏗️ Architektur

APIs → ETL → Storage (CSV / Postgres) → Streamlit Dashboard

------------------------------------------------------------------------

## 🚀 Quick Start

``` bash
git clone https://github.com/l1ghty34r/job-market-analyzer.git
cd job-market-analyzer

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

`.env` anlegen:

``` env
ADZUNA_APP_ID=xxx
ADZUNA_APP_KEY=xxx
USE_POSTGRES=false
```

Pipeline ausführen:

``` bash
python -m src.collect_jobs
python -m src.clean_jobs
python -m src.extract_skills
```

Dashboard starten:

``` bash
streamlit run app/main.py
```

------------------------------------------------------------------------

## 🛠️ Tech Stack

-   Python (pandas, numpy, requests)
-   Streamlit + Plotly
-   PostgreSQL (Neon, optional)
-   APIs: Bundesagentur für Arbeit, Adzuna

------------------------------------------------------------------------

## 📊 Example Insights

-   \~12 % der Data-Jobs bieten Remote/Hybrid
-   Höchste Remote-Quote bei Data Scientist & Analytics Engineer
-   Top Skills: SQL, Python, Excel
-   Remote konzentriert in großen Städten (Berlin, München, Hamburg)

------------------------------------------------------------------------

## ⚠️ Limitations

-   Duplikate zwischen Quellen möglich
-   Snapshot-Daten (Jobs können ablaufen)
-   Heuristische Klassifikation (kein ML)

------------------------------------------------------------------------

## 👤 Author

Michael Winkels