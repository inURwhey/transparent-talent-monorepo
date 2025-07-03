--- START OF FILE CHANGELOG.md ---
# Transparent Talent - Changelog

All notable changes to this project will be documented in this file.

## v0.51.0 - 2025-07-04 - Data Integrity: ENUMs for User Preferences

This release significantly enhances data integrity and prepares the system for more accurate relevancy calculations by migrating key user profile preference fields to PostgreSQL ENUM types. It includes full-stack implementation to ensure seamless display and persistence of these structured preferences.

### Added
-   **Database:** New PostgreSQL `ENUM` types: `company_size_enum`, `work_style_type_enum`, `conflict_resolution_enum`, `communication_pref_enum`, `change_tolerance_enum`, and `work_location_enum`.
-   **Database:** Explicit `NO_PREFERENCE` option added to all new ENUM types, enabling clear distinction from `NULL` (unset) values.
-   **Backend:** New `COMPANY_SIZE_MAPPING`, `WORK_STYLE_MAPPING`, `CONFLICT_RESOLUTION_MAPPING`, `COMMUNICATION_PREFERENCE_MAPPING`, `CHANGE_TOLERANCE_MAPPING`, and `WORK_LOCATION_MAPPING` in `ProfileService` for consistent ENUM value management.
-   **Frontend:** New explicit option arrays (`companySizeOptions`, `workStyleOptions`, etc.) for `Select` components on the User Profile page, improving maintainability and ensuring consistent option lists.

### Changed
-   **Database Schema:** Migrated `user_profiles` columns (`preferred_company_size`, `work_style_preference`, `conflict_resolution_style`, `communication_preference`, `change_tolerance`, `preferred_work_style`) from `TEXT`/`VARCHAR` to their respective new `ENUM` types.
-   **Backend (`ProfileService`):**
    *   Updated `allowed_fields` to reflect ENUM types.
    *   Enhanced `_map_db_to_display` and `_map_display_to_db` helpers to handle all newly converted ENUMs, ensuring bidirectional mapping between database short codes (e.g., `STARTUP`) and frontend display strings (e.g., `Startup (1-50 employees)`).
    *   Modified `get_profile_for_analysis` to use raw ENUM values for AI prompts while still formatting other fields.
-   **Frontend (`UserProfilePage`):**
    *   Updated `Select` components to bind `value` prop to `profile.fieldName ?? ''` ensuring correct behavior with `null` values and placeholders.
    *   Refined `handleChange` logic to consistently interpret `Select` input values, correctly mapping "No Preference" strings to their explicit values, and empty strings/`"null"` to `null` for backend submission.
    *   Adjusted `SelectValue` rendering for `preferred_company_size` and `preferred_work_style` to explicitly display "No Preference" in black text when it's selected.
-   **Frontend (`types.ts`):** Broadened type definitions for ENUM-backed fields (e.g., `preferred_work_style`) from strict literal unions to `string | null` to accommodate all valid display strings.

### Fixed
-   **Database Migration Error:** Resolved `invalid input value for enum` errors during database migration by implementing explicit `CASE WHEN` statements to map existing long-form `TEXT` values to new short-code `ENUM` values.
-   **TypeScript Compilation Error:** Fixed `TS2367` by updating `Profile` interface types, allowing frontend to correctly handle new ENUM string values.
-   **UI Display & Persistence Bugs:** Addressed issues where ENUM values (especially "No Preference") were not correctly displaying after save, appearing as grey placeholders instead of selected black text, or failing to persist.


## v0.50.0 - 2025-07-03 - CRM Reminders & Notes (Backend & Core Frontend)

This release implements the foundational CRM-like functionality for tracked jobs, allowing users to add "Next Action Date" and "Next Action Notes." It also includes critical bug fixes and architectural refinements across the frontend.

### Added
- **Feature: User-set Reminders & Next Action Notifications:** Implemented backend support for `next_action_at` (date) and `next_action_notes` (text) fields on `tracked_jobs`, enabling users to record future actions and reminders for job applications.
- **Frontend UI:** Added new interactive columns for "Next Action Date" (with date picker) and "Next Action Notes" (with textarea) to the "My Job Tracker" table.

### Changed
- **Backend:** Enhanced `TrackedJobService` to accept and persist updates for `next_action_at` and `next_action_notes`.
- **Frontend Data Model:** Updated `TrackedJob` interface in `types.ts` to reflect the `notes` column (instead of `user_notes`) and include new CRM fields.
- **Frontend Architecture:** Refactored `columns.tsx` to include interactive date pickers and text areas for new CRM fields.
- **Frontend Architecture:** Unified the update mechanism by passing a generic `handleUpdateJobField` function from `page.tsx` down to `JobTracker.tsx` and `columns.tsx`, enabling flexible updates to any modifiable tracked job field.
- **Frontend UX:** Modified `handleJobSubmit` in `page.tsx` to trigger a refetch of relevant data (tracked jobs and recommendations) instead of a full page reload after a new job submission, providing a smoother user experience.
- **Frontend Components:** Integrated Shadcn UI `Calendar` and `Popover` components for the date picker functionality.
- **Frontend Components:** Implemented `useState` and `onBlur` with `defaultValue` for `Textarea` to manage the "Next Action Notes" input.

### Fixed
- **Bugfix (Frontend UI):** Corrected the mapping for the `notes` column in `tracked_job_service.py` and `types.ts` to ensure existing user notes are correctly displayed.
- **Bugfix (Frontend Types):** Resolved TypeScript error `TS2322` by aligning async/sync return types and parameter types for `handleUpdateJobField` across frontend components (`page.tsx`, `JobTracker.tsx`, `columns.tsx`).
- **Bugfix (Frontend Imports):** Resolved TypeScript error `TS2307` by correcting the import path for `useTrackedJobsApi` in `page.tsx`.
- **Bugfix (Frontend Hook):** Resolved TypeScript error `TS2339` by explicitly exposing the `refetch` function from `useTrackedJobsApi`.

### Known Issues
- **UI Update Delay:** The "Next Action Date" and "Next Action Notes" fields do not visually update immediately after changes are saved, despite the backend successfully persisting the data and the frontend refetching it. The changes only become visible upon a manual page refresh. This is currently being investigated as a complex `react-table` rendering/memoization issue.

## v0.49.0 - 2025-07-03 - Company Profile V1 & Dashboard Refactor

This release completes the V1 of the Company Profile feature by adding a user-facing UI to display AI-generated company data. To support this, the entire dashboard frontend has been refactored into a more stable and modular architecture, resolving numerous bugs and improving future development velocity.

### Added
- **Feature: Company Profile Snapshot UI:** Users can now expand a tracked job row in the "My Job Tracker" table to view a snapshot of the company's profile, including its industry, size, mission, and business model. This makes the "Environment Fit" analysis transparent to the user.
- **Backend API:** A new endpoint `GET /api/companies/<int:company_id>/profile` was added to serve the company profile data to the frontend.

### Changed
- **Architecture (Frontend):** The main dashboard page (`page.tsx`) and its related components (`columns.tsx`, `data-table.tsx`) have been significantly refactored. Logic is now encapsulated in new, single-responsibility components like `JobTracker.tsx` and `CompanyProfileCard.tsx`, improving maintainability and fixing a cascade of state management bugs.
- **Backend:** The `tracked_job_service.py` now correctly includes the `company_id` in the data payload for the job tracker, enabling the frontend to fetch the correct profile.

### Fixed
- **Critical Frontend Bug:** Fixed a persistent bug where the Company Snapshot card would either not load data or get stuck in an infinite loading loop due to complex `useEffect` dependency issues.
- **Backend Data Bug:** Fixed a bug in `tracked_job_service.py` where a query for a non-existent `user_notes` column caused the main job tracker API to fail.

## v0.48.0 - 2025-07-02 - Automated Company Data Enrichment

This release implements a significant backend feature that automatically researches and enriches company data, directly improving the core job relevancy engine. It also includes several critical bugfixes related to data integrity and edge case handling in the job submission process.

### Added
- **Feature: Automated Company Research:** The system now automatically triggers AI-driven research to create a `company_profile` the first time a job from a new company is submitted. This process is fully automated and runs for all users, enriching the platform's core dataset.
- **AI Context:** The main job analysis prompt is now enhanced with the data from `company_profiles` (industry, mission, etc.), providing crucial context for a more accurate "Environment Fit" score.

