"""
Lookup deutscher Städte mit ihrer Region (Bundesland + Großraum).

Wird für den dynamischen Match-Score verwendet, ohne Geocoding-API zu brauchen.
Zwei Städte gelten als "in derselben Region", wenn sie dasselbe Großraum-Tag haben.
"""

# Großräume (regional cluster) für Match-Score
# Stadt → (Bundesland, Großraum-Tag)
GERMAN_CITIES = {
    # Rhein-Ruhr (NRW Metropolregion)
    "leverkusen":          ("NRW", "rhein-ruhr"),
    "köln":                ("NRW", "rhein-ruhr"),
    "koeln":               ("NRW", "rhein-ruhr"),
    "düsseldorf":          ("NRW", "rhein-ruhr"),
    "duesseldorf":         ("NRW", "rhein-ruhr"),
    "bonn":                ("NRW", "rhein-ruhr"),
    "essen":               ("NRW", "rhein-ruhr"),
    "dortmund":            ("NRW", "rhein-ruhr"),
    "duisburg":            ("NRW", "rhein-ruhr"),
    "bochum":              ("NRW", "rhein-ruhr"),
    "wuppertal":           ("NRW", "rhein-ruhr"),
    "mönchengladbach":     ("NRW", "rhein-ruhr"),
    "moenchengladbach":    ("NRW", "rhein-ruhr"),
    "krefeld":             ("NRW", "rhein-ruhr"),
    "neuss":               ("NRW", "rhein-ruhr"),
    "solingen":            ("NRW", "rhein-ruhr"),
    "remscheid":           ("NRW", "rhein-ruhr"),
    "gelsenkirchen":       ("NRW", "rhein-ruhr"),
    "oberhausen":          ("NRW", "rhein-ruhr"),
    "bergisch gladbach":   ("NRW", "rhein-ruhr"),
    "troisdorf":           ("NRW", "rhein-ruhr"),
    "hagen":               ("NRW", "rhein-ruhr"),
    "mülheim an der ruhr": ("NRW", "rhein-ruhr"),
    "muelheim an der ruhr": ("NRW", "rhein-ruhr"),
    "recklinghausen":      ("NRW", "rhein-ruhr"),
    "bottrop":             ("NRW", "rhein-ruhr"),
    "herne":               ("NRW", "rhein-ruhr"),

    # Restliches NRW
    "aachen":              ("NRW", "aachen-region"),
    "münster":             ("NRW", "münsterland"),
    "muenster":            ("NRW", "münsterland"),
    "bielefeld":           ("NRW", "ostwestfalen"),
    "paderborn":           ("NRW", "ostwestfalen"),
    "siegen":              ("NRW", "südwestfalen"),
    "hamm":                ("NRW", "rhein-ruhr"),

    # Berlin-Brandenburg
    "berlin":              ("Berlin", "berlin-bb"),
    "potsdam":             ("Brandenburg", "berlin-bb"),

    # Hamburg-Region
    "hamburg":             ("Hamburg", "hamburg-region"),
    "lübeck":              ("Schleswig-Holstein", "hamburg-region"),
    "luebeck":             ("Schleswig-Holstein", "hamburg-region"),
    "kiel":                ("Schleswig-Holstein", "hamburg-region"),

    # München / Oberbayern
    "münchen":             ("Bayern", "münchen-region"),
    "muenchen":            ("Bayern", "münchen-region"),
    "augsburg":            ("Bayern", "münchen-region"),
    "ingolstadt":          ("Bayern", "münchen-region"),
    "rosenheim":           ("Bayern", "münchen-region"),

    # Nordbayern
    "nürnberg":            ("Bayern", "nordbayern"),
    "nuernberg":           ("Bayern", "nordbayern"),
    "fürth":               ("Bayern", "nordbayern"),
    "fuerth":              ("Bayern", "nordbayern"),
    "erlangen":            ("Bayern", "nordbayern"),
    "regensburg":          ("Bayern", "nordbayern"),
    "würzburg":            ("Bayern", "nordbayern"),
    "wuerzburg":           ("Bayern", "nordbayern"),
    "bamberg":             ("Bayern", "nordbayern"),

    # Stuttgart / Baden-Württemberg
    "stuttgart":           ("Baden-Württemberg", "stuttgart-region"),
    "karlsruhe":           ("Baden-Württemberg", "stuttgart-region"),
    "mannheim":            ("Baden-Württemberg", "rhein-neckar"),
    "heidelberg":          ("Baden-Württemberg", "rhein-neckar"),
    "ludwigshafen":        ("Rheinland-Pfalz", "rhein-neckar"),
    "heilbronn":           ("Baden-Württemberg", "stuttgart-region"),
    "freiburg":            ("Baden-Württemberg", "südbaden"),
    "ulm":                 ("Baden-Württemberg", "stuttgart-region"),
    "tübingen":            ("Baden-Württemberg", "stuttgart-region"),
    "tuebingen":           ("Baden-Württemberg", "stuttgart-region"),
    "reutlingen":          ("Baden-Württemberg", "stuttgart-region"),
    "pforzheim":           ("Baden-Württemberg", "stuttgart-region"),
    "konstanz":            ("Baden-Württemberg", "südbaden"),

    # Frankfurt / Rhein-Main
    "frankfurt":           ("Hessen", "rhein-main"),
    "frankfurt am main":   ("Hessen", "rhein-main"),
    "wiesbaden":           ("Hessen", "rhein-main"),
    "mainz":               ("Rheinland-Pfalz", "rhein-main"),
    "darmstadt":           ("Hessen", "rhein-main"),
    "offenbach":           ("Hessen", "rhein-main"),
    "hanau":               ("Hessen", "rhein-main"),

    # Restl. Hessen
    "kassel":              ("Hessen", "nordhessen"),
    "marburg":             ("Hessen", "mittelhessen"),
    "gießen":              ("Hessen", "mittelhessen"),
    "giessen":             ("Hessen", "mittelhessen"),
    "fulda":               ("Hessen", "osthessen"),

    # Niedersachsen / Bremen
    "hannover":            ("Niedersachsen", "hannover-region"),
    "braunschweig":        ("Niedersachsen", "hannover-region"),
    "wolfsburg":           ("Niedersachsen", "hannover-region"),
    "göttingen":           ("Niedersachsen", "südniedersachsen"),
    "goettingen":          ("Niedersachsen", "südniedersachsen"),
    "osnabrück":           ("Niedersachsen", "osnabrück-region"),
    "osnabrueck":          ("Niedersachsen", "osnabrück-region"),
    "oldenburg":           ("Niedersachsen", "weser-ems"),
    "bremen":              ("Bremen", "weser-ems"),
    "bremerhaven":         ("Bremen", "weser-ems"),

    # Sachsen
    "dresden":             ("Sachsen", "sachsen"),
    "leipzig":             ("Sachsen", "sachsen"),
    "chemnitz":            ("Sachsen", "sachsen"),

    # Sachsen-Anhalt / Thüringen
    "magdeburg":           ("Sachsen-Anhalt", "mitteldeutschland"),
    "halle":               ("Sachsen-Anhalt", "mitteldeutschland"),
    "halle (saale)":       ("Sachsen-Anhalt", "mitteldeutschland"),
    "erfurt":              ("Thüringen", "mitteldeutschland"),
    "jena":                ("Thüringen", "mitteldeutschland"),
    "weimar":              ("Thüringen", "mitteldeutschland"),

    # Mecklenburg-Vorpommern
    "rostock":             ("Mecklenburg-Vorpommern", "ostsee"),
    "schwerin":            ("Mecklenburg-Vorpommern", "ostsee"),
    "greifswald":          ("Mecklenburg-Vorpommern", "ostsee"),

    # Saarland
    "saarbrücken":         ("Saarland", "saar-region"),
    "saarbruecken":        ("Saarland", "saar-region"),

    # Rheinland-Pfalz
    "trier":               ("Rheinland-Pfalz", "saar-region"),
    "koblenz":             ("Rheinland-Pfalz", "mittelrhein"),
    "kaiserslautern":      ("Rheinland-Pfalz", "rhein-neckar"),
}


