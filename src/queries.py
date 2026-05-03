"""
Python-Wrapper für die SQL-Queries aus sql/analysis_queries.sql.

Stellt die Queries als wiederverwendbare Funktionen bereit, die
DataFrames zurückgeben. So können Notebooks und Streamlit-Pages
nahtlos zwischen CSV- und Postgres-Backend wechseln.

Beispiel:
    from src.queries import top_skills, top_skills_per_role
    from src.load_to_postgres import get_engine

    engine = get_engine()
    df = top_skills(engine, limit=10)
"""

import pandas as pd
from sqlalchemy.engine import Engine


def top_skills(engine: Engine, limit: int = 10) -> pd.DataFrame:
    """Q1: Häufigste Skills insgesamt."""
    sql = """
        SELECT s.skill_name, COUNT(*) AS mention_count
        FROM job_skills js
        JOIN skills s ON js.skill_id = s.skill_id
        GROUP BY s.skill_name
        ORDER BY mention_count DESC
        LIMIT %(limit)s;
    """
    return pd.read_sql(sql, engine, params={"limit": limit})


def top_skills_per_role(engine: Engine, top_n: int = 5) -> pd.DataFrame:
    """Q2: Top N Skills pro Rolle (mit Window Function)."""
    sql = """
        WITH skill_counts AS (
            SELECT
                j.role_group,
                s.skill_name,
                COUNT(*) AS cnt,
                ROW_NUMBER() OVER (
                    PARTITION BY j.role_group
                    ORDER BY COUNT(*) DESC
                ) AS rank
            FROM jobs j
            JOIN job_skills js ON j.job_id  = js.job_id
            JOIN skills      s ON js.skill_id = s.skill_id
            WHERE j.role_group <> 'Other'
            GROUP BY j.role_group, s.skill_name
        )
        SELECT role_group, skill_name, cnt
        FROM skill_counts
        WHERE rank <= %(top_n)s
        ORDER BY role_group, cnt DESC;
    """
    return pd.read_sql(sql, engine, params={"top_n": top_n})


def jobs_per_role_remote(engine: Engine) -> pd.DataFrame:
    """Q3: Jobs pro Rolle und Arbeitsform."""
    sql = """
        SELECT role_group, remote_type, COUNT(*) AS jobs_count
        FROM jobs
        GROUP BY role_group, remote_type
        ORDER BY role_group, jobs_count DESC;
    """
    return pd.read_sql(sql, engine)


def junior_share_per_role(engine: Engine) -> pd.DataFrame:
    """Q4: Junior-Anteil pro Rolle."""
    sql = """
        SELECT
            role_group,
            COUNT(*) AS total_jobs,
            SUM(is_junior) AS junior_jobs,
            ROUND(100.0 * SUM(is_junior) / COUNT(*), 1) AS junior_share_pct
        FROM jobs
        GROUP BY role_group
        ORDER BY junior_share_pct DESC;
    """
    return pd.read_sql(sql, engine)


def top_cities(engine: Engine, min_jobs: int = 2, limit: int = 10) -> pd.DataFrame:
    """Q5: Top Städte mit Rollen-Diversität."""
    sql = """
        SELECT
            job_city,
            COUNT(*) AS jobs_count,
            COUNT(DISTINCT role_group) AS unique_roles,
            COUNT(DISTINCT employer_name) AS unique_employers
        FROM jobs
        WHERE job_city <> 'Unbekannt'
        GROUP BY job_city
        HAVING COUNT(*) >= %(min_jobs)s
        ORDER BY jobs_count DESC, unique_roles DESC
        LIMIT %(limit)s;
    """
    return pd.read_sql(sql, engine, params={"min_jobs": min_jobs, "limit": limit})


def top_junior_employers(engine: Engine, limit: int = 10) -> pd.DataFrame:
    """Q6: Top Arbeitgeber mit Junior-Stellen."""
    sql = """
        SELECT
            employer_name,
            COUNT(*) AS junior_jobs_count,
            STRING_AGG(DISTINCT role_group, ', ') AS roles_offered
        FROM jobs
        WHERE is_junior = 1
          AND employer_name IS NOT NULL
          AND employer_name <> ''
        GROUP BY employer_name
        ORDER BY junior_jobs_count DESC
        LIMIT %(limit)s;
    """
    return pd.read_sql(sql, engine, params={"limit": limit})