### Changed
- **Architecture:** The job submission workflow in `routes/jobs.py` has been refactored to be a single, atomic transaction, preventing partial data writes.
- **Architecture:** The "re-track job" functionality now correctly triggers a new analysis for an onboarded user if one doesn't already exist for them, ensuring a consistent user experience.

### Fixed
- **Critical Bug (Data Loss):** Fixed a bug where a premature `db.commit()` in the job submission route would break the transaction and cause the `company_profile` data to be silently lost.
- **Critical Bug (Server Crash):** Resolved a `TypeError: Object of type datetime is not JSON serializable` that crashed the job submission endpoint.
- **Critical Bug (SQL Error):** Corrected a SQL query that attempted to select a non-existent `id` column from the `job_analyses` table during the re-tracking process.

### Protocols
- **Added "Proactive Refactoring Suggestion":** The AI will now suggest refactoring overly large or complex files before modification.
- **Updated "Database Interaction Protocol":** Added a "Known Schema Quirks" section to explicitly document the primary key of the `job_analyses` table.

## v0.47.0 - 2025-07-03 - Profile Page UX Polish

This release implements several small but high-impact UX refinements on the user profile page, improving interactivity and creating a more intuitive layout.

### Changed
- **UI/UX:** "No Preference" is now a persistent, selectable state for dropdowns on the profile page, preventing the UI from incorrectly reverting to a placeholder.
- **UI/UX:** The "remote preference" checkbox is now correctly shown only when "Hybrid" is selected as the preferred work location.
- **UI/UX:** Co-located the "Save Profile" and "Back to Dashboard" buttons at the bottom of the profile form and moved feedback messages closer to the user's point of action.

### Fixed
- **UI/UX:** Resolved multiple TypeScript errors and UI state inconsistencies related to dropdown components on the profile page.

## v0.46.0 - 2025-07-03 - Dashboard & Profile UX Refactor

This release implements significant UX and layout improvements based on user feedback, creating a more intuitive and consistent experience.

### Changed
- **UI/UX:** Relocated the "Update Your Resume" form from the main dashboard to the `/dashboard/profile` page, logically grouping all profile-editing actions together.
- **UI/UX:** Refactored the "Analyze a New Job" form on the dashboard. The layout now matches the resume form, with the primary action button below the input field.
- **UI/UX:** Added dynamic, context-aware descriptive text to the job submission form to better explain its function ("Track" vs. "Analyze") based on the user's onboarding status.

### Added
- **Backlog:** Added "Create `STYLE_GUIDE.md`" to the backlog to codify recurring design patterns and UI/UX decisions.

## v0.45.0 - 2025-07-02 - Profile UX Refinement

This release implements a high-value UX improvement on the user profile page based on its RICE score.

### Changed
- **UI/UX:** Updated the "Desired Job Title" field to "Desired Job Title(s)" on the user profile page, including the label and placeholder text, to better reflect that users may be targeting multiple roles.

## v0.44.0 - 2025-07-02 - UX Refinements & Final Onboarding Fixes

This release completes the stabilization of the new user experience by refining UI interactions and resolving the final bug in the onboarding data lifecycle. The application is now fully stable with a robust and intuitive user flow.

### Added
- **Backlog:** Added new architectural epics to define User, Company, and Job lifecycles to parallel the existing Data Lifecycle documentation.

### Changed
- **UI/UX:** The main job submission button on the dashboard is now context-aware. It displays "Track" for users with incomplete profiles and "Analyze" for users who have completed onboarding, setting clear expectations.
- **UI/UX:** Refined the "Required Fields" indicators on the profile page to be more subtle and align with standard web conventions.

### Fixed
- **Critical Bug (Data Loss):** Resolved the final bug in the onboarding flow where parsing a resume could overwrite previously user-entered data. The backend now performs a true "enrich-if-empty" merge, preserving user data as the source of truth.

## v0.43.0 - 2025-07-02 - Onboarding Lifecycle Hardening & Stability
This release resolves a series of critical, interconnected bugs that affected the entire new user onboarding and job submission lifecycle. The application is now fully stable, and the logic for completing a user profile and triggering AI analysis is robust, resilient, and non-destructive.

### Added
- **Backend: Centralized Onboarding Logic:** Created a new, centralized service method (`check_and_trigger_onboarding_completion`) to reliably check user onboarding status from multiple endpoints.
- **Backend: Non-Destructive Resume Parsing:** Implemented "merge, don't overwrite" logic in the resume parsing endpoint. The AI now only fills profile fields that are empty, preserving user-entered data as the source of truth.

### Changed
- **Architecture:** The definition of a "complete" user profile now correctly requires both a set of required text fields and an active resume submission.
- **Architecture:** The user's manually entered data is now formally treated as the "source of truth," with AI parsing acting as a non-destructive enrichment step.
- **UI/UX:** Refined the profile page to use subtle `*` indicators for required fields and a single, clear instructional banner for a cleaner user experience.

### Fixed
- **Critical Bug (Deployment):** Resolved a fatal circular import error between services that was preventing all backend deployments.
- **Critical Bug (Data Integrity):** Fixed a `duplicate key value` database error that occurred when multiple incomplete users submitted jobs from the same company.
- **Critical Bug (Data Loss):** Corrected the resume parsing logic to prevent it from overwriting existing, user-entered profile data with `null` values.
- **Critical Bug (Stale UI):** Resolved the issue where "Unlock w/ Profile" would not update after a user completed all onboarding steps. The re-analysis trigger and frontend reload now work correctly.
- **Critical Bug (SQL):** Fixed a `column a.id does not exist` SQL error in the `trigger_reanalysis_for_user` service method.

## v0.42.0 - 2025-07-03 - Full-Stack Bug Bash & "Jobs For You" v1

This release marks a significant stabilization and feature implementation effort. It resolves a complex series of interconnected bugs across the frontend and backend, and successfully launches the V1 of the "Jobs For You" recommendation module on the user dashboard.

### Added
-   **Feature: "Jobs For You" Frontend Module:** Implemented the full frontend for the job recommendation module. This includes a new `useJobRecommendationsApi` hook for data fetching, a `JobsForYou.tsx` presentational component, and integration into the main dashboard page.
-   **Feature: Conditional AI Gating:** The backend now intelligently gates AI analysis. Jobs submitted by users with incomplete profiles are tracked immediately, but the AI analysis is deferred until the profile is completed, at which point a new re-analysis process is automatically triggered.
-   **Feature: Re-tracking Jobs:** Users can now re-track jobs they have previously deleted. The backend logic now correctly handles this edge case without causing a database conflict.
-   **Backend: Data Integrity Validation:** Added robust post-parsing validation in `job_service.py` to ensure `job_title` and `company_name` are always present and valid after AI processing, preventing silent data corruption.
-   **Protocols:** Added the `Self-Correction on Truncation` protocol to force the AI to prevent providing truncated code.

### Changed
-   **Backend:** Refactored all Flask blueprint routing to be consistent, resolving a major CORS/404 regression bug.
-   **Backend:** The `JobMatchingService` now includes the `matrix_rating` (letter grade) in its API response to ensure UI consistency.
-   **UI/UX:** The "Jobs For You" module now displays a clear "Complete Your Profile" call-to-action for users with incomplete profiles, instead of an empty state.
-   **UI/UX:** The "AI Grade" in the "My Job Tracker" table now displays an "Unlock" CTA for jobs tracked before profile completion.
-   **UI/UX:** The user is now redirected to the dashboard after saving their profile to ensure all page data is correctly synchronized and refetched.

### Fixed
-   **Critical Bug (Dashboard Inaccessible):** Resolved a CORS and 404 error that was blocking all API calls and making the dashboard unusable.
-   **Critical Bug (Data Integrity):** Fixed a database constraint violation that occurred when multiple incomplete users submitted jobs, by implementing a lightweight scrape for basic job details.
-   **Stale UI Data:** Fixed the bug where the "Jobs For You" module and the "AI Grade" CTA would not update after a user tracked a job or completed their profile.

## v0.41.0 - 2025-07-03 - Frontend Bugfixes & UX Polish

This release addresses several bugs and user experience issues identified after the initial launch of the "Jobs For You" recommendation module, and refines the core application routing.

