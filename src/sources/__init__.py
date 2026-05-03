"""
Job-Datenquellen.

Jede Quelle ist eine Subklasse von JobSource und liefert UnifiedJob-Objekte.
Neue Quellen hinzufügen: Subklasse von JobSource erstellen und in
get_all_sources() eintragen.
"""

from src.sources.adzuna import AdzunaSource
from src.sources.arbeitsagentur import ArbeitsagenturSource
from src.sources.base import JobSource, UnifiedJob


def get_all_sources() -> list[JobSource]:
    """Liste aller verfügbaren Job-Quellen."""
    return [
        ArbeitsagenturSource(),  # größte Quelle, kostenlos & unbegrenzt
        AdzunaSource(),          # Aggregator, kostenlos (250 Calls/Tag)
    ]


__all__ = [
    "JobSource",
    "UnifiedJob",
    "ArbeitsagenturSource",
    "AdzunaSource",
    "get_all_sources",
]
