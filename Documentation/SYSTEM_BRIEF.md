--- START OF FILE SYSTEM_BRIEF.md ---
# Transparent Talent: System Brief v1.8

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
*   **Application is stable and functional on its production domain.** The application now features a public-facing landing page for new user acquisition and a fully functional, authenticated user dashboard.
*   **New User Onboarding Improved:** Critical issues preventing new users from accessing the dashboard after sign-up have been resolved by ensuring a default user profile is automatically created. New users are now smoothly redirected to the profile page after signup, encouraging immediate profile completion.
*   **Architectural Hardening:** The data contract between the backend and the AI service has been standardized to `snake_case`, improving system-wide consistency and maintainability. Authentication is robust across original and new production domains.
*   **Core Feature Implemented:** The user dashboard now includes a sortable, filterable data table for the "My Job Tracker" section, significantly improving the user experience for managing tracked jobs.
*   **UI Refactor & Bug Fixes:** Resolved several UI bugs and refactored the frontend by decoupling the data table's column definitions, improving code quality and future scalability.
*   **Workflow Automation:** The user dashboard now intelligently automates the `applied_at` date for tracked jobs, setting it automatically when the status changes to 'Applied' and clearing it when changed from 'Applied', significantly streamlining user workflow. Frontend stability for data updates has also been improved.
*   **Pagination Implemented:** The "My Job Tracker" table now supports full pagination, including server-side data fetching and robust sorting, allowing efficient browsing of large datasets.
*   **Enhanced UI/UX:** Navigation has been polished; the header title links to the homepage, and the "Get Started" button on the landing page is now context-aware, directing users appropriately based on their login status.
*   **Data Integrity & AI Analysis Hardening:** The database schema for `job_analyses` has been significantly hardened to correctly support per-user job analyses and include protocol versioning. Backend logic has been updated to align with this new schema. Historical data with invalid job URLs has been identified and marked as 'Expired - Unreachable' to maintain a clean and accurate user dashboard.
*   **User Profile Management:** A comprehensive user profile management page has been implemented, allowing users to input and update their detailed career preferences, essential for personalized AI analysis. Associated backend API and navigation have been established. Frontend build stability for this page has been significantly improved by resolving module import errors.
*   **Work Style & Remote Preferences:** Users can now specify their `preferred_work_style` (e.g., On-site, Remote, Hybrid) and a general `is_remote_preferred` flag within their profile. The UI for these fields intelligently adapts to prevent conflicting inputs, and this information is now fed to the AI for improved job analysis relevance.
*   **Shadcn UI Integration:** Key UI components (labels, text areas, and select dropdowns) have been fully migrated to use Shadcn UI components across the profile and dashboard pages, enhancing visual consistency and project maintainability.

## 4. Immediate Backlog & Next Steps
1.  **Backend: Enhance Job Data for AI Matching:** Build out jobs profile to include location, remote status, and other pertinent details to assist with user:job matching. (RICE: 12000)
2.  **UI/UX: Add "Excited?" Favorite Column to Job Tracker:** Implement a true/false check column on the job tracker to allow users to favorite applications. (RICE: 7200)
3.  **UI/UX: Group Profile Fields into Collapsible Subsections:** Group profile fields into collapsable subsections. (RICE: 7200)
4.  **Feature: Define & Verify New User Account Flow:** Define and implement a comprehensive and verified onboarding flow for new user accounts beyond basic profile creation. (RICE: 6000)
5.  **Backend: Automated App Expiration:** Create a mechanism to automatically flag or hide job postings that are likely no longer valid after a certain period. (RICE: 4000)
6.  **UI/UX: User-Controlled Job Archiving & Expiration Notifications:** Implement a 2-step process to expire and hide tracked jobs, including user notifications for "ghosted" applications. (RICE: 3600)
7.  **UI/UX: 'Jobs for You' Module Restoration:** Ensure the "Jobs for You" module is present, visible, and sorted by relevancy on the user dashboard. (RICE: 3600)
8.  **UI: Transparent Relevance Scorecard:** Design and build the collapsible UI component that displays the detailed factors behind a job's score. (RICE: 3000)
9.  **Feature: Automated Application Status Expiration & Notifications:** Implement a mechanism to automatically flag or hide job postings that are likely no longer valid after a certain period, specifically for application statuses. (RICE: 2400)