### Changed
-   **Backend Routes:** Refactored all Flask Blueprints to have their `url_prefix` defined centrally in `app.py`. This resolves a series of `404` errors and subsequent CORS failures that were making the dashboard inaccessible.
-   **Onboarding Flow:** The dashboard page (`page.tsx`) no longer redirects incomplete users. Instead, it loads and conditionally renders CTAs, providing a better user context.
-   **Job Submission Logic:** The backend (`jobs.py`) now gates AI analysis. Jobs submitted by users with incomplete profiles are tracked, but a `job_analyses` record is not created, providing an incentive to complete the profile.

### Fixed
-   **Critical Bug (CORS/404):** Resolved a major regression bug that was blocking all API calls from the frontend due to incorrect blueprint registration and failed CORS preflight checks.
-   **"Jobs For You" State:** The recommendation module now correctly refetches its data after a user tracks a job, ensuring the list stays up-to-date without a manual refresh.
-   **Profile Completion CTA:** The logic for displaying the "Complete Your Profile" CTA in the "Jobs For You" module and the "Unlock AI Grade" CTA in the tracker table is now fully functional.

## v0.40.0 - 2025-07-03 - "Jobs For You" Frontend Architecture

This release completes the architectural design for the frontend module that will display job recommendations to the user. This work creates a clear, component-based implementation plan.

### Added
-   **Architecture:** Designed the frontend architecture for the "Jobs For You" module, including a new `useJobRecommendationsApi` custom hook for data fetching and a `JobsForYou.tsx` presentational component.
-   **Protocols:** Updated the `TASK_HANDOFF.md` document to include this new frontend epic, providing skeletal code and type definitions to guide implementation.

## v0.39.0 - 2025-07-03 - V1 Job Matching Service Implemented

This release introduces the core backend service for generating personalized job recommendations. This service provides the API foundation for the upcoming "Jobs For You" dashboard module.

### Added
-   **`services/job_matching_service.py`:** A new service containing the V1 matching algorithm. The algorithm calculates a `match_score` for each job based on the AI-generated `matrix_rating` and applies bonuses/penalties based on structured data alignment (work modality, salary range, leadership tier gap).
-   **`routes/recommendations.py`:** A new Flask Blueprint defining the `GET /api/jobs/recommendations` endpoint, which exposes the `JobMatchingService` to the frontend.

### Changed
-   **`app.py`:** The main application factory was updated to register the new recommendations blueprint, activating the `/api/jobs/recommendations` route.

## v0.38.0 - 2025-07-03 - Structured Job Data Parsing Implemented

This release enhances the backend's ability to ingest rich, structured data from job descriptions, a crucial step for building advanced job recommendation features.

### Added
-   **Backend:** Implemented parsing and storage of new structured job data fields (`salary_min`, `salary_max`, `required_experience_years`, `job_modality`, `deduced_job_level`) from AI analysis into the `jobs` table.
-   **Backend:** Added robust validation helper methods (`_parse_and_validate_int`, `_validate_enum`) in `job_service.py` to ensure data integrity of AI-generated structured fields, casting to correct types or setting to `NULL` for invalid values.
-   **Protocols:** Introduced the `Test Plan Generation Protocol` to `PROTOCOLS.md`, mandating detailed test plans for all implemented features, including SQL validation queries.

### Changed
-   **Backend AI Prompt:** Updated the Gemini AI prompt within `job_service.py` to explicitly request the new structured job data fields in its JSON output schema.
-   **Backend Routes:** Modified the `jobs/submit` route in `jobs.py` to include the new structured data in its `INSERT` and `ON CONFLICT DO UPDATE SET` statements for the `jobs` table.

### Fixed
-   No bugs were addressed in this release; changes were feature-driven.

## v0.37.0 - 2025-07-03 - Structured User Profile Salary Fields

This release implements the frontend changes for structured user salary preferences, aligning the UI with the recently migrated backend data model.

### Added
-   **UI:** Updated the User Profile page (`/dashboard/profile`) to replace the single "Desired Annual Compensation" text input with two new input fields: "Desired Minimum Annual Salary" (`desired_salary_min`) and "Desired Maximum Annual Salary" (`desired_salary_max`).
-   **UI:** Implemented automatic formatting of salary numbers with commas for display (e.g., `150000` to `150,000`).
-   **UI:** Enabled parsing of user input to accept numbers with or without commas, converting them to clean integers for backend submission.

### Changed
-   **Frontend:** Modified the `handleChange` function in `profile/page.tsx` to correctly handle the new integer-based salary fields, including parsing formatted input and ensuring `null` values for empty fields.
-   **Frontend:** Changed the `type` attribute of the salary input fields from `number` to `text` to allow for custom formatting and comma input.

### Fixed
-   **UI:** Removed the `step` attribute from the salary input fields to allow free-form numerical entry.

## v0.36.0 - 2025-07-03 - Job Matching Architecture & Salary Data Model

This release completes the high-level architectural design for the "Jobs For You" recommendation engine and refactors the underlying user profile data model for improved robustness and scalability. This work deconstructs two major epics into a clear, sequenced set of implementation tasks.

### Added
-   **Architecture:** Designed the V1 architecture for a new `JobMatchingService` and a corresponding `GET /api/jobs/recommendations` endpoint. The service's V1 scoring algorithm will rank jobs based on a combination of AI analysis and new structured data fields.
-   **Protocols:** Formally added an **"Epic/Task"** structure to the backlog management protocol to improve clarity and tracking of large feature initiatives.

### Changed
-   **Database:** Re-architected the `user_profiles` table by replacing the `desired_annual_compensation` TEXT column with two new INTEGER columns: `desired_salary_min` and `desired_salary_max`. This change eliminates brittle text parsing and improves data integrity.

### Fixed
-   No bugs were addressed in this release; changes were purely architectural and preparatory.

## v0.35.0 - 2025-07-02 - Enhanced Job Data Architecture & Handoff Protocol

This release implements the foundational database architecture for the "Jobs For You" recommendation engine. By enhancing the `jobs` table with structured, queryable fields, this work unblocks future development of advanced job matching services. This release also codifies a new "Task Handoff" protocol to improve workflow efficiency between different AI models.

### Added
-   **Database:** Created new `ENUM` types (`job_modality_enum`, `job_level_enum`) to support structured job data.
-   **Database:** Enhanced the `jobs` table by adding new columns for structured data, including `salary_min`, `salary_max`, `required_experience_years`, `job_modality`, and `deduced_job_level`.
-   **Protocols:** Added a new "Task Handoff Protocol" to `PROTOCOLS.md` to formalize the creation of `TASK_HANDOFF.md` files, ensuring seamless context transfer from Pro to Flash development sessions.

### Changed
-   **Protocols:** Refined the AI Model classification system to include `Creative` and sub-types for `Pro` tasks (`Pro Breakdown`, `Pro Execute`) for more accurate project planning.

## v0.34.0 - 2025-07-02 - AI Content Validation & Enhanced Profile Parsing

This release introduces intelligent AI-driven content validation at the submission pipeline's entry points and significantly improves the robustness of user profile parsing, preventing data inconsistencies and optimizing AI resource usage.

### Added
-   **Backend AI:** Implemented a new AI content classification step for both resume and job submissions. A lightweight AI model now verifies if submitted text is a valid resume or job posting early in the pipeline (`job_service.py`, `onboarding.py`). If not, the submission is rejected, saving tokens on full AI processing.
-   **Backend:** Added explicit post-parsing validation for specific AI-generated profile fields (`preferred_work_style`, `personality_16_personalities`) in `onboarding.py`. If AI output for these fields does not match expected formats or allowed values, the data is discarded (set to `null`) rather than causing database errors.

### Changed
-   **Backend Config:** Increased `MAX_RESUME_TEXT_LENGTH` to `25,000` characters and `MAX_JOB_TEXT_LENGTH` to `50,000` characters in `config.py`. These initial ingestion limits are now more permissive, anticipating a future AI-driven content trimming step.
-   **Backend AI Prompt:** Refined the AI prompt for `personality_16_personalities` and `preferred_work_style` in `onboarding.py` to guide Gemini towards generating values strictly adhering to expected formats (e.g., standard Myers-Briggs types, 'On-site', 'Remote', 'Hybrid').

### Fixed
-   **Backend:** Resolved the `value too long for type character varying(50)` error that was preventing resume submissions, by implementing robust post-parsing validation and discard logic for `personality_16_personalities` and `preferred_work_style`.

## v0.33.0 - 2025-07-02 - Core Backend Stability & UI Polish

