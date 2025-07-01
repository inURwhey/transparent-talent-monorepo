# Transparent Talent: System Brief v2.8

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
*   **AI Content Validation Implemented:** Backend now uses AI to classify if submitted text is a resume or job posting, saving tokens and improving user feedback.
*   **Robust Profile Parsing:** Resume parsing now includes intelligent post-processing validation for AI-generated profile fields, ensuring data integrity by discarding malformed values and preventing database errors.
*   **AI Input Validation Implemented:** Backend now validates the size of resume and job text inputs before sending to AI models, optimizing token usage.
*   **Job Submission Fully Functional:** The system can now successfully ingest new job URLs, perform AI analysis (including the new letter grade for `matrix_rating`), and save them to the database, resolving a critical blocking issue.
*   **Resume Versioning Implemented:** The backend now successfully saves and manages multiple versions of user-submitted resumes, marking only the latest as active, providing a foundation for resume history and more advanced features.
*   **Profile Dropdown Display Fixed:** The critical bug affecting dropdowns on the user profile page, which prevented saved values from being displayed correctly, has been resolved. This also eliminated associated console warnings and restored contextual placeholders.
*   **Profile Redirection Fixed:** The bug preventing users with incomplete profiles from being correctly redirected to the `/welcome` onboarding page has been resolved, ensuring a smoother initial user experience.
*   **Resume Versioning Architecture in Place:** The foundational database schema for storing historical resume submissions (`resume_submissions` table) has been successfully migrated to production. This deconstructs a large feature into smaller, manageable implementation tasks.
*   **End-to-End Onboarding Flow Stabilized:** The entire new user flow is now functional. This includes user sign-up, redirection to the `/welcome` page, successful resume parsing and profile creation, and final redirection to a complete and functional `/dashboard/profile` page.
*   **Production Authentication Hardened:** The application is now correctly configured with a Clerk Production Instance, including DNS, production API keys, and Google SSO settings. All backend routes now consistently handle user authentication context, resolving a series of cascading crashes.
*   **Application is stable and functional on its production domain.**

## 4. Immediate Backlog & Next Steps
1.  **Feature: Re-implement "Jobs For You" Dashboard Module:** Re-enable and refine the module that suggests jobs based on user preferences. (RICE: 6000)
2.  **UI/UX: Change "Desired Job Title" to "Desired Job Title(s)":** A simple text change on the profile page. (RICE: 20000)