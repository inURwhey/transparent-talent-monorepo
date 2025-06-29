# Transparent Talent: System Brief v2.2

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
*   **Architecture Style:** Decoupled three-tier application, managed in a **monorepo**. The backend now follows a service-oriented architecture with an application factory pattern.

## 3. Current Project Status
*   **Backend Service Layer Complete:** A dedicated service layer for business logic is now fully implemented in the backend. The new `TrackedJobService` encapsulates all logic for updating tracked jobs, completing the backend's service-oriented architecture refactor.
*   **Data Lifecycle Activated:** The foundational database migration for the new `tracked_jobs` data lifecycle has been successfully executed. The backend and frontend have been updated to be fully compatible with the new schema, including the new status `ENUM`s and milestone timestamp fields.
*   **Frontend Architecture Refactored:** The main user dashboard component (`page.tsx`) has been completely refactored. All data-fetching logic has been extracted into a reusable custom hook (`useTrackedJobsApi`), and UI sections have been broken into smaller, dedicated components, significantly improving maintainability.
*   **Backend Architecture Refactored:** The backend has been completely refactored from a monolithic `app.py` into a scalable, service-oriented architecture.
*   **Frontend Stability Restored:** A critical infinite loop bug on the user dashboard has been resolved, fixing core performance issues and related UI bugs.
*   **Automated Data Hygiene & Expiration:** Automated processes are now in place to identify and update the status of expired job postings and stale tracked applications.
*   **New User Onboarding Improved:** Critical issues preventing new users from accessing the dashboard after sign-up have been resolved by ensuring a default user profile is automatically created.
*   **Architectural Hardening:** The data contract between the backend and the AI service has been standardized to `snake_case`, improving system-wide consistency.
*   **Workflow Automation:** The user dashboard now intelligently automates the `applied_at` date for tracked jobs.
*   **Pagination Implemented:** The "My Job Tracker" table now supports full pagination.
*   **Enhanced UI/UX:** Navigation has been polished, and the "Get Started" button is now context-aware.
*   **Data Integrity & AI Analysis Hardening:** The database schema for `job_analyses` has been significantly hardened to correctly support per-user job analyses and include protocol versioning.
*   **User Profile Management:** A comprehensive user profile management page has been implemented.
*   **Work Style & Remote Preferences:** Users can now specify their `preferred_work_style` and `is_remote_preferred` flag within their profile.
*   **Shadcn UI Integration:** Key UI components have been fully migrated to use Shadcn UI components.
*   **New Feature: Job Tracker Enhancements:** The "My Job Tracker" now includes an "Excited?" column.
*   **UI/UX Improvement: Collapsible Profile Sections:** The User Profile page has been redesigned with collapsible sections.

## 4. Immediate Backlog & Next Steps
1.  **Feature: User-set Reminders & Next Action Notifications:** Implement the UI and backend logic to allow users to set reminders for their tracked jobs, utilizing the new `next_action_at` and `next_action_notes` fields. (RICE: 4000)
2.  **Marketing: LinkedIn Company Profile:** Create and populate a company profile on LinkedIn to establish a professional presence. (RICE: 10000)
3.  **UI/UX: Refine "Inactive Applications" Filter and Status Display:** Now that the new statuses are in place, refine the "Inactive Applications" filter to accurately reflect status categories like "Expired," "Rejected," "Withdrawn," and "Accepted." (RICE: 8000)
4.  **Feature: Define & Verify New User Account Flow:** Define and implement a comprehensive and verified onboarding flow for new user accounts beyond basic profile creation. (RICE: 6000)