This release significantly enhances core application stability by resolving critical backend database errors and improving AI data processing. It also delivers key UI refinements for a more intuitive user experience.

### Added
-   **Backend:** Implemented AI input size validation. New configuration variables (`MAX_RESUME_TEXT_LENGTH`, `MAX_JOB_TEXT_LENGTH`) limit the character length of text inputs (resumes, job descriptions) sent to AI models, optimizing token usage and preventing costly large requests.

### Changed
-   **Backend AI:** Updated the AI prompt for `matrix_rating` within `job_service.py` to instruct Gemini to generate letter grades (e.g., A+, B-) based on relevance scores, aligning with the intended business logic and replacing the previous "Strong Yes" scale.
-   **Frontend UI:** Renamed the "Closed Pipeline" filter to "Inactive Applications" for improved clarity and user experience on the dashboard.
-   **Frontend UI:** Implemented semantic color-coding and bolding for tracked job statuses (e.g., green for `OFFER_ACCEPTED`, red for `REJECTED`/`EXPIRED`, blue for active statuses) directly within the "Status" column of the job tracker table for better visual communication.
-   **Frontend UI:** Modified the "Relevance" column to display the AI-generated `matrix_rating` (letter grade) instead of the raw numerical sum of scores, and renamed its header to "AI Grade" for better clarity.

### Fixed
-   **Database:** Resolved a critical `value too long for type character varying(2)` database error that was blocking job submissions. This was fixed by identifying the `job_analyses.matrix_rating` column and guiding the user to alter its type to `VARCHAR(50)`.

## v0.32.0 - 2025-07-02 - Resume Versioning & Profile Polish

This release introduces core backend functionality for managing user resume versions and finalizes critical frontend UI stability, ensuring a polished user profile experience.

### Added
-   **Backend:** Implemented resume versioning on submission (`/api/onboarding/parse-resume`). Each resume text submitted is now stored in the `resume_submissions` table, with the most recent submission automatically set as `is_active = TRUE`, and all previous submissions for that user set to `FALSE`.

### Changed
-   **Backend AI:** Updated the AI prompt for `matrix_rating` within `job_service.py` to guide Gemini into generating letter grades (e.g., A+, B-) based on relevance scores, ensuring conceptual alignment with business requirements.
-   **Frontend UI:** Renamed the "Closed Pipeline" filter to "Inactive Applications" for improved clarity and user experience.
-   **Frontend UI:** Implemented semantic color-coding and bolding for job statuses (e.g., green for accepted, red for rejected/expired, blue for active) directly within the "Status" column of the job tracker table.
-   **Frontend UI:** Modified the "Relevance" column to display the AI-generated `matrix_rating` (letter grade) instead of the raw numerical sum, and renamed its header to "AI Grade."

### Fixed
-   **Database:** Resolved `value too long for type character varying(2)` database error by identifying and guiding the user to alter the `job_analyses.matrix_rating` column to `VARCHAR(50)`, unblocking job submissions.
-   **Frontend:** Resolved all remaining display and interaction issues with dropdowns in the "Work Style & Preferences" section of the user profile, including correct value display and removal of "uncontrolled to controlled" React warnings. Contextual placeholder text for these fields is now correctly managed.

## v0.31.0 - 2025-07-02 - Profile Dropdown & UI Consistency Fixes

This release resolves persistent issues with dropdown menus on the user profile page, ensuring that saved values are correctly displayed and eliminating console warnings related to component control. It also restores contextual placeholder text for a more intuitive user experience.

### Fixed
-   **Bugfix: Dropdowns in Work Style section don't show selected value:** Addressed the issue where dropdowns (e.g., "I am most productive when...") were not correctly displaying saved profile values. Implemented consistent use of Shadcn UI's controlled `Select` component behavior by binding `value` to an empty string (`""`) for unselected states and correctly mapping backend short codes (e.g., 'High') to their full descriptive sentences for display, and vice versa for saving. This also resolved "uncontrolled to controlled" React warnings.

## v0.30.0 - 2025-07-02 - Profile Redirection Bugfix

This release addresses a critical bug in the user onboarding flow, ensuring that users with incomplete profiles are correctly guided to the initial setup page.

### Fixed
-   **Bugfix: Redirect empty profiles to /welcome:** Resolved an issue where users with incomplete profiles were redirected to `/dashboard/profile` instead of the intended `/welcome` page, ensuring proper onboarding flow.

## v0.29.0 - 2025-07-01 - Resume Versioning Architecture

This release lays the architectural groundwork for a robust resume versioning system. This work deconstructs a large, complex feature into smaller, manageable implementation tasks, enabling more efficient future development.

### Added
-   **Database:** Created a new `resume_submissions` table to store the full history of a user's resume submissions. The table includes columns for `raw_text`, `submitted_at`, `source`, and an `is_active` flag to identify the primary resume.
-   **Database:** Added indexes to the new table for efficient querying and a partial unique index to ensure only one resume can be active per user at a time.

### Changed
-   **Protocols:** Updated the `Session Budgeting Protocol` to include a "Retroactive Costing" step, using completed session data to refine future task estimates.

### Fixed
-   No bugs were addressed in this release; changes were purely architectural and preparatory.

## v0.28.0 - 2025-07-01 - Production Onboarding & Profile Stabilization

This release marks a major stabilization of the core user experience by resolving a series of cascading bugs in the authentication, onboarding, and profile management flows. The application is now fully functional on its production domain with a robust sign-up process.

### Fixed
-   **Critical Auth: New User Redirect & Backend Crash:** Fixed a complete failure of the new user sign-up flow. The multi-layered solution involved:
    -   **Database:** Migrated the `users` table (`ALTER TABLE users ALTER COLUMN email DROP NOT NULL;`) to prevent backend crashes when Clerk created a user without an email.
    -   **Clerk Instance:** Moved the application from a Development to a full Production instance in Clerk, including configuring DNS and updating all services with `live` production API keys.
    -   **Clerk SSO:** Re-configured Google Sign-In for the new production instance to resolve OAuth `client_id` errors.
    -   **Backend Routes:** Refactored all backend routes (`profile.py`, `jobs.py`, `onboarding.py`) to consistently use `g.current_user` for retrieving the authenticated user, resolving multiple `AttributeError` crashes.
-   **Critical UI: Profile Page Restoration:** Restored multiple missing `<Collapsible>` sections to the User Profile page, which had been accidentally truncated.
-   **Critical UI: Profile Page Hang:** Resolved a silent frontend error where the profile page would hang indefinitely for new users due to an attempt to call a method on null geolocation data.
-   **Frontend Warnings:** Eliminated all Clerk SDK deprecation warnings by removing the `afterSignInUrl`/`afterSignUpUrl` props from components and the corresponding environment variables, relying instead on the modern `fallbackRedirectUrl` prop.

### Added
-   **Product Backlog:** Added several new feature and UX improvement ideas discovered during the debugging process, including resume versioning, enhanced profile completion UX, and smarter AI salary inference.

## [v0.27.0] - 2025-07-01 - Production Authentication & Profile Page Stability

This release resolves two critical, high-priority bugs that were blocking core user flows. It fully stabilizes the production authentication environment, including the new user sign-up and redirect process. It also restores the user profile page to its complete, functional state, fixing both visual and stability issues.

### Fixed
-   **Critical Bug (Profile Page):** Restored multiple missing `<Collapsible>` sections ("Work Environment & Requirements", "Skills & Industry Focus", "Personality & Self-Assessment") to the User Profile page, which had been accidentally truncated.
-   **Critical Bug (Profile Page Hang):** Resolved a silent frontend error where the profile page would hang indefinitely on "Loading profile..." for new users. The page was attempting to call `.toFixed()` on null geolocation data.
-   **Critical Bug (New User Redirect):** Fixed a complete failure of the new user sign-up flow. The fix was multi-layered:
    -   **Database:** Migrated the `users` table (`ALTER TABLE users ALTER COLUMN email DROP NOT NULL;`) to prevent backend crashes when Clerk created a user without an email (e.g., via social SSO).
    -   **Clerk Instance:** Moved the application from a Development to a full Production instance in Clerk, including configuring DNS CNAME records in Cloudflare to authorize the production domain.
    -   **Environment:** Updated Vercel and Render with new `live` production API keys.
    -   **SSO:** Re-configured Google Sign-In for the new production instance to resolve OAuth `client_id` errors.
    -   **Frontend:** Updated the `<SignUp>` component to use the modern `fallbackRedirectUrl` prop instead of the deprecated `afterSignUpUrl`.
