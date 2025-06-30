# Transparent Talent: System Brief v2.4

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
*   **DevOps Workflow Enhanced:** A robust, automated workflow for full-stack preview environments has been established. This connects Vercel Preview Deployments to dedicated Render services for feature branches, enabling isolated testing and significantly improving development velocity and stability.
*   **User Geolocation:** Users can now add their geographic location to their profile via a browser's Geolocation API, providing the foundational data for future proximity-based features. Critical data type bugs (`Decimal` vs `Number`) were resolved to ensure stability.
*   **Backend Service Layer Complete:** A dedicated service layer for business logic is now fully implemented in the backend. The new `TrackedJobService` encapsulates all logic for updating tracked jobs, completing the backend's service-oriented architecture refactor.
*   **Data Lifecycle Activated:** The foundational database migration for the new `tracked_jobs` data lifecycle has been successfully executed. The backend and frontend have been updated to be fully compatible with the new schema, including the new status `ENUM`s and milestone timestamp fields.
*   **Frontend Architecture Refactored:** The main user dashboard component (`page.tsx`) has been completely refactored. All data-fetching logic has been extracted into a reusable custom hook (`useTrackedJobsApi`), and UI sections have been broken into smaller, dedicated components, significantly improving maintainability.
*   **Backend Architecture Refactored:** The backend has been completely refactored from a monolithic `app.py` into a scalable, service-oriented architecture.
*   **Frontend Stability Restored:** A critical infinite loop bug on the user dashboard has been resolved. This fixed core performance issues and resolved related UI bugs, such as the status dropdown not persisting its state.
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
1.  **Marketing: LinkedIn Company Profile:** Create a company profile on LinkedIn. (RICE: 10000)
2.  **UI/UX: Refine "Inactive Applications" Filter and Status Display:** Refine the filter to accurately reflect the new status ENUMs. (RICE: 8000)
3.  **Feature: Define & Verify New User Account Flow:** Define a comprehensive onboarding flow for new users. (RICE: 6000)
4.  **Feature: User-set Reminders & Next Action Notifications:** Implement the UI and backend logic to allow users to set reminders for their tracked jobs. (RICE: 4000)