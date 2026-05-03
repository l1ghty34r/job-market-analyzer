"""
Data Job Market Analyzer Germany — Single-Page Dashboard.

Aktualisieren-Button:
  - Lokal: ruft die Pipeline direkt via subprocess auf
  - Cloud: triggert GitHub Actions Workflow via API

Erkennung Cloud vs. Lokal: env-Variable `STREAMLIT_RUNTIME` oder
das Vorhandensein von `GITHUB_TOKEN` in den secrets.
"""

import os
import subprocess
import sys
import time
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
    h1 { font-weight: 700 !important; letter-spacing: -0.02em; }
    h2, h3, h4, h5 { font-weight: 600 !important; letter-spacing: -0.01em; }

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
    }
    div[role="radiogroup"] > label > div:first-child { display: none; }

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

    /* ─── Metric-Cards ───────────────────────────────────────────── */
    [data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(129, 140, 248, 0.15);
        border-radius: 12px;
        padding: 16px 20px;
    }

    /* ─── Info-Boxen ─────────────────────────────────────────────── */
    div[data-testid="stAlert"] {
        border-radius: 10px;
        border: 1px solid rgba(129, 140, 248, 0.2);
        background: rgba(30, 41, 59, 0.5);
    }

    /* ─── Expander ───────────────────────────────────────────────── */
    [data-testid="stExpander"] {
        border-radius: 10px;
        border-color: rgba(129, 140, 248, 0.15) !important;
    }

    /* ─── Trennlinien ────────────────────────────────────────────── */
    hr {
        border-color: rgba(129, 140, 248, 0.15) !important;
        margin: 1.5rem 0 !important;
    }

    /* ─── Scrollbar ──────────────────────────────────────────────── */
    ::-webkit-scrollbar { width: 10px; height: 10px; }
    ::-webkit-scrollbar-track { background: rgba(30, 41, 59, 0.3); }
    ::-webkit-scrollbar-thumb {
        background: rgba(129, 140, 248, 0.3);
        border-radius: 5px;
    }
    ::-webkit-scrollbar-thumb:hover { background: rgba(129, 140, 248, 0.5); }
    </style>
    """,
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────────────
# Cloud vs. Lokal erkennen
# ─────────────────────────────────────────────────────────────────────
def _read_secret(key: str, default: str = "") -> str:
    """Liest aus st.secrets ODER os.environ."""
    try:
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return os.getenv(key, default)


# Cloud-Modus = wenn GITHUB_TOKEN gesetzt ist (für Workflow-Trigger)
GITHUB_TOKEN = _read_secret("GITHUB_TOKEN", "")
GITHUB_REPO = _read_secret("GITHUB_REPO", "")  # z.B. "user/job-market-analyzer"
IS_CLOUD = bool(GITHUB_TOKEN and GITHUB_REPO)


# ─────────────────────────────────────────────────────────────────────
# Helpers: Lokale Pipeline (subprocess)
# ─────────────────────────────────────────────────────────────────────
def run_pipeline_step_local(name: str, cmd: list[str], log_placeholder) -> bool:
    """Führt einen Pipeline-Schritt lokal via subprocess aus."""
    log_placeholder.markdown(f"▶ **{name}** läuft …")
    try:
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        result = subprocess.run(
            cmd, cwd=str(ROOT), capture_output=True, text=True,
            encoding="utf-8", errors="replace", env=env, timeout=600,
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
        log_placeholder.error(f"⏱️ {name} dauert zu lange (>10 min) – Abbruch.")
        return False
    except Exception as e:
        log_placeholder.error(f"❌ {name} crashed: {e}")
        return False


def run_pipeline_local(skip_collect: bool, to_postgres: bool, truncate: bool) -> None:
    """Lokale Pipeline mit Live-Status im UI."""
    python = sys.executable

    with st.status("🔄 Pipeline läuft…", expanded=True) as status:
        steps_ok = True

        if not skip_collect:
            step1 = st.empty()
            ok = run_pipeline_step_local(
                "1/4  Daten von APIs holen",
                [python, "-m", "src.collect_jobs"], step1,
            )
            steps_ok = steps_ok and ok
        else:
            st.markdown("⏭️  Schritt 1 (Collect) übersprungen")

        if steps_ok:
            step2 = st.empty()
            ok = run_pipeline_step_local(
                "2/4  Daten bereinigen",
                [python, "-m", "src.clean_jobs"], step2,
            )
            steps_ok = steps_ok and ok

        if steps_ok:
            step3 = st.empty()
            ok = run_pipeline_step_local(
                "3/4  Skills extrahieren",
                [python, "-m", "src.extract_skills"], step3,
            )
            steps_ok = steps_ok and ok

        if steps_ok and to_postgres:
            cmd = [python, "-m", "src.load_to_postgres"]
            if truncate:
                cmd.append("--truncate")
            step4 = st.empty()
            ok = run_pipeline_step_local("4/4  PostgreSQL aktualisieren", cmd, step4)
            steps_ok = steps_ok and ok
        elif not to_postgres:
            st.markdown("⏭️  Schritt 4 (PostgreSQL) übersprungen")

        if steps_ok:
            status.update(label="✅ Pipeline abgeschlossen", state="complete")
        else:
            status.update(label="❌ Pipeline fehlgeschlagen", state="error")

    if steps_ok:
        st.cache_data.clear()
        if st.button("🔄 Seite neu laden"):
            st.rerun()


# ─────────────────────────────────────────────────────────────────────
# Helpers: Cloud-Pipeline (GitHub Actions)
# ─────────────────────────────────────────────────────────────────────
def trigger_github_workflow(skip_collect: bool) -> tuple[bool, str]:
    """Triggert den GitHub Actions Workflow via API.

    Returns:
        (success, message)
    """
    import requests

    url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/update-data.yml/dispatches"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    payload = {
        "ref": "main",
        "inputs": {
            "skip_collect": str(skip_collect).lower(),
        },
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        if response.status_code == 204:
            return True, "Workflow gestartet"
        return False, f"GitHub API antwortete mit {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return False, f"Verbindungsfehler: {e}"


def get_latest_workflow_run() -> dict | None:
    """Holt den neuesten Workflow-Run-Status. None falls Fehler."""
    import requests

    url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/update-data.yml/runs"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    try:
        response = requests.get(url, headers=headers, params={"per_page": 1}, timeout=10)
        if response.status_code == 200:
            runs = response.json().get("workflow_runs", [])
            return runs[0] if runs else None
    except Exception:
        pass
    return None


def run_pipeline_cloud(skip_collect: bool) -> None:
    """Triggert GitHub Actions, zeigt Live-Status und aktualisiert automatisch."""
    with st.status("🔄 Pipeline läuft auf GitHub Actions…", expanded=True) as status:
        st.markdown("**1/3  Workflow triggern**")

        # Wichtig: Vorher den letzten Run-Timestamp merken, um den NEUEN
        # Run vom alten zu unterscheiden
        prev_run = get_latest_workflow_run()
        prev_run_id = prev_run.get("id") if prev_run else None

        success, msg = trigger_github_workflow(skip_collect)
        if not success:
            status.update(label="❌ Workflow konnte nicht gestartet werden",
                          state="error")
            st.error(f"Fehler: {msg}")
            return

        st.success(f"✅ {msg}")
        st.markdown("**2/3  Auf Workflow-Start warten** (~5 Sek.)")
        time.sleep(6)

        # Neuen Run holen — der hat eine andere ID als der alte
        new_run = None
        for _ in range(6):
            latest = get_latest_workflow_run()
            if latest and latest.get("id") != prev_run_id:
                new_run = latest
                break
            time.sleep(2)

        if not new_run:
            st.warning("Workflow gestartet, aber Status-Tracking nicht verfügbar.")
            status.update(label="⚠️ Workflow gestartet (Status unbekannt)",
                          state="complete")
            return

        run_url = new_run.get("html_url", "")
        st.markdown(
            f"**3/3  Workflow läuft** &nbsp; "
            f"[**→ Auf GitHub verfolgen**]({run_url})"
        )

        # Polling: alle 10 Sek. den Status prüfen, max 12 Min
        progress = st.empty()
        elapsed_info = st.empty()

        max_wait = 12 * 60  # 12 Minuten
        check_interval = 10
        elapsed = 0

        while elapsed < max_wait:
            current = _get_workflow_run_by_id(new_run["id"])
            if not current:
                break

            run_status = current.get("status")
            conclusion = current.get("conclusion")

            elapsed_min = elapsed // 60
            elapsed_sec = elapsed % 60
            elapsed_info.caption(
                f"⏱️ Läuft seit {elapsed_min}:{elapsed_sec:02d} Min …"
            )

            if run_status == "completed":
                if conclusion == "success":
                    progress.success("✅ Pipeline erfolgreich abgeschlossen!")
                    status.update(label="✅ Daten aktualisiert!",
                                  state="complete")
                    st.cache_data.clear()
                    st.balloons()
                    time.sleep(2)
                    st.rerun()
                else:
                    progress.error(
                        f"❌ Pipeline fehlgeschlagen ({conclusion}). "
                        f"[Logs anschauen →]({run_url})"
                    )
                    status.update(label="❌ Pipeline fehlgeschlagen",
                                  state="error")
                return

            progress.info(f"⏳ {run_status or 'wartet auf Runner'} …")
            time.sleep(check_interval)
            elapsed += check_interval

        # Timeout
        progress.warning(
            f"⏱️ Pipeline läuft länger als erwartet. "
            f"[Status auf GitHub prüfen →]({run_url})\n\n"
            "Du kannst den Browser-Tab schließen — sobald der Workflow durch ist, "
            "klick einfach auf 'Nur Cache leeren'."
        )
        status.update(label="⏱️ Polling gestoppt — Workflow läuft im Hintergrund",
                      state="complete")


def _get_workflow_run_by_id(run_id: int) -> dict | None:
    """Holt einen spezifischen Run-Status (für Polling)."""
    import requests
    url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/runs/{run_id}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None


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

        if IS_CLOUD:
            st.caption(
                "🌐 **Cloud-Modus:** Triggert GitHub Actions Workflow. "
                "Pipeline läuft 5–10 Min. im Hintergrund."
            )

            skip_collect = st.checkbox(
                "Ohne API-Sammlung (nur cleaning)",
                value=False,
                help="Nur cleaning + skill-extract + postgres-load (~1 min)",
                key="cloud_skip_collect",
            )

            if st.button("🚀 Workflow starten", type="primary",
                          use_container_width=True, key="trigger_cloud_btn"):
                run_pipeline_cloud(skip_collect)

            st.divider()

            # Status des letzten Runs anzeigen
            latest = get_latest_workflow_run()
            if latest:
                conclusion = latest.get("conclusion") or "läuft…"
                status_emoji = {
                    "success": "✅", "failure": "❌",
                    "cancelled": "⛔", "läuft…": "⏳",
                }.get(conclusion, "❓")
                st.caption(
                    f"Letzter Run: {status_emoji} {conclusion} "
                    f"([Details]({latest.get('html_url', '')}))"
                )

            st.divider()
            if st.button("Nur Cache leeren", use_container_width=True,
                          key="cloud_cache_clear",
                          help="Lädt Daten aus Postgres neu, ohne Pipeline."):
                st.cache_data.clear()
                st.rerun()

        else:
            # Lokaler Modus: subprocess
            st.caption("💻 **Lokal-Modus:** Pipeline läuft auf diesem Rechner.")

            skip_collect = st.checkbox(
                "Ohne API-Sammlung (nur cleaning)",
                value=False, key="local_skip_collect",
            )
            use_postgres_now = _read_secret("USE_POSTGRES", "").lower() == "true"
            to_postgres = st.checkbox(
                "PostgreSQL aktualisieren",
                value=use_postgres_now, key="local_to_postgres",
            )
            truncate = st.checkbox(
                "Tabellen vorher leeren", value=True,
                key="local_truncate", disabled=not to_postgres,
            )

            if st.button("Jetzt starten", type="primary",
                          use_container_width=True, key="local_run_btn"):
                run_pipeline_local(skip_collect, to_postgres, truncate)

            st.divider()
            if st.button("Nur Cache leeren", use_container_width=True,
                          key="local_cache_clear"):
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
backend = "PostgreSQL" if _read_secret("USE_POSTGRES", "").lower() == "true" else "CSV"

# Letzte Aktualisierung: bei Cloud aus letztem Workflow-Run, sonst Datei-mtime
last_update = "?"
if IS_CLOUD:
    latest_run = get_latest_workflow_run()
    if latest_run and latest_run.get("conclusion") == "success":
        try:
            ts = datetime.fromisoformat(
                latest_run["updated_at"].replace("Z", "+00:00")
            )
            last_update = ts.strftime("%d.%m.%Y %H:%M")
        except Exception:
            pass
else:
    csv_path = ROOT / "data" / "processed" / "jobs_cleaned.csv"
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
# Tab-Navigation
# ─────────────────────────────────────────────────────────────────────
TAB_LABELS = ["📊  Marktanalyse", "🔎  Jobsuche", "📚  Methodik"]

selected_tab = st.radio(
    "Navigation", options=TAB_LABELS, horizontal=True,
    label_visibility="collapsed", key="active_tab",
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
