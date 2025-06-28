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
*   **CRITICAL ISSUE:** The application is currently **not functional** due to a persistent authentication bug. The user dashboard fails to load data because all authenticated API requests are rejected by the backend with a `401 Unauthorized` error.
*   **Underlying Cause:** The `clerk-backend-api` library is throwing a `TypeError` at runtime, indicating its requirements for the `authenticate_request` method are not being met. The exact expected function signature and configuration remain unidentified despite extensive debugging.
*   **User Authentication:** The architectural components for authentication are in place, but are not working correctly in production. This is the highest priority issue to resolve.

## 4. Immediate Backlog & Next Steps
1.  **Bugfix: Resolve Production Authentication:** The highest priority remains to resolve the runtime authentication error preventing the dashboard from loading user data. All other work is blocked.
2.  **UI/UX: Transparent Relevance Scorecard:** Design and build the collapsible UI component that displays the factors behind a job's score.
3.  **Feature: User Job Submission:** Allow users to submit a URL for a job to be analyzed by the system.
4.  **UI/UX: Tabular Job Tracker:** Convert the job tracker to a filterable, sortable table.