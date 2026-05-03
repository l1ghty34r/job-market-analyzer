# 🚀 Deployment auf Streamlit Cloud

Diese Anleitung führt dich durch das Deployment des Dashboards auf [Streamlit Cloud](https://streamlit.io/cloud) — kostenlos und in ~10 Minuten erledigt.

---

## ✅ Vorbereitungen (lokal)

### 1. Code auf GitHub pushen

```bash
# Falls noch nicht passiert:
cd C:\dev\job-market-analyzer
git init
git add .
git commit -m "Initial commit: Data Job Market Analyzer"

# Repo auf GitHub erstellen, dann:
git remote add origin https://github.com/<USER>/job-market-analyzer.git
git branch -M main
git push -u origin main
```

> ⚠️ **Wichtig:** Vorher checken, dass `.env` und `data/processed/*.csv` **NICHT** im Repo sind. Die `.gitignore` sollte das verhindern.

### 2. Daten in Postgres laden (einmalig)

Streamlit Cloud hat **kein persistentes Filesystem** — nach jedem Neustart sind alle CSVs weg. Deshalb **Postgres als Datenquelle** nutzen.

```bash
# Lokal: Daten in Neon laden
python -m src.load_to_postgres --truncate
```

Damit liegen die 5.000+ Jobs in deiner Neon-DB. Die Cloud-App liest von dort.

---

## ☁️ Deployment auf Streamlit Cloud

### 1. Account anlegen

1. Auf [streamlit.io/cloud](https://streamlit.io/cloud) anmelden
2. Mit deinem GitHub-Account verbinden
3. "New app" klicken

### 2. App-Konfiguration

Auf dem "Deploy an app"-Screen:

| Feld | Wert |
|---|---|
| **Repository** | `<USER>/job-market-analyzer` |
| **Branch** | `main` |
| **Main file path** | `app/main.py` |
| **App URL** | `jobmarket-de` (frei wählbar, ergibt `jobmarket-de.streamlit.app`) |

### 3. Secrets eintragen

Vor dem ersten Deploy: **Advanced settings** öffnen → **Secrets** Tab.

Den Inhalt der lokalen `.env` ins Secrets-Feld kopieren, im **TOML-Format**:

```toml
ADZUNA_APP_ID = "deine_echte_app_id"
ADZUNA_APP_KEY = "dein_echter_app_key"

USE_POSTGRES = "true"
POSTGRES_HOST = "ep-xxx-xxx.eu-central-1.aws.neon.tech"
POSTGRES_PORT = "5432"
POSTGRES_DB = "jobmarket"
POSTGRES_USER = "..."
POSTGRES_PASSWORD = "..."
```

> 📋 **Vorlage** liegt unter [`.streamlit/secrets.toml.example`](.streamlit/secrets.toml.example)

### 4. Deploy klicken

1. **Deploy** klicken
2. ~2 Minuten warten (Streamlit installiert die `requirements.txt`)
3. App ist live unter `https://jobmarket-de.streamlit.app` ✨

---

## 🐛 Häufige Probleme

### "ModuleNotFoundError"

Streamlit installiert nur die Pakete aus `requirements.txt`. Falls etwas fehlt:

```bash
pip freeze > requirements.txt
git add requirements.txt && git commit -m "Update deps"
git push
```

→ Streamlit deployt automatisch neu.

### "Postgres connection refused"

- Prüfe, ob Neon den Schlafmodus aktiviert hat (Free-Tier pausiert nach 5 min Inaktivität)
- Schau in die Streamlit-Logs (Manage → Logs)
- Stelle sicher, dass `POSTGRES_HOST` korrekt im `secrets.toml` steht

### "Aktualisieren-Button funktioniert nicht"

Auf Streamlit Cloud läuft die Pipeline **nicht** automatisch — der Server hat keine API-Calls eingerichtet. Datenupdates müssen lokal passieren:

```bash
# Lokal:
python -m src.collect_jobs
python -m src.clean_jobs
python -m src.extract_skills
python -m src.load_to_postgres --truncate
```

→ Die Cloud-App liest dann automatisch die neuen Daten aus Postgres.

### "App ist langsam"

Streamlit Cloud Free-Tier hat begrenzten RAM. Bei 5.000+ Jobs:
- Sicherstellen, dass `@st.cache_data` aktiv ist (steht in `utils.py`)
- Datenmenge ggf. begrenzen (z.B. nur letzte 90 Tage)

---

## 🔄 Updates deployen

Jeder `git push` zum Main-Branch triggert ein **automatisches Re-Deployment**. Du musst nichts manuell tun.

```bash
# Code ändern...
git add .
git commit -m "Improve feature X"
git push
# → App wird in 1-2 Min neu deployed
```

---

## 📊 Optional: Tägliche Daten-Updates

Wenn du **automatische Daten-Updates** willst (täglich neue Jobs sammeln), brauchst du einen externen Cron-Trigger, weil Streamlit Cloud das nicht selbst kann:

**Option A — GitHub Actions** (kostenlos, empfohlen):

`.github/workflows/daily-update.yml`:
```yaml
name: Daily Data Update
on:
  schedule:
    - cron: "0 3 * * *"  # 3 Uhr nachts UTC
  workflow_dispatch:

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - run: |
          python -m src.collect_jobs
          python -m src.clean_jobs
          python -m src.extract_skills
          python -m src.load_to_postgres --truncate
        env:
          ADZUNA_APP_ID: ${{ secrets.ADZUNA_APP_ID }}
          ADZUNA_APP_KEY: ${{ secrets.ADZUNA_APP_KEY }}
          USE_POSTGRES: "true"
          POSTGRES_HOST: ${{ secrets.POSTGRES_HOST }}
          POSTGRES_USER: ${{ secrets.POSTGRES_USER }}
          POSTGRES_PASSWORD: ${{ secrets.POSTGRES_PASSWORD }}
          POSTGRES_DB: ${{ secrets.POSTGRES_DB }}
```

→ GitHub Settings → Secrets → Action Secrets eintragen.
→ Läuft täglich um 3 Uhr, Daten landen in Neon, Streamlit-App zeigt automatisch neue Daten.

---

## ✅ Fertig!

Deine App sollte jetzt live sein. Trag den Link in die `README.md` ein:

```markdown
> 🔗 **[jobmarket-de.streamlit.app](https://jobmarket-de.streamlit.app)**
```

Damit hast du einen **Live-Demo-Link** für deinen CV — Recruiter können das Dashboard direkt anklicken statt nur Screenshots zu sehen.
