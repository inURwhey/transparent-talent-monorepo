# Transparent Talent: System Brief v2.7

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
*   **End-to-End Onboarding Flow Stabilized:** The entire new user flow is now functional. This includes user sign-up, redirection to the `/welcome` page, successful resume parsing and profile creation, and final redirection to a complete and functional `/dashboard/profile` page.
*   **Production Authentication Hardened:** The application is now correctly configured with a Clerk Production Instance, including DNS, production API keys, and Google SSO settings. All backend routes now consistently handle user authentication context, resolving a series of cascading crashes.
*   **Profile Page Fully Functional:** A critical bug causing the user profile page to be incomplete and hang for new users has been fixed. All sections are now fully rendered and functional.
*   **DevOps Workflow Enhanced:** A robust, automated workflow for full-stack preview environments has been established.
*   **User Geolocation:** Users can now add their geographic location to their profile via a browser's Geolocation API.
*   **Backend Service Layer Complete:** A dedicated service layer for business logic is now fully implemented in the backend.
*   **Application is stable and functional on its production domain.**

## 4. Immediate Backlog & Next Steps
1.  **Bugfix: Redirect empty profiles to /welcome:** Users with an account but no profile data are not redirected to the `/welcome` page from the dashboard. (RICE: 10000)
2.  **Bugfix: Dropdowns in Work Style section don't show selected value:** The dropdowns on the profile page do not correctly display the user's saved selection upon page load. (RICE: 10000)
3.  **Feature: Re-implement "Jobs For You" Dashboard Module:** Restore the AI-driven job recommendation module to the main user dashboard. (RICE: 6000)