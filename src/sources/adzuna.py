"""
Adzuna API – Job-Aggregator mit guter Deutschland-Abdeckung.

API-Doku: https://developer.adzuna.com/
Authentifizierung: app_id + app_key (kostenlos auf der Website registrieren)
Free Tier: 250 Calls/Tag, 1000 Ergebnisse/Call

Registrieren auf https://developer.adzuna.com/signup
"""

import os
import time
from typing import Optional

import requests

from src.sources.base import JobSource, UnifiedJob


class AdzunaSource(JobSource):
    name = "adzuna"
    base_url = "https://api.adzuna.com/v1/api/jobs/de/search"

    def __init__(self):
        # Liest aus st.secrets ODER os.environ (Cloud-kompatibel)
        self.app_id = self._read_credential("ADZUNA_APP_ID")
        self.app_key = self._read_credential("ADZUNA_APP_KEY")

    @staticmethod
    def _read_credential(key: str) -> str | None:
        """Liest Credential aus st.secrets (Streamlit Cloud) oder .env (lokal)."""
        try:
            import streamlit as st
            if hasattr(st, "secrets") and key in st.secrets:
                return str(st.secrets[key])
        except Exception:
            pass
        return os.getenv(key)

    def fetch(
        self,
        search_term: str,
        max_results: Optional[int] = None,
        location: Optional[str] = None,
        distance_km: int = 50,
    ) -> list[UnifiedJob]:
        if not (self.app_id and self.app_key):
            print(f"  ⚠️  [{self.name}] Keine Credentials – überspringe.")
            return []

        # Adzuna Hard-Cap (sonst sinnlos viele Calls)
        effective_limit = max_results if max_results else 1000

        results: list[UnifiedJob] = []
        page = 1
        per_page = 50

        while len(results) < effective_limit:
            url = f"{self.base_url}/{page}"
            params = {
                "app_id": self.app_id,
                "app_key": self.app_key,
                "results_per_page": per_page,
                "what": search_term,
                "content-type": "application/json",
            }
            if location:
                params["where"] = location
                params["distance"] = distance_km

            try:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
            except requests.exceptions.RequestException as e:
                print(f"  ❌ [{self.name}] Fehler auf Seite {page}: {e}")
                break

            jobs = data.get("results", []) or []
            print(f"  [{self.name}] Seite {page}: {len(jobs)} Jobs")

            if not jobs:
                break

            for raw in jobs:
                results.append(self._map(raw, search_term))
                if len(results) >= effective_limit:
                    break

            if len(jobs) < per_page:
                break

            page += 1
            time.sleep(0.3)

        return results[:effective_limit]

    def _map(self, raw: dict, search_term: str) -> UnifiedJob:
        """Mappt Adzuna-Antwort auf UnifiedJob-Schema."""
        location_obj = raw.get("location", {}) or {}
        area = location_obj.get("area", []) or []
        # Area-Format: ["Deutschland", "Bundesland", "Stadt"] oder ähnlich
        # Wir extrahieren das Letzte als Stadt, das Vorletzte als Bundesland
        city = area[-1] if len(area) >= 1 else None
        state = area[-2] if len(area) >= 2 else None

        company = raw.get("company", {}) or {}
        category = raw.get("category", {}) or {}

        # Adzuna-spezifisch: contract_type kann "permanent" / "contract" sein
        contract_type = raw.get("contract_type") or raw.get("contract_time")

        return UnifiedJob(
            job_id=self.make_job_id(str(raw.get("id", ""))),
            job_title=raw.get("title", ""),
            employer_name=company.get("display_name", ""),
            source=self.name,
            job_description=raw.get("description"),
            job_apply_link=raw.get("redirect_url"),
            job_city=city,
            job_state=state,
            job_country="Deutschland",
            job_employment_type=contract_type,
            job_is_remote=None,  # Adzuna hat kein klares Remote-Flag
            job_posted_at=raw.get("created"),
            salary_min=raw.get("salary_min"),
            salary_max=raw.get("salary_max"),
            salary_period="yearly" if raw.get("salary_min") else None,
            search_term=search_term,
        )
