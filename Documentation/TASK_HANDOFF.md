# Task Handoff: Implement Structured Job Data Parsing

## 1. Objective
Update the job submission service (`/api/jobs/submit`) to have the AI model parse new structured data fields from job descriptions and save them to the `jobs` table.

## 2. Acceptance Criteria
- When a new job is submitted, the AI prompt in `job_service.py` must be updated to request the new structured fields.
- The backend logic must correctly extract these new fields from the AI's JSON response.
- The `INSERT` statement for the `jobs` table must be updated to include the new data for `salary_min`, `salary_max`, `required_experience_years`, `job_modality`, and `deduced_job_level`.
- The process must handle cases where the AI cannot find a value for a field (i.e., it should insert `NULL`).

## 3. Relevant Files to Modify
- `apps/backend/services/job_service.py`

## 4. Contextual Schema Information

### Database Migration that was just executed:
```sql
-- Step 1: Create the custom ENUM types for structured data
CREATE TYPE job_modality_enum AS ENUM ('On-site', 'Remote', 'Hybrid');
CREATE TYPE job_level_enum AS ENUM ('Entry', 'Mid', 'Senior', 'Staff', 'Principal', 'Manager', 'Director', 'VP', 'C-Suite');

-- Step 2: Alter the jobs table to add the new structured data columns
ALTER TABLE jobs ADD COLUMN salary_min INTEGER;
ALTER TABLE jobs ADD COLUMN salary_max INTEGER;
ALTER TABLE jobs ADD COLUMN required_experience_years INTEGER;
ALTER TABLE jobs ADD COLUMN job_modality job_modality_enum;
ALTER TABLE jobs ADD COLUMN deduced_job_level job_level_enum;

\d jobs table description:

Table "public.jobs"
        Column         |           Type           | Collation | Nullable |              Default
-----------------------+--------------------------+-----------+----------+-----------------------------------
 id                    | integer                  |           | not null | nextval('jobs_id_seq'::regclass)
 company_id            | integer                  |           | not null |
 company_name          | text                     |           |          |
 job_title             | text                     |           |          |
 job_url               | text                     |           | not null |
 status                | character varying(50)    |           |          | 'Active'::character varying
 source                | character varying(50)    |           |          | 'User Submission'::character varying
 last_checked_at       | timestamp with time zone |           |          | now()
 created_at            | timestamp with time zone |           |          | now()
 updated_at            | timestamp with time zone |           |          | now()
 salary_min            | integer                  |           |          |
 salary_max            | integer                  |           |          |
 required_experience_years | integer              |           |          |
 job_modality          | job_modality_enum        |           |          |
 deduced_job_level     | job_level_enum           |           |          |
Indexes:
    "jobs_pkey" PRIMARY KEY, btree (id)
    "jobs_job_url_key" UNIQUE CONSTRAINT, btree (job_url)
Foreign-key constraints:
    "jobs_company_id_fkey" FOREIGN KEY (company_id) REFERENCES companies(id)