-   **Debugging:** Added `console.log` statements to the profile fetch lifecycle to improve future debugging.

### Changed
-   **Protocols:** Updated `PROTOCOLS.md` to include a `400,000` token soft-stop for Pro model conversations in the `Session Budgeting Protocol`.

## v0.26.0 - 2025-07-01 - User Onboarding & Deep Fit Framework (Partial)

This release implements the foundational backend and frontend scaffolding for a new, two-phase user onboarding experience designed to capture deep user preferences. While the feature is not yet complete, the core API endpoints, database schema, and UI pages have been established. This release also includes a critical fix for new user signups.

### Added
-   **Feature:** Created a new `/welcome` page for resume submission as the first step for new users.
-   **Backend:** Added a `/api/onboarding/parse-resume` endpoint to parse resume text using Gemini and pre-fill user profiles.
-   **Database:** Migrated the `user_profiles` table to include `has_completed_onboarding` and several new "Deep Fit" columns for work style preferences.

### Changed
-   **Authentication:** The `auth.py` decorator now correctly resolves a Clerk `sub` ID to an internal user ID, creating a new user record in the database on their first API call. This makes the user creation flow robust.

### Fixed
-   **Critical Bug:** Resolved a `KeyError: 'id'` and a `column "full_name" does not exist` error that caused a `500 Internal Server Error` for all new user signups, unblocking the registration process.

### Known Issues
-   The user profile page (`/dashboard/profile`) is currently broken and does not render all fields.
-   The redirect flow for new users from signup -> welcome -> profile is not yet implemented.
-   UI elements on the profile page, such as dropdowns, are not displaying their selected values correctly.

## [v0.25.0] - 2025-06-30 - Full-Stack Preview Environments & Branching Workflow

This release establishes a foundational DevOps capability, enabling fully automated, full-stack preview environments for feature branches. This significantly improves development velocity, testing reliability, and code quality by allowing isolated testing before merging to production.

### Added
-   **DevOps:** Enabled full-stack preview environments by connecting Vercel Preview Deployments with dedicated Render backend services for feature branches.
-   **Backend:** Implemented regex-based validation for the JWT's `azp` claim in `auth.py` to securely and automatically authorize dynamic Vercel preview URLs.

### Changed
-   **Backend:** Refactored the Flask CORS configuration in `app.py` to correctly handle preflight `OPTIONS` requests from any origin, unblocking cross-origin communication for preview deployments.
-   **Frontend:** The API client hook (`useTrackedJobsApi.ts`) now uses a preview-specific environment variable (`NEXT_PUBLIC_BACKEND_PREVIEW_URL`) to connect to the correct backend service during preview deployments.
-   **Documentation:** Added a formal "Git Branching & Preview Protocol" to `PROTOCOLS.md` to guide future development.

### Fixed
-   **Authentication:** Resolved critical authentication failures ('Invalid Authorized Party') that previously blocked all Vercel preview deployments.
-   **CORS:** Fixed "No 'Access-Control-Allow-Origin' header" errors that blocked all API communication from Vercel preview deployments.

## [v0.24.0] - 2025-07-01 - User Profile Geolocation

This release introduces the ability for users to add their geographic location to their profile, laying the groundwork for future proximity-based job searching.

### Added
-   **Feature:** A "Use My Current Location" button on the user profile page now allows users to capture their latitude and longitude via the browser's Geolocation API.
-   **Feature:** A "Clear Location" button has been added, giving users control to remove their saved coordinate data.
-   **Database:** Migrated the `user_profiles` table to add `latitude` and `longitude` columns.

### Changed
-   **Backend:** The `ProfileService` now correctly converts `Decimal` types from the database into `float`s before JSON serialization, preventing data type mismatches on the frontend.
-   **Documentation:** `PROTOCOLS.md` has been updated with new "Full-File Output," "Backlog Content," and refined "Session Budgeting" protocols to improve development efficiency. `BACKLOG.md` has been streamlined to only include "To Do" items.

### Fixed
-   **Frontend:** Resolved a critical bug where `latitude` and `longitude` were being treated as strings after being fetched from the API, causing a `toFixed is not a function` error and crashing the profile page.
-   **UI:** Restored all missing content within the collapsible sections of the profile page that was accidentally removed in a previous turn.

## [v0.23.0] - 2025-07-01 - Backend Service Layer Implementation

This release completes the backend refactoring effort by introducing a dedicated service layer for business logic, further enhancing the application's architecture and maintainability.

### Added
-   **`apps/backend/services/tracked_job_service.py`**: A new service class was created to encapsulate all business logic related to updating tracked job records, in accordance with the `DATA_LIFECYCLE.md` plan.

### Changed
-   **`apps/backend/routes/jobs.py`**: The `update_tracked_job` route handler was refactored to delegate all update logic to the new `TrackedJobService`, making the route a clean API-facing wrapper.
-   **Documentation**: Updated `BACKLOG.md` and `PROTOCOLS.md` to include a new "Session Cost" estimation system for better planning and management of AI Studio token quotas.

## [v0.22.0] - 2025-07-01 - Data Lifecycle Migration & Frontend Refactor

This release implements the foundational database schema for the new Data Lifecycle model and completes the frontend component refactoring for the main user dashboard.

### Changed
-   **Database:** Executed a major migration on the `tracked_jobs` table to align with `DATA_LIFECYCLE.md`. This replaced the `status` text field with a robust `ENUM` and added several new `TIMESTAMPTZ` columns for tracking milestones (e.g., `applied_at`, `first_interview_at`, `resolved_at`).
-   **Backend:** Updated all backend services and routes (`jobs.py`, `admin_service.py`) to be compatible with the new `tracked_jobs` schema.
-   **Frontend:** Refactored the monolithic `dashboard/page.tsx` by extracting all data fetching and state management for tracked jobs into a new custom hook (`useTrackedJobsApi.ts`).
-   **Frontend:** Decoupled type definitions into a dedicated `types.ts` file and the job submission form into its own `JobSubmissionForm.tsx` component.
-   **Frontend:** Updated the dashboard UI's filtering logic and status-change handlers to use the new data model and ENUMs from the backend.

### Fixed
-   Resolved a `git` divergence and merge conflict caused by amending a pushed commit, successfully recovering the local branch and pushing the required fix.
-   Corrected a TypeScript error in `page.tsx` where an invalid property (`updated_at`) was being passed in a payload, which was causing Vercel build failures.

## [v0.21.0] - 2025-07-01 - Backend Modularization & Frontend Stability

This release marks a major architectural refactoring of the backend, transforming it from a single monolithic file into a scalable, service-oriented application. Additionally, a critical performance bug on the frontend dashboard has been resolved, which also fixed related UI component-state issues.

### Added
-   **Backend Architecture:** Introduced a new service-oriented architecture with an application factory (`create_app`).
-   **Backend Modules:** Created new, dedicated modules for `config`, `database`, `services` (job, profile, admin), and `routes` (using Flask Blueprints) to organize code by domain.

### Changed
-   **Backend:** Refactored the entire `apps/backend/app.py` file. It is now a lean application factory that assembles the application from modular components. All business logic, database connections, and route definitions have been moved to their respective modules.
-   **Deployment:** Updated the Render **Build Command** and **Start Command** to work with the new package-aware, modular architecture, resolving deployment failures.

### Fixed
-   **Backend:** Resolved `ImportError: attempted relative import with no known parent package` which caused deployment failures after the initial refactor.
-   **Frontend:** Fixed a critical infinite loop in the dashboard's `useEffect` hooks in `page.tsx` that was causing repeated, unnecessary API calls and preventing the dashboard from loading correctly.
-   **Frontend:** Frontend: As a beneficial side effect of fixing the render loop, resolved a bug where the status dropdown in the "My Job Tracker" table would not persist its state or would collapse unexpectedly.


## [v0.20.0] - 2025-07-01 - Architectural Definition

This release marks a significant architectural milestone. A comprehensive data lifecycle for the core `tracked_jobs` entity has been formally defined and documented, establishing a robust state machine that will govern all future application pipeline features. This work serves as the foundation for enhanced data integrity, advanced analytics, and new user-facing functionality.

