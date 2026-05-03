"""
Basisklasse für Job-Datenquellen.

Jede Quelle (Arbeitsagentur, Adzuna) implementiert eine
Subklasse von JobSource und liefert Daten im einheitlichen Schema
zurück. So bleiben Cleaning und Analyse quellenagnostisch.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional


# ----------------------------------------------------------------------------
# Einheitliches Schema – alle Quellen mappen ihre Antworten hierauf
# ----------------------------------------------------------------------------
@dataclass
class UnifiedJob:
    """Einheitliches Schema, das alle Quellen ausgeben."""
    # Pflichtfelder
    job_id: str
    job_title: str
    employer_name: str
    source: str                       # "arbeitsagentur", "adzuna"

    # Optional – Pflicht wenn vorhanden
    job_description: Optional[str] = None
    job_apply_link: Optional[str] = None
    job_city: Optional[str] = None
    job_state: Optional[str] = None
    job_country: str = "Deutschland"
    job_employment_type: Optional[str] = None
    job_is_remote: Optional[bool] = None
    job_posted_at: Optional[str] = None
    job_posted_at_datetime_utc: Optional[datetime] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_period: Optional[str] = None
    search_term: Optional[str] = None

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary für DataFrames."""
        return asdict(self)


class JobSource(ABC):
    """Basisklasse für eine Job-Datenquelle."""

    name: str = "base"

    @abstractmethod
    def fetch(
        self,
        search_term: str,
        max_results: int = 50,
        location: Optional[str] = None,
    ) -> list[UnifiedJob]:
        """Holt Jobs für einen Suchbegriff. Liefert UnifiedJob-Liste."""
        ...

    def make_job_id(self, raw_id: str) -> str:
        """Erstellt eine quellen-präfixierte job_id, um Kollisionen zu vermeiden."""
        return f"{self.name}_{raw_id}"
