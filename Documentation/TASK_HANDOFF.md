# Task Handoff: Implement V1 Job Matching & Recommendations

## Epic 1: Structured User Profile Data
### Objective
Update the user profile page and backend services to use structured integer fields for salary preferences, eliminating free-text parsing.

### Task 1.1: Update Frontend Profile Page UI
*   **Acceptance Criteria:**
    *   In `apps/frontend/app/dashboard/profile/page.tsx`, replace the single `<Input>` for "Desired Annual Compensation" with two `<Input type="number">` components: "Desired Minimum Salary" (`desired_salary_min`) and "Desired Maximum Salary" (`desired_salary_max`).
    *   The `handleChange` function must be updated to handle the new integer fields.
    *   The form submission must correctly send `desired_salary_min` and `desired_salary_max` to the backend.
*   **Relevant Files:** `apps/frontend/app/dashboard/profile/page.tsx`, `apps/frontend/app/dashboard/types.ts`.

### Contextual Schema: `user_profiles`
---
-- The 'desired_annual_compensation' TEXT column has been DROPPED.
-- New columns have been ADDED:
ALTER TABLE user_profiles ADD COLUMN desired_salary_min INTEGER;
ALTER TABLE user_profiles ADD COLUMN desired_salary_max INTEGER;
---
## Epic 2: Structured Job Data & V1 Matching Engine
### Objective
Enhance the backend to parse structured data from job descriptions and create a V1 job recommendation service.

### Task 2.1: Update AI Prompt for Structured Job Data
*   **Acceptance Criteria:**
    *   The AI prompt in `job_service.py` must be updated to request the new structured fields from job descriptions.
    *   The backend logic must correctly extract `salary_min`, `salary_max`, `required_experience_years`, `job_modality`, and `deduced_job_level` from the AI's response.
    *   The `INSERT` statement for the `jobs` table must be updated to save this new data.
*   **Relevant Files:** `apps/backend/services/job_service.py`.

### Task 2.2: Implement V1 JobMatchingService
*   **Acceptance Criteria:**
    *   A new file `apps/backend/services/job_matching_service.py` is created.
    *   A new file `apps/backend/routes/recommendations.py` is created with a `GET /api/jobs/recommendations` endpoint.
    *   The service implements the V1 Matching Algorithm (Base AI Grade + Bonuses/Penalties for Modality, Salary, and Leadership).
    *   The service correctly returns a ranked list of job recommendations.
*   **Relevant Files:** `apps/backend/services/job_matching_service.py`, `apps/backend/routes/recommendations.py`, `apps/backend/app.py`.

### Contextual Schema: `jobs`
---
-- New columns have been ADDED:
ALTER TABLE jobs ADD COLUMN salary_min INTEGER;
ALTER TABLE jobs ADD COLUMN salary_max INTEGER;
ALTER TABLE jobs ADD COLUMN required_experience_years INTEGER;
ALTER TABLE jobs ADD COLUMN job_modality job_modality_enum; -- ('On-site', 'Remote', 'Hybrid')
ALTER TABLE jobs ADD COLUMN deduced_job_level job_level_enum; -- ('Entry', ..., 'C-Suite')
---