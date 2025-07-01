# Transparent Talent: System Brief v2.11

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
*   **User Profile Salary Fields Updated:** The frontend UI for the user profile page now correctly handles structured integer inputs for desired minimum and maximum annual salary, including visual formatting with commas. This aligns with the recent backend database migration.
*   **Job Matching Architecture Designed:** The foundational architecture for the "Jobs For You" recommendation engine is complete. This includes the design for a new `JobMatchingService`, its V1 scoring algorithm, and the necessary database schema enhancements to the `jobs` table.
*   **User Profile Data Model Hardened:** The `user_profiles` table has been refactored to use structured integer columns (`desired_salary_min`, `desired_salary_max`) for salary preferences.
*   **AI Content Validation Implemented:** Backend now uses AI to classify if submitted text is a resume or job posting.
*   **Resume Versioning Implemented:** The backend successfully saves and manages multiple versions of user-submitted resumes.
*   **Application is stable and functional on its production domain.** The end-to-end new user onboarding flow is stable, and all major UI and authentication bugs have been resolved.

## 4. Immediate Backlog & Next Steps
1.  **Backend: Update AI prompt to parse new structured job fields:** Update the prompt in `job_service.py` to populate the new structured data columns in the `jobs` table. (RICE: 12000)
2.  **Backend: Implement V1 JobMatchingService:** Build the new service and API endpoint to generate ranked job recommendations for users. (RICE: 6000)
3.  **UI: Implement "Jobs For You" Dashboard Module:** Build the frontend component to display the job recommendations. (RICE: 6000)