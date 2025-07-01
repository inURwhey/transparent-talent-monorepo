# Transparent Talent: System Brief v2.13

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
*   **V1 Job Matching Service Implemented:** The backend now has a functional `GET /api/jobs/recommendations` endpoint that returns a ranked list of job suggestions based on a V1 matching algorithm. This service provides the API foundation for the "Jobs For You" dashboard module.
*   **Structured Job Data Ingestion Live:** The backend successfully extracts and stores structured data (salary range, experience years, modality, job level) from AI analysis into the `jobs` table.
*   **User Profile Salary Fields Updated:** The frontend UI for the user profile page now correctly handles structured integer inputs for desired minimum and maximum annual salary.
*   **Application is stable and functional on its production domain.** The end-to-end new user onboarding flow is stable, and all major UI and authentication bugs have been resolved.

## 4. Immediate Backlog & Next Steps
1.  **UI: Implement "Jobs For You" Dashboard Module:** Build the frontend component to display the job recommendations from the new API endpoint. (RICE: 6000)
2.  **Feature: User-set Reminders & Next Action Notifications:** Implement CRM-like functionality for users to set reminders for their tracked jobs. (RICE: 4000)
3.  **UI/UX: Change "Desired Job Title" to "Desired Job Title(s)":** A simple text change on the profile page. (RICE: 20000)