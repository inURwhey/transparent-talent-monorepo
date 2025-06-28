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
*   **Architectural Hardening:** The data contract between the backend and the AI service has been standardized to `snake_case`, improving system-wide consistency and maintainability.
*   **Core Feature Implemented:** The user dashboard now includes a sortable, filterable data table for the "My Job Tracker" section, significantly improving the user experience for managing tracked jobs.
*   **UI Refactor & Bug Fixes:** Resolved several UI bugs and refactored the frontend by decoupling the data table's column definitions, improving code quality and future scalability.

## 4. Immediate Backlog & Next Steps
1.  **UI/UX: Transparent Relevance Scorecard:** Design and build the collapsible UI component that displays the detailed factors behind a job's score. (RICE: 3000)
2.  **Deployment: Production Domain:** Configure and deploy the application to a production-ready domain. (RICE: 4000)
3.  **Backend: Automated App Expiration:** Create a mechanism to automatically flag or hide job postings that are likely no longer valid after a certain period. (RICE: 4000)