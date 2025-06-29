--- START OF FILE CHANGELOG.md ---
# Transparent Talent - Changelog

All notable changes to this project will be documented in this file.

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