def normalize_city(name: str) -> str:
    """Normalisiert einen Städtenamen für den Lookup."""
    return str(name or "").strip().lower()


def lookup_region(city: str) -> tuple[str | None, str | None]:
    """Findet (Bundesland, Großraum) für eine Stadt. (None, None) falls unbekannt."""
    norm = normalize_city(city)
    if not norm:
        return None, None
    if norm in GERMAN_CITIES:
        return GERMAN_CITIES[norm]
    # Fallback: erstes Wort versuchen (z.B. "Frankfurt am Main" → "frankfurt")
    first_word = norm.split()[0] if norm.split() else ""
    if first_word in GERMAN_CITIES:
        return GERMAN_CITIES[first_word]
    return None, None


def calculate_match_score(
    job_city: str,
    job_state: str,
    job_remote_type: str,
    user_city: str,
) -> int:
    """
    Berechnet Standort-Match-Score (0-100).

    Logik:
        100 — Remote (perfekt für Homeoffice-Suche)
         90 — Hybrid im selben Großraum (gelegentlich Office, aber nah)
         80 — Onsite in derselben Stadt
         60 — Onsite im selben Großraum
         40 — Onsite im selben Bundesland
         30 — Hybrid woanders (selten machbar wegen Pendeln)
         20 — "Remote/Hybrid erwähnt" außerhalb der Region (Möglichkeit, aber unklar)
          0 — Onsite woanders, keine Remote-Option
    """
    job_remote = str(job_remote_type or "").lower()

    # Remote-Job → immer Top-Score, unabhängig von Stadt
    if job_remote == "remote":
        return 100

    if not user_city:
        # Kein Wohnort eingegeben → Remote-/Hybrid-Score nur grob
        if job_remote == "hybrid":
            return 60
        if "remote" in job_remote or "hybrid" in job_remote:
            return 40
        return 0

    user_norm = normalize_city(user_city)
    job_norm = normalize_city(job_city)

    user_state, user_cluster = lookup_region(user_city)
    job_state_lookup, job_cluster = lookup_region(job_city)

    # Selbe Stadt
    same_city = user_norm and job_norm and user_norm == job_norm
    # Selber Großraum (z.B. Köln & Düsseldorf, beides "rhein-ruhr")
    same_cluster = (user_cluster and job_cluster and user_cluster == job_cluster)
    # Selbes Bundesland
    job_state_str = job_state_lookup or str(job_state or "")
    same_state = (user_state and job_state_str
                  and user_state.lower() in job_state_str.lower())

    # Hybrid-Bewertung
    if job_remote == "hybrid":
        if same_cluster:
            return 90
        if same_state:
            return 50
        return 30

    # Onsite-Bewertung
    if same_city:
        return 80
    if same_cluster:
        return 60
    if same_state:
        return 40

    # "Remote/Hybrid erwähnt" – unklar
    if "remote" in job_remote or "hybrid" in job_remote:
        return 20

    return 0
