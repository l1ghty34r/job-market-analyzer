"""
Tab — Jobsuche: Filter-basierte Stellensuche.

Kein Score-System mehr — der Nutzer filtert selbst nach Bedarf.
Sortierung: Neueste Jobs zuerst.
"""

import ast
import html as html_lib
import math

import pandas as pd
import streamlit as st

from src.remote_filter import filter_remote_jobs, is_remote_friendly_text


# ─────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────
def _parse_skills(value) -> list[str]:
    if pd.isna(value) or value == "" or value == "[]":
        return []
    if isinstance(value, list):
        return value
    try:
        parsed = ast.literal_eval(str(value))
        return parsed if isinstance(parsed, list) else []
    except (ValueError, SyntaxError):
        return []


def _esc(value) -> str:
    return html_lib.escape(str(value or "—"))


def _format_date(value) -> str:
    if value is None or pd.isna(value):
        return ""
    try:
        dt = pd.to_datetime(value, errors="coerce", utc=True)
        if pd.isna(dt):
            return ""
        now = pd.Timestamp.now(tz="UTC")
        days = (now - dt).days
        if days == 0:
            return "heute"
        if days == 1:
            return "gestern"
        if days < 7:
            return f"vor {days} Tagen"
        if days < 30:
            return f"vor {days // 7} Wo."
        return dt.strftime("%d.%m.%Y")
    except Exception:
        return ""


# ─────────────────────────────────────────────────────────────────────
# Job-Card (ohne Score)
# ─────────────────────────────────────────────────────────────────────
def _job_card_html(job: pd.Series) -> str:
    """Rendert einen Job als HTML-Card."""
    title = _esc(job.get("job_title"))
    employer = _esc(job.get("employer_name"))
    city = _esc(job.get("job_city"))
    role = _esc(job.get("role_group"))
    remote = _esc(job.get("remote_type"))
    is_junior = bool(job.get("is_junior", 0))

    # Live-Erkennung von Remote: drei Quellen kombiniert
    is_remote = (
        bool(job.get("is_remote_friendly", False))
        or job.get("remote_type") in ("Remote", "Hybrid", "Remote/Hybrid erwähnt")
        or is_remote_friendly_text(job.get("job_title"), job.get("job_description"))
    )

    apply_link = (job.get("job_apply_link") or "").strip()
    posted = _format_date(job.get("job_posted_at_datetime_utc") or job.get("job_posted_at"))

    # Linker Akzent-Balken: grün wenn Remote-fähig, sonst grau
    accent_color = "#10b981" if is_remote else "#6366f1"

    # Skills als Chips
    skills_list = _parse_skills(job.get("skills_found"))[:8]
    skills_html = "".join(
        f'<span style="display:inline-block;background:rgba(99,102,241,0.15);'
        f'color:#c7d2fe;padding:3px 10px;border-radius:8px;'
        f'font-size:0.8em;margin:2px 4px 2px 0;">'
        f'{_esc(s)}</span>'
        for s in skills_list
    )

    # Badges: Remote, Junior
    badges = []
    if is_remote:
        badges.append(
            '<span style="display:inline-block;background:rgba(16,185,129,0.15);'
            'color:#6ee7b7;padding:3px 10px;border-radius:8px;font-size:0.78em;'
            'font-weight:600;margin-right:6px;border:1px solid rgba(16,185,129,0.3);">'
            '🏠 Remote/Homeoffice</span>'
        )
    if is_junior:
        badges.append(
            '<span style="display:inline-block;background:rgba(245,158,11,0.15);'
            'color:#fbbf24;padding:3px 10px;border-radius:8px;font-size:0.78em;'
            'font-weight:600;margin-right:6px;border:1px solid rgba(245,158,11,0.3);">'
            '🎓 Junior</span>'
        )
    badges_html = "".join(badges)

    if apply_link:
        apply_button = (
            f'<a href="{html_lib.escape(apply_link)}" target="_blank" rel="noopener" '
            f'style="display:inline-block;background:{accent_color};color:white !important;'
            f'padding:10px 22px;border-radius:8px;text-decoration:none !important;'
            f'font-weight:600;font-size:0.9em;white-space:nowrap;">Zur Anzeige →</a>'
        )
    else:
        apply_button = (
            '<span style="color:#9ca3af;font-style:italic;font-size:0.85em;">'
            'Kein Link verfügbar</span>'
        )

    return (
        f'<div style="background:rgba(30,41,59,0.5);border:1px solid rgba(129,140,248,0.15);'
        f'border-left:4px solid {accent_color};border-radius:12px;'
        f'padding:18px 22px;margin-bottom:14px;'
        f'transition:all 0.18s ease;">'
        f'<div style="display:flex;justify-content:space-between;'
        f'align-items:flex-start;gap:16px;flex-wrap:wrap;">'
        f'<div style="flex:1;min-width:280px;">'
        + (f'<div style="margin-bottom:8px;">{badges_html}</div>' if badges_html else '')
        + f'<h3 style="margin:6px 0 6px 0;font-size:1.1em;color:#e2e8f0;'
        f'line-height:1.3;font-weight:600;">{title}</h3>'
        f'<div style="color:#94a3b8;font-size:0.92em;margin-bottom:10px;">'
        f'🏢 <strong style="color:#cbd5e1;">{employer}</strong> &nbsp;·&nbsp; 📍 {city} '
        f'&nbsp;·&nbsp; 🌍 {remote} &nbsp;·&nbsp; 💼 {role}'
        + (f' &nbsp;·&nbsp; 🕒 {posted}' if posted else '')
        + f'</div>'
        f'<div>{skills_html}</div>'
        f'</div>'
        f'<div style="flex-shrink:0;align-self:center;">{apply_button}</div>'
        f'</div>'
        f'</div>'
    )


