# Transparent Talent: System Brief v1.5

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
*   **Authentication Hardened:** The frontend authentication middleware has been correctly implemented using the latest Clerk v5 standards, making the routing and security model more robust and reliable.
*   **User Dashboard:** The frontend dashboard successfully loads all user data (profile, job matches, tracked jobs) from the authenticated backend API.

## 4. Immediate Backlog & Next Steps
1.  **Feature: User Job Submission:** Allow users to submit a URL for a job to be analyzed by the system. (RICE: 6000)
2.  **UI/UX: Tabular Job Tracker:** Convert the job tracker to a filterable, sortable table. (RICE: 4000)
3.  **UI/UX: Transparent Relevance Scorecard:** Design and build the collapsible UI component that displays the factors behind a job's score. (RICE: 3000)