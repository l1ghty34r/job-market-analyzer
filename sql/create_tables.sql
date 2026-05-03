-- ============================================================================
-- Schema für Data Job Market Analyzer
-- ============================================================================
-- Zielsystem: PostgreSQL 13+
--
-- Designprinzipien:
--   - Eine zentrale jobs-Tabelle (Fakten zur Stellenanzeige)
--   - Eine skills-Tabelle (Lookup für eindeutige Skills)
--   - Eine job_skills-Bridge (m:n zwischen jobs und skills)
--   - Indizes auf häufig gefilterte Spalten (role_group, job_city, is_junior)
--
-- Ausführung:
--   psql -U <user> -d <db> -f sql/create_tables.sql
-- ============================================================================

DROP TABLE IF EXISTS job_skills CASCADE;
DROP TABLE IF EXISTS skills CASCADE;
DROP TABLE IF EXISTS jobs CASCADE;


-- Haupttabelle: eine Zeile pro Stellenanzeige
CREATE TABLE jobs (
    job_id              VARCHAR(255) PRIMARY KEY,
    job_title           TEXT,
    employer_name       TEXT,
    job_employment_type VARCHAR(100),
    job_apply_link      TEXT,
    job_description     TEXT,
    job_is_remote       BOOLEAN,
    job_posted_at       VARCHAR(100),
    job_posted_at_utc   TIMESTAMP,
    job_location        TEXT,
    job_city            VARCHAR(255),
    job_state           VARCHAR(255),
    job_country         VARCHAR(50),
    salary_min          NUMERIC(10, 2),
    salary_max          NUMERIC(10, 2),
    salary_avg          NUMERIC(10, 2),
    salary_period       VARCHAR(50),
    search_term         VARCHAR(100),
    is_junior           SMALLINT NOT NULL DEFAULT 0 CHECK (is_junior IN (0, 1)),
    remote_type         VARCHAR(50),
    role_group          VARCHAR(50),
    inserted_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Skill-Lookup: eine Zeile pro eindeutigem Skill
CREATE TABLE skills (
    skill_id   SERIAL PRIMARY KEY,
    skill_name VARCHAR(100) UNIQUE NOT NULL
);

-- Bridge-Tabelle: m:n zwischen jobs und skills
CREATE TABLE job_skills (
    job_id   VARCHAR(255) NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    skill_id INTEGER     NOT NULL REFERENCES skills(skill_id) ON DELETE CASCADE,
    PRIMARY KEY (job_id, skill_id)
);


-- Indizes für häufige Filter
CREATE INDEX idx_jobs_role_group   ON jobs(role_group);
CREATE INDEX idx_jobs_city         ON jobs(job_city);
CREATE INDEX idx_jobs_state        ON jobs(job_state);
CREATE INDEX idx_jobs_remote_type  ON jobs(remote_type);
CREATE INDEX idx_jobs_is_junior    ON jobs(is_junior);
CREATE INDEX idx_jobs_employer     ON jobs(employer_name);
CREATE INDEX idx_jobs_posted       ON jobs(job_posted_at_utc);

CREATE INDEX idx_jobskills_skill   ON job_skills(skill_id);


-- Praktische Views für häufige Joins
CREATE OR REPLACE VIEW v_jobs_with_skills AS
SELECT
    j.job_id,
    j.job_title,
    j.employer_name,
    j.job_city,
    j.job_state,
    j.role_group,
    j.remote_type,
    j.is_junior,
    j.salary_avg,
    s.skill_name
FROM jobs j
LEFT JOIN job_skills js ON j.job_id  = js.job_id
LEFT JOIN skills      s ON js.skill_id = s.skill_id;


COMMENT ON TABLE jobs       IS 'Bereinigte Stellenanzeigen aus der JSearch API';
COMMENT ON TABLE skills     IS 'Eindeutige technische Skills (Lookup)';
COMMENT ON TABLE job_skills IS 'm:n-Verbindung zwischen jobs und skills';
COMMENT ON VIEW  v_jobs_with_skills IS 'Joined Jobs + Skills, eine Zeile pro Job-Skill-Paar';
