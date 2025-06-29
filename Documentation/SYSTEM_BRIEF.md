# Transparent Talent: System Brief v1.9

## 1. Core Vision & Business Model
*   **Problem:** The job market is inefficient, opaque, and biased.
*   **Short-Term Solution:** An AI-powered service for individual job seekers that uses a feedback-driven, consultative approach to provide clarity and systematically evaluate opportunities.
*   **Long-Term Vision ("Nielsen for Talent"):** Become a foundational, two-way transparency layer for the talent market by providing standardized, verified data for both candidates and businesses.
*   **Core Value Prop:** Replace subjective, keyword-driven hiring with explicit, multi-dimensional relevance calculations (`Position Relevance` + `Environment Fit`).

## 2. Technology Stack & Architecture
*   **Frontend:** Next.js (React) hosted on **Vercel**.
*   **Backend:** Python with **Flask**, hosted as a web service on **Render**.
*   **Database:** **PostgreSQL**, hosted on **Render**.
*   **AI Service:** Google **Gemini API**, called exclusively from the backend.
*   **Authentication:** **Clerk**, integrated with the frontend. Backend uses manual JWT verification.
*   **Architecture Style:** Decoupled three-tier application, managed in a **monorepo**.

## 3. Current Project Status
*   **Architecture:** Formally defined and documented a comprehensive data lifecycle for tracked jobs in `DATA_LIFECYCLE.md`, creating a robust state machine that includes milestone timestamps, CRM-like functionality for next actions, and a foundation for future features like offer negotiation support and hiring funnel analytics.
*   **Application is stable and functional on its production domain.** The application now features a public-facing landing page for new user acquisition and a fully functional, authenticated user dashboard.
*   **Automated Data Hygiene & Expiration:** Automated processes are now in place to identify and update the status of expired job postings (based on URL validity, age, or legacy format) and stale tracked applications (based on inactivity).
*   **Enhanced Job Tracker UI:** The "My Job Tracker" table displays clear statuses for job postings and tracked applications, including reasons for expiration. New filtering options allow users to efficiently view "All Jobs", "Active" or "Inactive" job applications, and "Active" or "Expired" job postings. The filtering and pagination now work cohesively.
*   **New User Onboarding Improved:** Critical issues preventing new users from accessing the dashboard after sign-up have been resolved by ensuring a default user profile is automatically created. New users are now smoothly redirected to the profile page after signup, encouraging immediate profile completion.
*   **Architectural Hardening:** The data contract between the backend and the AI service has been standardized to `snake_case`, improving system-wide consistency and maintainability. Authentication is robust across original and new production domains.
*   **UI Refactor & Bug Fixes:** Resolved several UI bugs and refactored the frontend by decoupling the data table's column definitions, improving code quality and future scalability.
*   **Workflow Automation:** The user dashboard now intelligently automates the `applied_at` date for tracked jobs, setting it automatically when the status changes to 'Applied' and clearing it when changed from 'Applied', significantly streamlining user workflow. Frontend stability for data updates has also been improved.
*   **Pagination Implemented:** The "My Job Tracker" table now supports full pagination, including server-side data fetching and robust sorting, allowing efficient browsing of large datasets.
*   **Enhanced UI/UX:** Navigation has been polished; the header title links to the homepage, and the "Get Started" button on the landing page is now context-aware, directing users appropriately based on their login status.
*   **Data Integrity & AI Analysis Hardening:** The database schema for `job_analyses` has been significantly hardened to correctly support per-user job analyses and include protocol versioning. Backend logic has been updated to align with this new schema. Historical data with invalid job URLs has been identified and marked as 'Expired - Unreachable' to maintain a clean and accurate user dashboard.
*   **User Profile Management:** A comprehensive user profile management page has been implemented, allowing users to input and update their detailed career preferences, essential for personalized AI analysis. Associated backend API and navigation have been established. Frontend build stability for this page has been significantly improved by resolving module import errors.
*   **Work Style & Remote Preferences:** Users can now specify their `preferred_work_style` (e.g., On-site, Remote, Hybrid) and a general `is_remote_preferred` flag within their profile. The UI for these fields intelligently adapts to prevent conflicting inputs, and this information is now fed to the AI for improved job analysis relevance.
*   **Shadcn UI Integration:** Key UI components (labels, text areas, and select dropdowns) have been fully migrated to use Shadcn UI components across the profile and dashboard pages, enhancing visual consistency and project maintainability.
*   **New Feature: Job Tracker Enhancements:** The "My Job Tracker" now includes an "Excited?" column with a checkbox, allowing users to easily flag jobs they are enthusiastic about.
*   **UI/UX Improvement: Collapsible Profile Sections:** The User Profile page has been redesigned with collapsible sections for "Contact & Basic Information", "Career Aspirations", "Work Environment & Requirements", "Skills & Industry Focus", and "Personality & Self-Assessment", significantly improving the user experience for managing detailed profile data.

## 4. Immediate Backlog & Next Steps
1.  **Refactor: Separate `tracked_jobs.status` into `status` and `status_reason` columns (with ENUMs):** The first implementation step of the new Data Lifecycle definition. This involves a database migration and refactoring backend logic. (RICE: 4.0)
2.  **Refactor: Modularize Large Frontend/Backend Files:** Break down monolithic files like `app.py` and `page.tsx` into smaller, more maintainable service modules and components to improve code quality. (RICE: 300)
3.  **Bugfix: Status dropdown not persisting/collapsing on render size:** Investigate and fix the UI issue where the status dropdown does not persist its state or collapses unexpectedly based on browser render size. (RICE: 10000)
4.  **UI/UX: Refine "Inactive Applications" Filter and Status Display:** Refine the "Inactive Applications" filter to accurately reflect status categories like "Expired," "Rejected," "Withdrawn," and "Accepted." (RICE: 8000)
5.  **Feature: Define & Verify New User Account Flow:** Define and implement a comprehensive and verified onboarding flow for new user accounts beyond basic profile creation. (RICE: 6000)
6.  **Feature: User-set Reminders & Next Action Notifications:** Implement the UI and backend logic for the new `next_action_at` and `next_action_notes` fields defined in the Data Lifecycle plan. (RICE: 4000)