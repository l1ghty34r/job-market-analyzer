"""
Extrahiert technische Skills aus Job-Beschreibungen.

Verbesserungen gegenüber naivem Substring-Matching:
- Wortgrenzen: 'git' matcht nicht in 'digital'
- Synonyme: 'powerbi' → 'power bi', 'ml' → 'machine learning'
- Mehrwort-Skills: 'machine learning', 'power bi', 'scikit-learn'

Output:
- data/exports/jobs_with_skills.csv: Jobs + Liste gefundener Skills
- data/exports/job_skills.csv: Normalisierte Skill-Tabelle (1 Zeile = 1 Job-Skill-Paar)
"""

import re

import pandas as pd

from src.config import PROCESSED_DIR, EXPORT_DIR, SKILL_KEYWORDS


# Synonyme/Schreibvarianten → kanonische Form
SKILL_SYNONYMS = {
    "powerbi": "power bi",
    "power-bi": "power bi",
    "ms power bi": "power bi",
    "ml": "machine learning",
    "scikit learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "postgres": "postgresql",
    "psql": "postgresql",
    "google cloud": "gcp",
    "google cloud platform": "gcp",
    "amazon web services": "aws",
    "ms excel": "excel",
    "github": "git",
    "gitlab": "git",
    "google analytics 4": "ga4",
    "google analytics": "ga4",
}


def build_skill_pattern(skill: str) -> re.Pattern:
    """
    Baut eine Regex mit Wortgrenzen für einen Skill.

    Spezialfall: Skills die mit Sonderzeichen enden (c++, c#) brauchen
    keine rechte Wortgrenze. Bei mehrwortigen Skills sind Wortgrenzen
    nur am Anfang/Ende sinnvoll.
    """
    escaped = re.escape(skill)
    # \b funktioniert nicht zuverlässig vor/nach Sonderzeichen wie '+'
    # Daher: Wortgrenze nur wenn Skill mit Wortzeichen beginnt/endet
    left = r"\b" if skill[0].isalnum() else r""
    right = r"\b" if skill[-1].isalnum() else r""
    return re.compile(left + escaped + right, re.IGNORECASE)


def extract_skills(text: str, patterns: dict[str, re.Pattern]) -> list[str]:
    """
    Findet alle Skills im Text via Regex-Patterns.

    Returns: Sortierte Liste eindeutiger Skill-Namen (kanonische Form).
    """
    text = str(text)
    found = set()

    for skill, pattern in patterns.items():
        if pattern.search(text):
            # Synonym-Mapping anwenden
            canonical = SKILL_SYNONYMS.get(skill.lower(), skill.lower())
            found.add(canonical)

    return sorted(found)


def main() -> None:
    input_file = PROCESSED_DIR / "jobs_cleaned.csv"
    df = pd.read_csv(input_file)

    print(f"Verwende Datei: {input_file}")
    print(f"Anzahl Jobs: {len(df)}")

    # Vollständige Keyword-Liste: SKILL_KEYWORDS + Synonyme als Suchbegriffe
    all_search_terms = list(SKILL_KEYWORDS) + list(SKILL_SYNONYMS.keys())

    # Patterns vorkompilieren (Performance)
    patterns = {term: build_skill_pattern(term) for term in all_search_terms}

    # Kombinierter Text für Suche
    combined_text = (
        df["job_title"].fillna("").astype(str) + " "
        + df["job_description"].fillna("").astype(str)
    )

    df["skills_found"] = combined_text.apply(
        lambda x: extract_skills(x, patterns)
    )
    df["skill_count"] = df["skills_found"].apply(len)

    # Export 1: Jobs mit Skill-Listen
    jobs_with_skills_file = EXPORT_DIR / "jobs_with_skills.csv"
    df.to_csv(jobs_with_skills_file, index=False)

    # Export 2: Normalisierte Skill-Tabelle (Long-Format)
    skill_rows = []
    for _, row in df.iterrows():
        for skill in row["skills_found"]:
            skill_rows.append({
                "job_id": row["job_id"],
                "job_title": row["job_title"],
                "employer_name": row["employer_name"],
                "job_city": row["job_city"],
                "job_state": row.get("job_state", ""),
                "role_group": row["role_group"],
                "remote_type": row["remote_type"],
                "is_junior": row["is_junior"],
                "skill": skill,
            })

    skills_df = pd.DataFrame(skill_rows)
    skills_file = EXPORT_DIR / "job_skills.csv"
    skills_df.to_csv(skills_file, index=False)

    print("\n--- Skill-Extraktion abgeschlossen ---")
    print(f"Jobs mit Skill-Listen: {jobs_with_skills_file}")
    print(f"Normalisierte Skill-Tabelle: {skills_file}")
    print(f"Anzahl Skill-Zuordnungen: {len(skills_df)}")
    print(f"Ø Skills pro Job: {df['skill_count'].mean():.1f}")

    if not skills_df.empty:
        print("\nTop 15 Skills:")
        print(skills_df["skill"].value_counts().head(15).to_string())

        print("\nTop 5 Skills pro Rolle:")
        top_by_role = (
            skills_df.groupby(["role_group", "skill"])
            .size()
            .reset_index(name="count")
            .sort_values(["role_group", "count"], ascending=[True, False])
        )
        print(top_by_role.groupby("role_group").head(5).to_string(index=False))


if __name__ == "__main__":
    main()
