"""
Multi-Source Job-Collector.

Orchestriert die Job-Quellen aus src/sources/ und schreibt die Ergebnisse in
ein einheitliches Format nach data/raw/jobs_raw_master.csv.

Beispiele:
    # Alle Quellen, alle Standard-Suchbegriffe, deutschlandweit
    python -m src.collect_jobs

    # Nur Arbeitsagentur, deutschlandweit
    python -m src.collect_jobs --sources arbeitsagentur

    # Nur lokal in NRW
    python -m src.collect_jobs --location "Köln" --umkreis 50

    # Eigene Suchbegriffe
    python -m src.collect_jobs --terms "data analyst" "python developer"

    # Größere Tiefe pro Suche
    python -m src.collect_jobs --max-results 200
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from dotenv import load_dotenv

from src.config import RAW_DIR, SEARCH_TERMS
from src.sources import get_all_sources

load_dotenv()


def merge_with_master(new_df: pd.DataFrame) -> pd.DataFrame:
    """Lädt bestehende Master-Datei, hängt neue Daten an, dedupliziert über job_id."""
    master_path = RAW_DIR / "jobs_raw_master.csv"
    if master_path.exists():
        try:
            existing = pd.read_csv(master_path)
            print(f"\n📂 Bestehende Master-Datei: {len(existing)} Jobs")
            combined = pd.concat([existing, new_df], ignore_index=True)
        except Exception as e:
            print(f"⚠️  Konnte Master nicht laden ({e}). Starte neu.")
            combined = new_df
    else:
        combined = new_df

    if "job_id" in combined.columns:
        before = len(combined)
        combined = combined.drop_duplicates(subset=["job_id"], keep="last")
        print(f"   Nach Dedup: {len(combined)} Jobs (-{before - len(combined)})")

    return combined


def main(
    source_names: Optional[list[str]] = None,
    custom_terms: Optional[list[str]] = None,
    location: Optional[str] = None,
    umkreis: int = 50,
    max_results: Optional[int] = None,
    berufsfeld: Optional[str] = None,
    veroeffentlichtseit: Optional[int] = None,
) -> None:
    sources = get_all_sources()
    if source_names:
        sources = [s for s in sources if s.name in source_names]

    if not sources:
        print("❌ Keine Quellen ausgewählt.")
        sys.exit(1)

    terms = custom_terms or SEARCH_TERMS

    print("=" * 64)
    print("🔍 Multi-Source Job Collection")
    print(f"   Quellen:        {[s.name for s in sources]}")
    print(f"   Suchbegriffe:   {len(terms)}")
    print(f"   Ort:            {location or '— (deutschlandweit)'}")
    if location:
        print(f"   Umkreis:        {umkreis} km")
    if berufsfeld:
        print(f"   Berufsfeld:     {berufsfeld}")
    if veroeffentlichtseit is not None:
        print(f"   Frische:        Jobs der letzten {veroeffentlichtseit} Tage")
    print(f"   Max pro Suche:  {max_results if max_results else 'ALLE verfügbaren'}")
    print("=" * 64)

    all_jobs = []

    for source in sources:
        print(f"\n──── Quelle: {source.name} ────")
        for i, term in enumerate(terms, start=1):
            print(f"\n[{source.name} {i}/{len(terms)}] '{term}'")
            try:
                # Quellen-spezifische Parameter zusammenbauen
                kwargs = {
                    "search_term": term,
                    "max_results": max_results,
                    "location": location,
                }
                if source.name == "arbeitsagentur":
                    kwargs["umkreis"] = umkreis
                    if berufsfeld:
                        kwargs["berufsfeld"] = berufsfeld
                    if veroeffentlichtseit is not None:
                        kwargs["veroeffentlichtseit"] = veroeffentlichtseit
                elif source.name == "adzuna":
                    kwargs["distance_km"] = umkreis

                jobs = source.fetch(**kwargs)
                for j in jobs:
                    if not j.search_term:
                        j.search_term = term
                all_jobs.extend(j.to_dict() for j in jobs)
                print(f"  -> {len(jobs)} Jobs gesammelt")
            except Exception as e:
                print(f"  ❌ Fehler: {e}")

    if not all_jobs:
        print("\n❌ Keine Daten gesammelt.")
        sys.exit(1)

    df_new = pd.DataFrame(all_jobs)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Backup-Datei dieses Laufs
    backup_path = RAW_DIR / f"jobs_raw_{timestamp}.csv"
    df_new.to_csv(backup_path, index=False)

    # Master-Datei aktualisieren
    df_master = merge_with_master(df_new)
    master_path = RAW_DIR / "jobs_raw_master.csv"
    df_master.to_csv(master_path, index=False)

    print("\n" + "=" * 64)
    print("✅ Collection abgeschlossen")
    print(f"   Neue Jobs (dieser Lauf): {len(df_new)}")
    print(f"   Master-Datei (gesamt):   {len(df_master)}")
    print(f"\n   Verteilung pro Quelle (dieser Lauf):")
    for src, cnt in df_new["source"].value_counts().items():
        print(f"     {src}: {cnt}")
    print(f"\n   Backup: {backup_path.name}")
    print("=" * 64)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-Source Job Collector")
    parser.add_argument(
        "--sources", nargs="+", default=None,
        choices=["arbeitsagentur", "adzuna"],
        help="Welche Quellen nutzen (default: alle)",
    )
    parser.add_argument(
        "--terms", nargs="+", default=None,
        help="Eigene Suchbegriffe (default: SEARCH_TERMS aus config.py)",
    )
    parser.add_argument(
        "--location", default=None,
        help="Ort für lokale Suche, z.B. 'Köln' (default: deutschlandweit)",
    )
    parser.add_argument(
        "--umkreis", type=int, default=50,
        help="Suchradius in km (nur mit --location, default: 50)",
    )
    parser.add_argument(
        "--max-results", type=int, default=None,
        help="Max Jobs pro Quelle und Suchbegriff (default: ALLE verfügbaren)",
    )
    parser.add_argument(
        "--berufsfeld", default=None,
        help="Berufsfeld-Filter für Arbeitsagentur, "
             "z.B. 'Informatik, Information und Kommunikation'",
    )
    parser.add_argument(
        "--seit-tagen", type=int, default=None, dest="veroeffentlichtseit",
        help="Nur Jobs der letzten N Tage (0-100, nur Arbeitsagentur)",
    )
    args = parser.parse_args()

    main(
        source_names=args.sources,
        custom_terms=args.terms,
        location=args.location,
        umkreis=args.umkreis,
        max_results=args.max_results,
        berufsfeld=args.berufsfeld,
        veroeffentlichtseit=args.veroeffentlichtseit,
    )
