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
*   **Application is stable and functional.** The application now features a public-facing landing page for new user acquisition.
*   **Core Feature Implemented:** The user dashboard now includes a sortable, filterable data table for the "My Job Tracker" section, significantly improving the user experience for managing tracked jobs.
*   **Critical Bug Fix:** Resolved a persistent data contract mismatch between the frontend and backend that caused the dashboard to fail to render. This has hardened the application's stability.
*   **User Dashboard:** The frontend dashboard successfully loads all user data (profile, job matches, tracked jobs) from the authenticated backend API and displays it in the appropriate components.

## 4. Immediate Backlog & Next Steps
1.  **Architecture: Data Contract Standardization:** Perform a one-time pass of the backend API endpoints to ensure all JSON responses strictly align with the database's naming conventions. (RICE: 24.0)
2.  **UI/UX: Transparent Relevance Scorecard:** Design and build the collapsible UI component that displays the detailed factors behind a job's score. (RICE: 3000)
3.  **Deployment: Production Domain:** Configure and deploy the application to a production-ready domain. (RICE: 4000)