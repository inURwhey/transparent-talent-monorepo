# Transparent Talent: System Brief v2.14

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
*   **CRM Reminders & Notes (Live):** The foundational CRM-like functionality has been implemented, allowing users to add "Next Action Date" and "Next Action Notes" to their tracked jobs. This enhances personal pipeline management.
*   **V1 Company Profiles (Live):** An end-to-end feature for company data is now live. The backend automatically researches new companies upon job submission. The frontend has been refactored into a modular architecture and now displays this AI-generated company data in an expandable "Company Snapshot" card within the job tracker, making the "Environment Fit" score transparent to the user.
*   **Onboarding Lifecycle Hardened:** The entire new user experience, from sign-up and job submission to profile completion, is stable and robust.
*   **Application is stable and functional on its production domain.**

## 4. Immediate Backlog & Next Steps
1.  **Architecture: Distinguish 'Unset' vs 'No Preference' in DB:** Migrate user profile preference fields from `TEXT` to `ENUM` types to differentiate between a field a user hasn't set versus one they explicitly have no preference for. This is critical for data integrity and improving the accuracy of the relevancy engine. (RICE: 4000)
2.  **Backend: Re-process malformed job data:** Create an admin endpoint to clean up historical job data that was saved with placeholder titles. (RICE: 4000)
3.  **Bugfix: UI Update Delay for Job Tracker Fields:** The "Next Action Date" and "Next Action Notes" fields do not visually update immediately after changes are saved, despite successful backend persistence and frontend data refetch. This requires further investigation into React's reconciliation and `react-table`'s rendering pipeline. (Priority: High)