# ─────────────────────────────────────────────────────────────────────
# Hauptfunktion: render
# ─────────────────────────────────────────────────────────────────────
def render(jobs_with_skills: pd.DataFrame):
    """Rendert den Jobsuche-Tab."""

    if jobs_with_skills.empty:
        st.warning("Keine Jobs im Datensatz – bitte zuerst die Pipeline laufen lassen.")
        return

    df = jobs_with_skills.copy()

    if df.empty:
        st.warning("Keine Jobs im Datensatz.")
        return

    # Falls is_remote_friendly noch nicht in Daten (alte Pipeline) → on-the-fly berechnen
    if "is_remote_friendly" not in df.columns:
        # Fallback: aus remote_type ableiten
        df["is_remote_friendly"] = df["remote_type"].isin(
            ["Remote", "Hybrid", "Remote/Hybrid erwähnt"]
        )

    # ─────────────────────────────────────────────────────────────────
    # FILTER-LEISTE
    # ─────────────────────────────────────────────────────────────────
    st.markdown("##### 🔍 Filter")

    # Reihe 1: Hauptfilter
    f1, f2, f3 = st.columns([2, 2, 1])

    with f1:
        roles = sorted(df["role_group"].dropna().unique().tolist())
        selected_roles = st.multiselect(
            "Rolle",
            options=roles,
            default=[],
            placeholder="Alle Rollen",
            key="js_roles",
            help="Leer = alle Rollen werden angezeigt.",
        )

    with f2:
        cities = sorted(
            df[df["job_city"] != "Unbekannt"]["job_city"].dropna().unique().tolist()
        )
        selected_cities = st.multiselect(
            "Stadt",
            options=cities,
            default=[],
            placeholder="Alle Städte",
            key="js_cities",
        )

    with f3:
        remote_only = st.toggle(
            "🏠 Remote / Homeoffice",
            value=False,
            help="Zeigt nur Stellen mit Remote-, Homeoffice- oder mobilem Arbeiten.",
            key="js_remote_only",
        )

    # Reihe 2: weitere Filter
    f4, f5 = st.columns([3, 1])
    with f4:
        search_query = st.text_input(
            "🔎 Stichwort (Titel, Arbeitgeber, Beschreibung)",
            placeholder="z.B. Versicherung, SAP, Python ...",
            key="js_search",
            label_visibility="collapsed",
        )
    with f5:
        only_with_link = st.toggle(
            "🔗 Nur mit Link",
            value=False,
            help="Filtert Stellen ohne Bewerbungslink aus.",
            key="js_only_link",
        )

    # Erweiterte Filter
    with st.expander("⚙️ Erweiterte Filter", expanded=False):
        ef1, ef2 = st.columns(2)

        with ef1:
            junior_filter = st.radio(
                "Erfahrungslevel",
                options=["Alle", "Nur Junior", "Ohne Junior"],
                index=0,
                horizontal=True,
                key="js_junior",
            )

            if "source" in df.columns:
                sources = sorted(df["source"].dropna().unique().tolist())
                selected_sources = st.multiselect(
                    "📡 Datenquellen",
                    options=sources,
                    default=sources,
                    key="js_sources",
                )
            else:
                selected_sources = None

        with ef2:
            all_skills = set()
            for v in df["skills_found"].dropna():
                all_skills.update(_parse_skills(v))
            required_skills = st.multiselect(
                "🛠️ Muss-Skills (alle erforderlich)",
                options=sorted(all_skills),
                default=[],
                key="js_required_skills",
            )

    # ─────────────────────────────────────────────────────────────────
    # FILTER ANWENDEN
    # ─────────────────────────────────────────────────────────────────
    if selected_roles:
        df = df[df["role_group"].isin(selected_roles)]
    if selected_cities:
        df = df[df["job_city"].isin(selected_cities)]
    if remote_only:
        df = filter_remote_jobs(df)

    if junior_filter == "Nur Junior":
        df = df[df["is_junior"] == 1]
    elif junior_filter == "Ohne Junior":
        df = df[df["is_junior"] == 0]

    if search_query:
        q = search_query.lower()
        mask = (
            df["job_title"].fillna("").str.lower().str.contains(q, na=False)
            | df["job_description"].fillna("").str.lower().str.contains(q, na=False)
            | df["employer_name"].fillna("").str.lower().str.contains(q, na=False)
        )
        df = df[mask]

    if required_skills:
        def has_all(s):
            skills = _parse_skills(s)
            return all(req in skills for req in required_skills)
        df = df[df["skills_found"].apply(has_all)]

    if selected_sources is not None and "source" in df.columns:
        df = df[df["source"].isin(selected_sources)]

    if only_with_link and "job_apply_link" in df.columns:
        df = df[df["job_apply_link"].notna() & (df["job_apply_link"] != "")]

    # ─────────────────────────────────────────────────────────────────
    # SORTIERUNG: NEUESTE ZUERST
    # ─────────────────────────────────────────────────────────────────
    if "job_posted_at_datetime_utc" in df.columns:
        df["_sort_date"] = pd.to_datetime(
            df["job_posted_at_datetime_utc"], errors="coerce", utc=True
        )
        df = df.sort_values("_sort_date", ascending=False, na_position="last")
        df = df.drop(columns=["_sort_date"]).reset_index(drop=True)

    st.markdown("")
    st.markdown(f"##### **{len(df)}** Stellen passen zu deinen Kriterien")

    if df.empty:
        st.info("Keine Treffer. Versuche, Filter zu lockern.")
        return

    # ─────────────────────────────────────────────────────────────────
    # PAGINATION + CARDS
    # ─────────────────────────────────────────────────────────────────
    PAGE_SIZE = 10
    total_pages = max(1, math.ceil(len(df) / PAGE_SIZE))

    if "jobsuche_page" not in st.session_state:
        st.session_state.jobsuche_page = 1
    if st.session_state.jobsuche_page > total_pages:
        st.session_state.jobsuche_page = 1

    page = st.session_state.jobsuche_page
    start = (page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    visible_jobs = df.iloc[start:end]

    cards_html = "".join(_job_card_html(row) for _, row in visible_jobs.iterrows())
    if hasattr(st, "html"):
        st.html(f"<div>{cards_html}</div>")
    else:
        st.markdown(cards_html, unsafe_allow_html=True)

    if total_pages > 1:
        st.markdown("")
        nav_l, nav_c, nav_r = st.columns([1, 2, 1])
        with nav_l:
            if st.button("← Zurück", disabled=page == 1, use_container_width=True,
                          key="page_back"):
                st.session_state.jobsuche_page = max(1, page - 1)
                st.rerun()
        with nav_c:
            st.markdown(
                f"<div style='text-align:center;padding-top:8px;color:#6b7280;'>"
                f"Seite <strong>{page}</strong> von {total_pages} "
                f"&nbsp;·&nbsp; Stellen {start + 1}–{min(end, len(df))} von {len(df)}"
                f"</div>",
                unsafe_allow_html=True,
            )
        with nav_r:
            if st.button("Weiter →", disabled=page >= total_pages,
                          use_container_width=True, key="page_fwd"):
                st.session_state.jobsuche_page = min(total_pages, page + 1)
                st.rerun()