### Added
-   **Architecture:** Created `Documentation/DATA_LIFECYCLE.md` to define a comprehensive state machine for the `tracked_jobs` entity. This foundational document includes explicit state definitions (e.g., `SAVED`, `INTERVIEWING`, `OFFER_NEGOTIATIONS`), controlled transition rules, key milestone timestamps (`applied_at`, `resolved_at`), and CRM-like features (`next_action_at`).

### Changed
-   **Documentation:** Refined and expanded the product backlog based on the data lifecycle planning session. The high-level "Define & Implement Data Lifecycle" epic was completed, and its implementation was broken down into several smaller, actionable tasks.
-   **Documentation:** Added several new, high-value features to the backlog, including "Detailed Interview Stage Tracking", "AI-Assisted Offer Negotiation", and "User-set Reminders & Next Action Notifications".
-   **Documentation:** Linked the `ARCHITECTURE.md` to the new `DATA_LIFECYCLE.md` document for better cross-reference.

## [v0.19.0] - 2025-06-30 - Automated Expiration & UI Filtering

This release introduces robust backend automation for identifying and marking expired job postings and stale tracked applications, significantly improving data hygiene. The user interface has also been enhanced with new status displays and filtering options to help users manage their job pipeline more effectively. Critical authentication and frontend build issues were resolved to ensure application stability.

### Added
-   **Backend Feature:** Implemented automated job posting expiration based on URL reachability, age (60 days from `found_at`), and identification of legacy malformed URLs, marking them with specific `Expired - Unreachable`, `Expired - Time Based`, or `Expired - Legacy Format` statuses in the `jobs` table.
-   **Backend Feature:** Implemented automated tracked application expiration, marking applications as `Expired` with `Stale - No action in 30 days` reason if `updated_at` is older than 30 days and not in a final status.
-   **Frontend UI:** Integrated `job_posting_status` and `last_checked_at` into the "My Job Tracker" table to show the status of the original job posting.
-   **Frontend UI:** Added `status_reason` column to the "My Job Tracker" table to display reasons for application statuses (e.g., "Stale - No action in 30 days").
-   **Frontend UI:** Implemented client-side filtering options for "My Job Tracker" to allow users to view "All Jobs", "Active Applications", "Inactive Applications", "Active Job Postings", and "Expired Job Postings".

### Changed
-   **Backend Architecture:** Refined `check_job_url_validity` to use a more precise regex for URL extraction and explicitly handle legacy malformed URLs outside the general validity check.
-   **Frontend UI/UX:** Updated the "Active Applications" filter definition to include `Applied`, `Interviewing`, and `Offer` statuses, providing a more accurate representation of an active pipeline.
-   **Frontend UI/UX:** The filter dropdown now dynamically updates the table's total count and resets pagination (`pageIndex` to 0) when a filter is applied, ensuring correct pagination behavior for filtered results.
-   **Backend Authentication:** Enhanced `auth.py` with more detailed logging for JWT validation steps and improved error handling to provide better diagnostics for authentication failures.
-   **Backend Authentication:** Temporarily (`v0.19.0` only for testing) modified `/api/admin` endpoints to use `X-Api-Key` authentication for easier testing, then reverted to `token_required` (Clerk JWT) for production security.

### Fixed
-   **Frontend Build:** Resolved persistent `Unexpected token main` syntax error in `apps/frontend/app/dashboard/page.tsx` that caused Vercel build failures.
-   **Backend Authentication:** Corrected `JWT Invalid Token Error: Token is missing the "aud" claim` by re-implementing manual validation for Clerk's `azp` claim instead of `PyJWT`'s `audience` parameter.
-   **Backend Data Query:** Fixed SQL regex operator usage (`~`) in `apps/backend/app.py` for matching legacy URL patterns in `jobs` table.

## [v0.18.0] - 2025-06-30 - Job Tracker Enhancement & Profile UX Improvements

This release focuses on enhancing the job tracker's usability by introducing a "favorite" feature and improving the user profile management experience with collapsible sections for better navigation.

### Added
-   **Feature:** Implemented an `is_excited` boolean field and a corresponding interactive checkbox column in the "My Job Tracker" table to allow users to mark jobs as favorites.
-   **UI/UX:** Organized the User Profile management page (`/dashboard/profile`) into logical, collapsible subsections (e.g., "Contact & Basic Information", "Career Aspirations", "Work Environment & Requirements", "Skills & Industry Focus", "Personality & Self-Assessment") using Shadcn UI's `Collapsible` component. These sections are expanded by default upon page load.

### Changed
-   **Frontend UI:** Reordered columns in the "My Job Tracker" table to move the "Excited?" column after the "Relevance" score, improving visual separation and clarity.
-   **Frontend UI:** Replaced the native HTML `<select>` element with the Shadcn UI `Select` component in the "Status" column of the "My Job Tracker" table for improved UI consistency.
-   **Documentation:** Identified and added "Feature: Bulk Actions for Tracked Jobs" to the unrefined backlog, acknowledging the need for bulk operations following the implementation of row selection.
-   **Documentation:** Identified and added "Platform: Standard Business Email Addresses" and "Marketing: LinkedIn Company Profile" to the unrefined backlog for future consideration.
-   **Documentation:** Updated `PROTOCOLS.md` to reflect the current `shadcn` CLI command (`npx shadcn@latest add <component>`) instead of the deprecated `shadcn-ui`, and added a comprehensive frontend development and deployment protocol.
-   **Documentation:** Added "Backend: Build out job profiles and the import process to store important information" and "Backend: Build out user, company, and job lifecycles" to the unrefined backlog.

### Fixed
-   **Frontend Build:** Resolved a syntax error (`Expected 'from', got '=>'`) in `apps/frontend/app/dashboard/profile/page.tsx` related to the `useRouter` import.
-   **Frontend Build:** Resolved a syntax error (`Expected 'from', got 's'`) in `apps/frontend/app/dashboard/profile/page.tsx` related to the `Input` component import.
-   **Frontend Build:** Resolved "Module not found" error for `@/components/ui/collapsible` by adding `npx shadcn@latest add collapsible` to the deployment steps.
-   **Frontend UI:** Corrected an issue where the "Excited?" column appeared twice in the "My Job Tracker" table due to a duplicate column definition.
-   **Frontend UI:** Ensured all newly implemented collapsible sections on the user profile page are expanded by default.

## [v0.17.0] - 2025-06-30 - User Onboarding Redirection

This release improves the new user onboarding experience by automatically redirecting new sign-ups to their profile page.

### Added
-   **Feature:** Implemented automatic redirection of new users to `/dashboard/profile` immediately after sign-up to streamline the onboarding process for profile completion.

### Changed
-   No existing features were changed in this release.

### Fixed
-   No specific bugs were identified or fixed in this release; changes were feature-driven.

## [v0.16.0] - 2025-06-30 - Shadcn UI Refinement & Core Component Installation

This release focuses on improving the user interface consistency by adopting Shadcn UI components more broadly across the application and establishing foundational UI components for future development.

### Added
-   **UI Components:** Installed core Shadcn UI components (`label`, `textarea`, `select`) in `apps/frontend`, configuring `components.json` with `Zinc` as the base color.

### Changed
-   **Frontend UI:** Replaced all native HTML `<label>`, `<textarea>`, and `<select>` elements with their corresponding Shadcn UI components (`Label`, `Textarea`, `Select`) on the User Profile management page (`apps/frontend/app/dashboard/profile/page.tsx`).
-   **Frontend UI:** Updated the "Paste Job Posting URL" label on the main Dashboard page (`apps/frontend/app/dashboard/page.tsx`) to use the Shadcn UI `Label` component.

### Fixed
-   No specific bugs were identified or fixed in this release; changes were feature-driven.

## [v0.15.0] - 2025-06-30 - User Profile Work Style & Remote Preferences

This release introduces new user profile fields to capture preferred work style and remote preferences, enhancing the context for future AI job matching. It also refines the user interface for these new fields to prevent logical inconsistencies.

### Added
-   **Feature:** Implemented `preferred_work_style` (On-site, Remote, Hybrid) and `is_remote_preferred` (boolean) fields to the user profile management page.
-   **Database Schema:** Added `preferred_work_style` (VARCHAR) and `is_remote_preferred` (BOOLEAN) columns to the `user_profiles` table.
-   **Backend API:** Enhanced `/api/profile` (GET and PUT) to handle the new profile fields.
-   **AI Context:** Updated the job analysis prompt within `/api/jobs/submit` to include `preferred_work_style` and `is_remote_preferred` in the user profile context for AI processing.

