"""
Bundesagentur für Arbeit – offizielle Stellendatenbank Deutschlands.

API-Doku: https://jobsuche.api.bund.dev/
Authentifizierung: X-API-Key Header (öffentlicher Schlüssel "jobboerse-jobsuche")
Rate-Limit: ~1000 Requests/Stunde

Liefert die größte aktuelle Job-Datenbank Deutschlands. Komplett kostenlos.

Wichtige Parameter:
    was         – Freitext-Suche im Jobtitel
    wo          – Ort (mit umkreis kombinierbar)
    berufsfeld  – Berufsfeld-Filter (z.B. "Informatik, Information und Kommunikation")
                  Findet auch Jobs, deren Titel kein "Data" enthält!
    veroeffentlichtseit – nur Jobs der letzten N Tage (0-100)
"""

import time
from typing import Optional

import requests
import urllib3

from src.sources.base import JobSource, UnifiedJob

# Die API hat ein selbst-signiertes/abweichendes Zertifikat – wir deaktivieren
# die TLS-Validierung für diese Quelle. Das ist okay, weil wir nur Lesezugriff
# auf öffentliche Daten haben und keine Credentials senden.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ArbeitsagenturSource(JobSource):
    name = "arbeitsagentur"
    base_url = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/app/jobs"

    headers = {
        "User-Agent": "Jobsuche/2.9.2",
        "Host": "rest.arbeitsagentur.de",
        "X-API-Key": "jobboerse-jobsuche",
        "Connection": "keep-alive",
    }

    # Hard-Cap als Sicherheits-Limit (verhindert versehentliches Abgreifen
    # zehntausender Jobs). Bei normaler Data-Suche werden eh selten >5000.
    HARD_CAP = 10_000

    def fetch(
        self,
        search_term: str,
        max_results: Optional[int] = None,
        location: Optional[str] = None,
        umkreis: int = 50,
        berufsfeld: Optional[str] = None,
        veroeffentlichtseit: Optional[int] = None,
    ) -> list[UnifiedJob]:
        """
        Holt Jobs von der Arbeitsagentur-API.

        Args:
            search_term: Freitext-Suche im Jobtitel ("was")
            max_results: Maximum (None = ALLE verfügbaren, bis HARD_CAP)
            location: Ort ("wo"), z.B. "Köln" oder "Leverkusen"
            umkreis: Suchradius in km (default 50)
            berufsfeld: Berufsfeld-Filter, z.B. "Informatik, Information und Kommunikation"
            veroeffentlichtseit: Nur Jobs der letzten N Tage (0-100)

        Returns:
            Liste aller gefundenen UnifiedJob-Objekte.
        """
        # Effektives Limit: min(max_results, HARD_CAP) – bei None nur HARD_CAP
        effective_limit = min(max_results, self.HARD_CAP) if max_results else self.HARD_CAP

        results: list[UnifiedJob] = []
        page = 1
        size = 100  # Max pro API-Aufruf

        # Max-Treffer-Hinweis aus der ersten Antwort
        total_available: Optional[int] = None

        while len(results) < effective_limit:
            params = {
                "angebotsart": 1,           # 1 = Stellenangebot (kein Praktikum)
                "page": page,
                "pav": "false",             # keine privaten Arbeitsvermittler
                "size": size,
                "was": search_term,
            }
            if location:
                params["wo"] = location
                params["umkreis"] = umkreis
            if berufsfeld:
                params["berufsfeld"] = berufsfeld
            if veroeffentlichtseit is not None:
                params["veroeffentlichtseit"] = veroeffentlichtseit

            try:
                response = requests.get(
                    self.base_url,
                    headers=self.headers,
                    params=params,
                    verify=False,
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()
            except requests.exceptions.RequestException as e:
                print(f"  ❌ [{self.name}] Fehler auf Seite {page}: {e}")
                break

            stellenangebote = data.get("stellenangebote", []) or []

            # Total-Treffer beim ersten Call merken
            if total_available is None:
                total_available = data.get("maxErgebnisse") or len(stellenangebote)
                if total_available > effective_limit:
                    print(f"  ℹ️  [{self.name}] Insgesamt {total_available} Jobs verfügbar "
                          f"(hole bis zu {effective_limit})")
                else:
                    print(f"  ℹ️  [{self.name}] Insgesamt {total_available} Jobs verfügbar")

            print(f"  [{self.name}] Seite {page}: {len(stellenangebote)} Jobs "
                  f"(gesamt: {len(results) + len(stellenangebote)})")

            if not stellenangebote:
                break

            for raw in stellenangebote:
                results.append(self._map(raw, search_term))
                if len(results) >= effective_limit:
                    break

            # Wenn weniger als Page-Size zurückkommt, sind wir am Ende
            if len(stellenangebote) < size:
                break

            page += 1
            time.sleep(0.4)  # Schonend zur API (max 1000/h erlaubt)

        return results

    def _map(self, raw: dict, search_term: str) -> UnifiedJob:
        """Mappt Arbeitsagentur-Antwort auf UnifiedJob-Schema."""
        ort = raw.get("arbeitsort", {}) or {}
        city = ort.get("ort", "")
        region = ort.get("region", "")

        # Job-Detail-Link auf der Jobbörse
        # 1. Bevorzugt: refnr (eindeutige Referenz-Nummer)
        # 2. Fallback: hashId (URL-sicherer Hash)
        # 3. Letzter Fallback: Such-URL mit Titel + Arbeitgeber
        ref = raw.get("refnr", "")
        hash_id = raw.get("hashId", "")
        title = raw.get("titel", "")
        arbeitgeber = raw.get("arbeitgeber", "")

        if ref:
            apply_link = f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{ref}"
        elif hash_id:
            apply_link = f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{hash_id}"
        elif title:
            # Fallback: Suche nach Titel + Arbeitgeber als URL-Parameter
            from urllib.parse import quote_plus
            query = quote_plus(f"{title} {arbeitgeber}".strip())
            apply_link = (
                f"https://www.arbeitsagentur.de/jobsuche/suche?was={query}"
            )
        else:
            apply_link = None

        description = raw.get("stellenbeschreibung") or raw.get("titel") or ""

        return UnifiedJob(
            job_id=self.make_job_id(ref or hash_id or f"{title}_{arbeitgeber}"),
            job_title=title,
            employer_name=arbeitgeber,
            source=self.name,
            job_description=description,
            job_apply_link=apply_link,
            job_city=city,
            job_state=region,
            job_country="Deutschland",
            job_employment_type=(raw.get("arbeitszeitmodelle") or [None])[0],
            job_is_remote=None,
            job_posted_at=raw.get("aktuelleVeroeffentlichungsdatum"),
            search_term=search_term,
        )
