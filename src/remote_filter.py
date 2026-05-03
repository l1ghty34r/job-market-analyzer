"""
Live-Erkennung von Remote/Homeoffice-Stellen.

Wird beim Filtern in den Dashboard-Tabs verwendet (zusätzlich zur
beim Cleaning gesetzten `is_remote_friendly`-Spalte). So fangen wir
auch Stellen ein, die durch ein älteres Cleaning übersehen wurden.
"""

import re

import pandas as pd


# Liste an Schlüsselbegriffen, die "Homeoffice/Remote möglich" signalisieren.
# Word-boundaries werden bei Bedarf in der Regex angewendet.
REMOTE_PATTERNS = [
    # Englisch
    r"\bremote\b",
    r"\bhome[\s\-]?office\b",
    r"\bhomeoffice\b",
    r"\bwork\s+from\s+home\b",
    r"\bwfh\b",
    r"\bmobile\s+work\b",
    # Deutsch
    r"\bmobiles?\s+arbeit(?:en)?\b",
    r"\bmobile[\s\-]?arbeit\b",
    r"\bortsunabh[äa]ngig\b",
    r"\bortsungebunden\b",
    r"\bortsflexibel\b",
    r"\bvon\s+zu\s*hause\b",
    r"\btele[\s\-]?arbeit\b",
    # Hybrid-Varianten
    r"\bhybrid(?:es?)?\s+arbeit(?:en)?\b",
    r"\bhybrid\b",
]

# Vorkompilierte Regex (case-insensitive) für Performance bei vielen Jobs
_COMBINED_REGEX = re.compile(
    "|".join(REMOTE_PATTERNS),
    flags=re.IGNORECASE,
)


def is_remote_friendly_text(*texts: str) -> bool:
    """Prüft ob einer der gegebenen Texte einen Remote-/Homeoffice-Hinweis enthält.

    Args:
        *texts: Beliebig viele Text-Strings (z.B. Titel + Description)

    Returns:
        True wenn mindestens ein Remote-Keyword gefunden wird
    """
    combined = " ".join(str(t or "") for t in texts)
    if not combined.strip():
        return False
    return bool(_COMBINED_REGEX.search(combined))


def filter_remote_jobs(df: pd.DataFrame) -> pd.DataFrame:
    """Filtert einen Jobs-DataFrame auf Stellen mit Remote-/Homeoffice-Hinweisen.

    Berücksichtigt drei Quellen, damit nichts durchrutscht:
        1. Spalte `is_remote_friendly` aus dem Cleaning (falls vorhanden)
        2. Spalte `remote_type` (Remote / Hybrid / Remote/Hybrid erwähnt)
        3. Live-Suche in `job_title` + `job_description`

    Returns:
        Gefilterter DataFrame, der nur Remote-fähige Jobs enthält.
    """
    if df.empty:
        return df

    masks = []

    # 1. Vorberechnete Spalte
    if "is_remote_friendly" in df.columns:
        masks.append(df["is_remote_friendly"].fillna(False).astype(bool))

    # 2. remote_type
    if "remote_type" in df.columns:
        masks.append(
            df["remote_type"].isin(["Remote", "Hybrid", "Remote/Hybrid erwähnt"])
        )

    # 3. Live-Suche im Text
    title_col = df["job_title"].fillna("") if "job_title" in df.columns else ""
    desc_col = df["job_description"].fillna("") if "job_description" in df.columns else ""
    combined = (title_col + " " + desc_col)
    text_match = combined.str.contains(
        _COMBINED_REGEX, regex=True, na=False
    )
    masks.append(text_match)

    # Vereinen: ein Job zählt als Remote wenn IRGENDEINE Quelle das sagt
    final_mask = masks[0]
    for m in masks[1:]:
        final_mask = final_mask | m

    return df[final_mask].copy()