### Changed
-   **Frontend UI/UX:** Implemented conditional rendering for the "I prefer remote work generally." checkbox, making it only visible if "Preferred Work Style" is not set to "On-site" to prevent conflicting user input. Automatically unchecks and hides `is_remote_preferred` if "On-site" is selected.
-   **Documentation:** Increased the priority (RICE score) of the backlog item "Refine UI Components: Implement Shadcn UI for Textarea, Label, and Select" due to observed technical debt and UI consistency needs.

### Fixed
-   No specific bugs were identified or fixed in this release; changes were feature-driven.

## [v0.14.0] - 2025-06-29 - User Profile Management & UI Bugfixes

This release introduces the foundational user profile management feature, allowing users to input and update their detailed career preferences. Critical frontend build and import errors were also resolved, ensuring application stability.

### Added
-   **Feature:** Implemented a dedicated User Profile Management page (`/dashboard/profile`) allowing users to input and update detailed profile information.
-   **Backend API:** Added `PUT /api/profile` endpoint to support comprehensive updates to user profiles, including dynamic field handling.
-   **Frontend UI:** Added navigation from the main dashboard to the new user profile page via an "Edit Profile" button.
-   **Documentation:** Added new unrefined ideas to the product backlog for future consideration (Geo-location for current location, LinkedIn content parsing for resume, preferred work style/remote preference, and modularization of large frontend/backend files).

### Changed
-   **Backend API:** Enhanced `GET /api/profile` to ensure all profile fields are consistently returned, converting `None` values to empty strings for frontend convenience.
-   **Documentation:** Refined the definition of the "AI Model" column in `BACKLOG.md` to clarify its purpose for AI assistant (my) level of effort in code generation.

### Fixed
-   **Frontend Build:** Resolved syntax errors in `apps/frontend/app/dashboard/profile/page.tsx` caused by accidental inclusion of markdown formatting.
-   **Frontend Build:** Corrected relative import paths (`./data-table`, `./components/columns`) in `apps/frontend/app/dashboard/profile/page.tsx` to resolve "Module not found" errors.
-   **Frontend UI:** Replaced missing Shadcn UI components (`Textarea`, `Label`, `Select`) with native HTML elements and basic Tailwind CSS styling in `apps/frontend/app/dashboard/profile/page.tsx` to ensure successful build and functionality.

## [v0.13.0] - 2025-06-29 - Data Integrity & Analysis Hardening

This release significantly improves the backend's data integrity, particularly for AI-driven job analyses. It ensures that analyses are correctly associated with specific users and includes versioning for future compatibility. Historical data was also cleaned up to improve dashboard clarity.

### Added
-   **Database:** Added `user_id` and `analysis_protocol_version` columns to the `job_analyses` table, and updated the primary key to a composite `(job_id, user_id)` to support per-user analyses.
-   **Backend:** Implemented a new internal `ANALYSIS_PROTOCOL_VERSION` constant (`2.0`) to tag new and updated AI analyses.
-   **Backend:** Added a temporary, authenticated `/api/debug/mark-unreachable-jobs` endpoint to facilitate a one-time data cleanup operation.

### Changed
-   **Backend API:** Modified the `/api/jobs/submit` endpoint to use an `UPSERT` (INSERT ON CONFLICT UPDATE) logic for `job_analyses` records, ensuring analyses are created or updated for specific user-job pairs.
-   **Backend API:** Updated the `JOIN` condition in `/api/jobs/submit` and `/api/tracked-jobs` to correctly fetch `job_analyses` for the specific `user_id` and `job_id`, preventing data leakage and ensuring correct data display.

### Fixed
-   **Data Integrity:** Resolved the issue of `job_analyses` only storing a single analysis per job, now correctly supporting per-user analyses.
-   **Historical Data:** Cleaned up historical `tracked_jobs` entries that lacked valid job URLs or v2.0 analyses, marking 295 such jobs as "Expired - Unreachable" in the database.
-   **Backend Errors:** Corrected multiple SQL syntax errors in remediation scripts that prevented successful database updates, particularly in the `UPDATE FROM` clause.

## [v0.12.0] - 2025-06-29 - New User Onboarding Fixes & UI Polish

This release addresses critical new user onboarding issues, ensuring a smooth transition from sign-up to dashboard. It also enhances overall user experience through improved navigation consistency on the landing page and across the application header.

### Added
-   **Backend:** Implemented automatic creation of a default `user_profiles` entry for new users upon their first request to `/api/profile`, ensuring a profile always exists and preventing dashboard errors.

### Changed
-   **Frontend UI/UX:** The "Get Started" button on the landing page (`/`) is now dynamically context-aware. For signed-in users, it directs to `/dashboard`; for signed-out users, it directs to `/sign-up`.
-   **Frontend UI/UX:** The "Transparent Talent" header text now functions as a clickable link, consistently navigating to the application's homepage (`/`).

### Fixed
-   **Onboarding:** Resolved the "An Error Occurred" issue experienced by new users attempting to access the dashboard immediately after sign-up, caused by a missing `user_profiles` entry.
-   **UI/UX:** Eliminated the redundant "Go to Dashboard →" link on the landing page's hero section, streamlining navigation options.
-   **UI/UX:** Corrected the navigation loop on the landing page for logged-in users who clicked "Get Started."

## [v0.11.0] - 2025-06-28 - Job Tracker Pagination & Stable Sorting

This release introduces comprehensive pagination for the "My Job Tracker" table, significantly enhancing performance and user experience when managing numerous tracked jobs. A critical bug related to unstable data sorting on paginated results has also been resolved.

### Added
-   **UI/UX:** Implemented client-side pagination controls for the "My Job Tracker" data table.
-   **Backend:** Added `page` and `limit` query parameters to the `/api/tracked-jobs` endpoint to support server-side pagination.
-   **Backend:** The `/api/tracked-jobs` endpoint now returns the `total_count` of tracked jobs, enabling accurate pagination display on the frontend.

### Changed
-   **Backend:** Modified the `get_tracked_jobs` SQL query to include `LIMIT` and `OFFSET` clauses.
-   **Backend:** Enhanced the `ORDER BY` clause in `get_tracked_jobs` to include `t.id DESC` as a secondary sort key, ensuring stable and consistent pagination results even when multiple jobs share the same `created_at` timestamp.
-   **Frontend:** Updated `apps/frontend/app/dashboard/page.tsx` to manage pagination state and pass it to the `DataTable` component.
-   **Frontend:** Refactored `handleUpdate` and `handleRemoveJob` in `page.tsx` to re-fetch the current page of data after a successful operation, maintaining data consistency.
-   **Frontend:** Adjusted `handleJobSubmit` in `page.tsx` to reset pagination to the first page after a new job submission, ensuring the new entry is immediately visible.
-   **Frontend:** Configured `@tanstack/react-table` in `apps/frontend/app/dashboard/data-table.tsx` for manual pagination, integrating external state and `totalCount`.

### Fixed
-   **Data Consistency:** Resolved an issue where jobs could appear duplicated across different pagination pages or be skipped entirely due to unstable sorting of rows with identical `created_at` timestamps.

## [v0.10.0] - 2025-06-28 - Automated 'Date Applied' & Frontend Stability

This release introduces a significant quality-of-life improvement by automating the 'Date Applied' field for tracked jobs, streamlining the user workflow. It also includes critical frontend stability enhancements that improve the reliability of UI updates and deployment processes.

### Added
-   **UI/UX:** Implemented automatic population of the `applied_at` date when a tracked job's status is set to "Applied".
-   **UI/UX:** Added logic to clear the `applied_at` date when a tracked job's status is changed from "Applied" to any other status.

### Changed
-   **Frontend:** Enhanced the optimistic UI update logic within the `handleUpdate` function in `apps/frontend/app/dashboard/page.tsx` to correctly handle `null` and `undefined` values.
-   **Frontend:** Refined the `UpdatePayload` type to explicitly allow `null` for optional fields like `notes`, aligning with data model requirements.

### Fixed
-   **Build:** Resolved a TypeScript compilation error (`Type 'undefined' is not assignable to type 'string | null'`) in `apps/frontend/app/dashboard/page.tsx` that was causing Vercel build failures.

## [v0.9.0] - 2025-06-28 - Production Domain Deployment

This release establishes the Transparent Talent application on its official production domain, significantly enhancing its public accessibility and formalizing its presence. Critical authentication configurations were updated to ensure seamless operation under the new domain.

