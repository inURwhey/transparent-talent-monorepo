# Transparent Talent: System Brief v1.4

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
*   **Authentication:** **Clerk**, integrated across the full stack.
*   **Architecture Style:** Decoupled three-tier application, managed in a **monorepo**.

## 3. Current Project Status
*   **Data Migration:** Complete. All historical data has been migrated into the PostgreSQL database.
*   **Backend API:** A functional v1 is deployed on Render, with all endpoints now secured by token-based authentication. The API routes have been refactored for security.
*   **Frontend UI:** A functional v1 dashboard is deployed to Vercel, with all pages protected by a full authentication flow. Data-fetching logic has been modernized.
*   **User Authentication:** Complete. End-to-end user authentication is implemented and deployed. Although a final runtime issue is preventing the dashboard from loading data, the foundational code, database migrations, and architecture are in place.

## 4. Immediate Backlog & Next Steps
1.  **Bugfix: Resolve Production Authentication:** The highest priority is to resolve the final runtime authentication error preventing the dashboard from loading user data.
2.  **UI/UX: Transparent Relevance Scorecard:** Design and build the collapsible UI component that displays the factors behind a job's score.
3.  **Feature: User Job Submission:** Allow users to submit a URL for a job to be analyzed by the system.
4.  **UI/UX: Tabular Job Tracker:** Convert the job tracker to a filterable, sortable table.