def skill_gap_junior_senior(engine: Engine, min_mentions: int = 3) -> pd.DataFrame:
    """Q7: Skill-Lücke zwischen Junior und Senior."""
    sql = """
        SELECT
            s.skill_name,
            SUM(CASE WHEN j.is_junior = 1 THEN 1 ELSE 0 END) AS junior_mentions,
            SUM(CASE WHEN j.is_junior = 0 THEN 1 ELSE 0 END) AS senior_mentions,
            COUNT(*) AS total_mentions,
            ROUND(
                100.0 * SUM(CASE WHEN j.is_junior = 1 THEN 1 ELSE 0 END) / COUNT(*),
                1
            ) AS junior_share_pct
        FROM jobs j
        JOIN job_skills js ON j.job_id  = js.job_id
        JOIN skills      s ON js.skill_id = s.skill_id
        GROUP BY s.skill_name
        HAVING COUNT(*) >= %(min_mentions)s
        ORDER BY junior_share_pct ASC;
    """
    return pd.read_sql(sql, engine, params={"min_mentions": min_mentions})


def remote_quota_per_state(engine: Engine, min_jobs: int = 2) -> pd.DataFrame:
    """Q8: Remote-Quote pro Bundesland."""
    sql = """
        SELECT
            job_state,
            COUNT(*) AS total_jobs,
            SUM(CASE WHEN remote_type IN ('Remote', 'Hybrid') THEN 1 ELSE 0 END)
                AS remote_or_hybrid_jobs,
            ROUND(
                100.0 * SUM(CASE WHEN remote_type IN ('Remote', 'Hybrid') THEN 1 ELSE 0 END)
                / COUNT(*),
                1
            ) AS remote_quota_pct
        FROM jobs
        WHERE job_state <> 'Unbekannt'
        GROUP BY job_state
        HAVING COUNT(*) >= %(min_jobs)s
        ORDER BY remote_quota_pct DESC;
    """
    return pd.read_sql(sql, engine, params={"min_jobs": min_jobs})


def salary_stats_per_role(engine: Engine) -> pd.DataFrame:
    """Q9: Gehalts-Statistik pro Rolle."""
    sql = """
        SELECT
            role_group,
            COUNT(*) FILTER (WHERE salary_avg IS NOT NULL) AS jobs_with_salary,
            ROUND(AVG(salary_avg)::numeric, 0) AS avg_salary,
            ROUND(MIN(salary_avg)::numeric, 0) AS min_salary,
            ROUND(MAX(salary_avg)::numeric, 0) AS max_salary
        FROM jobs
        WHERE salary_avg IS NOT NULL
        GROUP BY role_group
        ORDER BY avg_salary DESC NULLS LAST;
    """
    return pd.read_sql(sql, engine)


def avg_skills_per_job_by_role(engine: Engine) -> pd.DataFrame:
    """Q10: Durchschnittliche Skill-Anzahl pro Job pro Rolle."""
    sql = """
        WITH skill_counts_per_job AS (
            SELECT
                j.job_id,
                j.role_group,
                COUNT(js.skill_id) AS skills_count
            FROM jobs j
            LEFT JOIN job_skills js ON j.job_id = js.job_id
            GROUP BY j.job_id, j.role_group
        )
        SELECT
            role_group,
            COUNT(*) AS jobs,
            ROUND(AVG(skills_count)::numeric, 1) AS avg_skills_per_job,
            MAX(skills_count) AS max_skills_per_job
        FROM skill_counts_per_job
        GROUP BY role_group
        ORDER BY avg_skills_per_job DESC;
    """
    return pd.read_sql(sql, engine)


# ============================================================================
# Convenience: Alle Queries im Überblick
# ============================================================================

ALL_QUERIES = {
    "Q1: Top Skills": top_skills,
    "Q2: Top Skills pro Rolle": top_skills_per_role,
    "Q3: Jobs pro Rolle/Arbeitsform": jobs_per_role_remote,
    "Q4: Junior-Anteil pro Rolle": junior_share_per_role,
    "Q5: Top Städte": top_cities,
    "Q6: Top Junior-Arbeitgeber": top_junior_employers,
    "Q7: Skill-Lücke Junior/Senior": skill_gap_junior_senior,
    "Q8: Remote-Quote pro Bundesland": remote_quota_per_state,
    "Q9: Gehalt pro Rolle": salary_stats_per_role,
    "Q10: Ø Skills pro Job": avg_skills_per_job_by_role,
}
