"""
Diagnose-Skript: Zeigt, welche Jobs als 'Other' klassifiziert werden.

Hilft uns zu verstehen, warum so viele Jobs ausgefiltert werden.

Ausführen:
    python -m src.diagnose_classification
"""

import pandas as pd
from collections import Counter

from src.config import PROCESSED_DIR


def main():
    path = PROCESSED_DIR / "jobs_cleaned.csv"
    if not path.exists():
        print(f"❌ Datei nicht gefunden: {path}")
        return

    df = pd.read_csv(path)
    print(f"📊 Gesamt: {len(df)} Jobs\n")

    # Verteilung pro role_group
    print("=" * 60)
    print("VERTEILUNG NACH ROLLEN-KATEGORIE:")
    print("=" * 60)
    counts = df["role_group"].value_counts()
    for role, count in counts.items():
        pct = count / len(df) * 100
        print(f"  {role:30s} {count:>5d}  ({pct:>5.1f}%)")

    # 'Other'-Jobs analysieren
    other = df[df["role_group"] == "Other"]
    if other.empty:
        print("\n✅ Keine 'Other'-Jobs gefunden!")
        return

    print(f"\n{'=' * 60}")
    print(f"'OTHER'-JOBS ANALYSE ({len(other)} Jobs):")
    print("=" * 60)

    # Häufigste Wörter in 'Other'-Job-Titeln
    all_words = []
    for title in other["job_title"].dropna():
        # Wörter extrahieren, lowercase, nur alphabetisch
        words = [w.lower().strip(".,()/-") for w in str(title).split()]
        words = [w for w in words if len(w) > 3 and w.isalpha()]
        all_words.extend(words)

    print("\nHäufigste Wörter in 'Other'-Titeln (zeigt was wir noch erkennen könnten):")
    word_counts = Counter(all_words)
    for word, count in word_counts.most_common(30):
        print(f"  {word:30s} {count:>5d}")

    # 20 zufällige 'Other'-Titel zeigen
    print(f"\n{'=' * 60}")
    print("20 ZUFÄLLIGE 'OTHER'-JOB-TITEL:")
    print("=" * 60)
    sample = other.sample(min(20, len(other)), random_state=42)
    for _, row in sample.iterrows():
        title = str(row.get("job_title", ""))[:80]
        source = str(row.get("source", "?"))
        print(f"  [{source:15s}] {title}")


if __name__ == "__main__":
    main()
