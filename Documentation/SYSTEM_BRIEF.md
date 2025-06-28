# Transparent Talent: System Brief v1.7

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
*   **Architectural Hardening:** The data contract between the backend and the AI service has been standardized to `snake_case`, improving system-wide consistency and maintainability. Authentication is robust across original and new production domains.
*   **Core Feature Implemented:** The user dashboard now includes a sortable, filterable data table for the "My Job Tracker" section, significantly improving the user experience for managing tracked jobs.
*   **UI Refactor & Bug Fixes:** Resolved several UI bugs and refactored the frontend by decoupling the data table's column definitions, improving code quality and future scalability.
*   **Workflow Automation:** The user dashboard now intelligently automates the `applied_at` date for tracked jobs, setting it automatically when the status changes to 'Applied' and clearing it when changed from 'Applied', significantly streamlining user workflow. Frontend stability for data updates has also been improved.
*   **Pagination Implemented:** The "My Job Tracker" table now supports full pagination, including server-side data fetching and robust sorting, allowing efficient browsing of large datasets.

## 4. Immediate Backlog & Next Steps
1.  **Bugfix: New Account Dashboard Error:** Resolve the "An Error Occurred" issue when new users navigate to the dashboard immediately after sign-up. (RICE: 12000)
2.  **Backend: Automated App Expiration:** Create a mechanism to automatically flag or hide job postings that are likely no longer valid after a certain period. (RICE: 4000)
3.  **UI/UX: Context-Aware "Get Started" Button:** Refine the landing page's "Get Started" button behavior based on user login status. (RICE: 4000)
4.  **Feature: Define & Verify New User Account Flow:** Define and implement a comprehensive and verified onboarding flow for new user accounts. (RICE: 6000)
5.  **UI: Transparent Relevance Scorecard:** Design and build the collapsible UI component that displays the detailed factors behind a job's score. (RICE: 3000)
6.  **UI/UX: 'Jobs for You' Module Restoration:** Ensure the "Jobs for You" module is present, visible, and sorted by relevancy on the user dashboard. (RICE: 3600)