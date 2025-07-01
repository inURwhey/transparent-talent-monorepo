# Transparent Talent: System Brief v2.12

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
*   **Structured Job Data Ingestion Live:** The backend now successfully extracts and stores new structured data (salary range, experience years, modality, job level) from AI analysis into the `jobs` table. This is a crucial step towards implementing job recommendations.
*   **User Profile Salary Fields Updated:** The frontend UI for the user profile page now correctly handles structured integer inputs for desired minimum and maximum annual salary, including visual formatting with commas.
*   **Job Matching Architecture Designed:** The foundational architecture for the "Jobs For You" recommendation engine is complete.
*   **User Profile Data Model Hardened:** The `user_profiles` table has been refactored to use structured integer columns for salary preferences.
*   **AI Content Validation Implemented:** Backend now uses AI to classify if submitted text is a resume or job posting.
*   **Resume Versioning Implemented:** The backend successfully saves and manages multiple versions of user-submitted resumes.
*   **Application is stable and functional on its production domain.** The end-to-end new user onboarding flow is stable, and all major UI and authentication bugs have been resolved.

## 4. Immediate Backlog & Next Steps
1.  **Backend: Implement V1 JobMatchingService:** Build the new service and API endpoint to generate ranked job recommendations for users. (RICE: 6000)
2.  **UI: Implement "Jobs For You" Dashboard Module:** Build the frontend component to display the job recommendations. (RICE: 6000)
3.  **UI/UX: Prompt Users with Incomplete Profiles to Update:** Guide users to fill out their profile to improve recommendations. (RICE: 8000)