### Added
-   **Deployment:** Configured and deployed the frontend application to the production domain `transparenttalent.ai` (redirecting to `www.transparenttalent.ai`) on Vercel.

### Changed
-   **Authentication:** Updated Vercel frontend environment variables and Render backend `CLERK_AUTHORIZED_PARTY` to correctly recognize and validate JWTs from the new `www.transparenttalent.ai` domain.

### Fixed
-   **Authentication Error:** Resolved "Profile fetch failed" and `401 Unauthorized` errors on the dashboard caused by invalid authorized party configurations for the new production domain.

## [v0.8.0] - 2025-06-28 - Data Contract Standardization & UI Refactor

This release completes a key architectural task by standardizing the data contract with the AI service to use `snake_case`, improving system-wide consistency. It also includes a significant frontend refactor for maintainability and several bug fixes that improve the user experience.

### Added
-   **Architectural Improvement:** Decoupled frontend table column definitions into a dedicated `apps/frontend/app/dashboard/components/columns.tsx` component to improve code organization and maintainability.
-   **UI Feature:** The "My Job Tracker" table now displays a "Date Saved" column, using the creation date of the tracked job for more accurate record-keeping.

### Changed
-   **Data Contract:** Standardized the AI job analysis data contract to use `snake_case` for all keys, from the initial prompt to the final API response.
-   **Backend API:** Updated the `/api/tracked-jobs` and `/api/jobs/submit` endpoints to include the `created_at` timestamp in their responses.
-   **Frontend Data Model:** The `TrackedJob` interface and all related components were updated to use the new `created_at` field.

### Fixed
-   **UI Bug:** Corrected a CSS issue where dropdown menus were semi-transparent and had an incorrect z-index, causing them to improperly overlap table content.
-   **UI Bug:** Resolved an issue where newly submitted jobs would display "Invalid Date". The table now correctly shows the "Date Saved" for new entries and a placeholder for un-set "Date Applied" fields.

## [v0.7.0] - 2025-06-28
| Feature/Bugfix | Original Tier | RICE Score |
| :--- | :--- | :--- |
| **UI: Interactive Job Tracker** | T2 | 4000 |

## [v0.6.0] - 2025-06-28
| Feature/Bugfix | Original Tier | RICE Score |
| :--- | :--- | :--- |
| **Feature: User Job Submission** | T2 | 6000 |

## [v0.5.0] - 2025-06-28
| Feature/Bugfix | Original Tier | RICE Score |
| :--- | :--- | :--- |
| **Feature: Logged Out Experience** | T2 | 8000 |

## [v0.4.0] - 2025-06-28
| Feature/Bugfix | Original Tier | RICE Score |
| :--- | :--- | :--- |
| **Bugfix: Resolve Production Authentication** | T1 | 12000 |

## [v0.3.1] - 2025-06-28 - Failed Authentication Bugfix Attempt

This release documents a significant but unsuccessful attempt to resolve the critical production authentication bug. While the issue persists, the debugging process revealed key insights into the unexpected behavior of the `clerk-backend-api` library, which will inform the next attempt.

### Changed
-   **Iterative Debugging on `auth.py`:** Multiple versions of the `token_required` decorator were deployed to diagnose a series of cascading errors. This process invalidated several common implementation patterns.

### Fixed
-   **Clerk Dashboard Misconfiguration:** Corrected a user-facing issue where a misconfigured "Restrictions" list was improperly blocking valid user sign-in attempts.

### Unresolved Issues
-   **Critical `401 Unauthorized` Error:** The root cause of the authentication failure remains. The latest logs indicate the `clerk.authenticate_request()` method is throwing a `TypeError: Clerk.authenticate_request() missing 1 required positional argument: 'options'`, even when provided with what appear to be the correct parameters. The exact expected structure for the `options` argument remains unknown.

## [v0.3.0] - 2025-06-27 - End-to-End User Authentication

This version implements a complete, secure authentication system across the entire application stack, from the frontend client to the backend API.

### Added
-   **User Authentication:** Integrated Clerk for robust user sign-up, sign-in, and session management across the full stack.
-   **Frontend Middleware:** Added `middleware.ts` to the Next.js app to protect all routes and enforce authentication.
-   **Backend Token Validation:** Created an `auth.py` decorator in the Flask backend to validate JWTs on all protected API endpoints.
-   **Clerk SDKs:** Added `@clerk/nextjs` to the frontend and `clerk-backend-api` to the backend.
-   **Database Migration:** Added a `clerk_user_id` column to the `users` table to link application data with the authentication provider.

### Changed
-   **API Security:** All backend endpoints in `app.py` were refactored to be protected by the `@token_required` decorator and to securely derive the user's identity from the session, removing user identifiers from URL parameters.
-   **Frontend Dashboard:** The main dashboard component was refactored to use modern, secure data-loading hooks (`useAuth`, `useUser`) instead of relying on URL parameters.
-   **Frontend Layout:** Modified `apps/frontend/app/layout.tsx` to include the `<ClerkProvider>` and user session controls (`<UserButton>`).

### Fixed
-   **Vercel Deployments:** Resolved a series of `MIDDLEWARE_INVOCATION_FAILED` and TypeScript build errors by correcting the Clerk middleware implementation and component props.
-   **Render Deployments:** Fixed numerous `ModuleNotFoundError` and `TypeError` crashes by correcting the Clerk python package name (`clerk-backend-api`), updating the import paths in `auth.py`, and aligning the Clerk client usage with the specific library version's requirements.
-   **Python Versioning:** Discovered and confirmed that the original Python version (3.13) was incompatible with the authentication libraries, necessitating a downgrade to a stable LTS version (3.12) for production deployments.

## [v0.2.0] - 2025-06-26 - Monorepo Migration & Production Deployment

This version marks the successful re-architecting of the project into a professional monorepo structure and the full deployment of all services to production hosting environments.

### Added
-   **`vercel.json`:** Created a Vercel configuration file to provide explicit build and routing instructions, ensuring successful deployment of the frontend application.
-   **`ARCHITECTURE.md`:** Added a dedicated document to formally describe the full-stack system architecture.

### Changed
-   **Repository Structure:** Migrated the entire codebase from two separate projects into a single monorepo, managed with pnpm workspaces and Turborepo.
-   **Frontend Deployment:** The Next.js frontend is now deployed to **Vercel** from the `apps/frontend` directory of the monorepo.
-   **Backend Deployment:** The Render deployment configuration was updated to correctly build and deploy the Flask API from the `apps/backend` directory of the monorepo.

### Fixed
-   Resolved multiple Git submodule issues that prevented proper version tracking of the frontend and backend applications.
-   Corrected conflicting `package-lock.json` and `next.config.ts` files that caused local and production build failures.
-   Systematically debugged and resolved a series of Vercel 404 deployment errors by correcting build outputs and implementing explicit routing rules.

## [v0.1.0] - 2025-06-26 - Initial MVP and Data Foundation

This initial version represents the successful transition from a manual, spreadsheet-based system to a functional full-stack web application with a robust data foundation.

### Added
-   **Initial Backend API (v1):** Deployed a Python Flask application to Render, serving user data and job information via a RESTful API.
-   **Job Tracker Functionality:** Implemented full CRUD (`GET`, `POST`, `PUT`, `DELETE`) endpoints for tracked jobs, allowing users to manage their application pipeline.
-   **Initial Frontend Dashboard (v1):** Developed a local Next.js application that successfully connects to the backend API to display user profiles, watchlists, job matches, and the interactive job tracker.
-   **Comprehensive Data Migration:**
    *   Successfully designed and executed a migration script to import all historical user and company data from **Bubble JSON exports** into the new PostgreSQL database.
    *   Successfully designed and executed a second, more complex migration script to parse, clean, and import all historical application data from multiple **CSV files** (`TT Opportunities`, `Greg Freed - Job Search`).
    *   Unified all disparate data sources into a single, relational database, creating a comprehensive foundation for all future features.

### Changed
-   **Upgraded Database:** Migrated from a conceptual file-based system to a production-grade **PostgreSQL** database hosted on Render.
-   **Enhanced Business Logic:** Refined API endpoints to filter out irrelevant job data and intelligently handle application status changes.

### Fixed
-   Resolved multiple Python dependency issues (`flask_cors`) to ensure stable deployment on Render.
-   Corrected and iteratively fixed database schema mismatches discovered during the complex data migration process.