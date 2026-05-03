-- ============================================================================
-- Analyse-Queries für den Data Job Market Analyzer
-- ============================================================================
-- Zielsystem: PostgreSQL 13+
--
-- Diese Queries beantworten typische Fragen, die das Streamlit-Dashboard
-- visualisiert. Sie zeigen verschiedene SQL-Techniken:
--   - Joins (INNER, LEFT)
--   - Aggregationen (GROUP BY, HAVING)
--   - Window Functions (ROW_NUMBER, RANK)
--   - CTEs (WITH)
--   - CASE-Logik
--   - Subqueries
-- ============================================================================


-- ----------------------------------------------------------------------------
-- Q1: Top 10 Skills insgesamt
-- ----------------------------------------------------------------------------
SELECT
    s.skill_name,
    COUNT(*) AS mention_count
FROM job_skills js
JOIN skills s ON js.skill_id = s.skill_id
GROUP BY s.skill_name
ORDER BY mention_count DESC
LIMIT 10;


-- ----------------------------------------------------------------------------
-- Q2: Top 5 Skills pro Rolle (Window Function)
-- Ranking innerhalb einer Rolle nach Häufigkeit
-- ----------------------------------------------------------------------------
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
WHERE rank <= 5
ORDER BY role_group, cnt DESC;


-- ----------------------------------------------------------------------------
-- Q3: Anzahl Jobs pro Rolle und Arbeitsform
-- ----------------------------------------------------------------------------
SELECT
    role_group,
    remote_type,
    COUNT(*) AS jobs_count
FROM jobs
GROUP BY role_group, remote_type
ORDER BY role_group, jobs_count DESC;


-- ----------------------------------------------------------------------------
-- Q4: Junior-Anteil pro Rolle
-- Wie hoch ist der Anteil an Junior-Stellen für jede Rolle?
-- ----------------------------------------------------------------------------
SELECT
    role_group,
    COUNT(*) AS total_jobs,
    SUM(is_junior) AS junior_jobs,
    ROUND(100.0 * SUM(is_junior) / COUNT(*), 1) AS junior_share_pct
FROM jobs
GROUP BY role_group
ORDER BY junior_share_pct DESC;


-- ----------------------------------------------------------------------------
-- Q5: Top 10 Städte mit Rollen-Diversität
-- Welche Städte haben die meisten unterschiedlichen Rollen?
-- ----------------------------------------------------------------------------
SELECT
    job_city,
    COUNT(*) AS jobs_count,
    COUNT(DISTINCT role_group) AS unique_roles,
    COUNT(DISTINCT employer_name) AS unique_employers
FROM jobs
WHERE job_city <> 'Unbekannt'
GROUP BY job_city
HAVING COUNT(*) >= 2
ORDER BY jobs_count DESC, unique_roles DESC
LIMIT 10;


-- ----------------------------------------------------------------------------
-- Q6: Top Arbeitgeber mit Junior-Stellen
-- Wer stellt Berufseinsteiger ein?
-- ----------------------------------------------------------------------------
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
LIMIT 10;


-- ----------------------------------------------------------------------------
-- Q7: Skills-Lücke Junior vs Senior
-- Welche Skills werden bei Senior-Stellen häufiger gefordert als bei Juniors?
-- (Skills, die den Karrierepfad beschreiben)
-- ----------------------------------------------------------------------------
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
HAVING COUNT(*) >= 3
ORDER BY junior_share_pct ASC;


-- ----------------------------------------------------------------------------
-- Q8: Remote-Quote pro Bundesland
-- ----------------------------------------------------------------------------
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
HAVING COUNT(*) >= 2
ORDER BY remote_quota_pct DESC;


-- ----------------------------------------------------------------------------
-- Q9: Gehalts-Statistik pro Rolle (sofern Daten vorhanden)
-- ----------------------------------------------------------------------------
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


-- ----------------------------------------------------------------------------
-- Q10: Average Skills pro Job
-- Wie viele Skills werden pro Stelle im Durchschnitt erwähnt?
-- Aufgeteilt nach Rolle.
-- ----------------------------------------------------------------------------
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
