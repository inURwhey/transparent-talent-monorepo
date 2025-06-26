# Transparent Talent: System Brief v1.3

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
*   **Architecture Style:** Decoupled three-tier application, managed in a **monorepo**.

## 3. Current Project Status
*   **Data Migration:** Complete. All historical data from Bubble JSON exports and various job search CSVs has been successfully migrated into the PostgreSQL database.
*   **Backend API:** A functional v1 is deployed on Render from the monorepo. It includes endpoints for user profiles, watchlists, job matches, and a full CRUD API for the `tracked_jobs` table.
*   **Frontend UI:** A functional v1 dashboard is deployed to **Vercel** from the monorepo. It successfully fetches and displays data from the live backend API.

## 4. Immediate Backlog & Next Steps
1.  **Security: Implement User Authentication:** Integrate a third-party auth service (e.g., Clerk).
2.  **UI/UX: Transparent Relevance Scorecard:** Design and build the collapsible UI component that displays the factors behind a job's score. **(Highest Priority Feature)**
3.  **UI/UX: Tabular Job Tracker:** Convert the job tracker to a filterable, sortable table.
4.  **Feature: User Feedback Loop:** Implement the "thumbs-up/down" feedback mechanism on job matches.