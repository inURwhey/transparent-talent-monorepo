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
*   **Automated Data Enrichment:** The system is now significantly more intelligent. It automatically researches new companies upon job submission, creating a rich profile of company data (industry, mission, etc.). This data is then fed directly into the core AI analysis prompt, substantially improving the accuracy of the "Environment Fit" calculation and strengthening the platform's primary value proposition.
*   **Onboarding Lifecycle Hardened:** The entire new user experience, from sign-up and job submission to profile completion, is stable and robust. Critical bugs related to data integrity, state synchronization, and edge cases (like re-tracking jobs or resume parsing overwriting data) have been resolved.
*   **"Jobs For You" Module (v1) Live:** A module on the user dashboard displays a ranked list of personalized job recommendations.
*   **Application is stable and functional on its production domain.**

## 4. Immediate Backlog & Next Steps
1.  **Architecture: Distinguish 'Unset' vs 'No Preference' in DB:** Migrate user profile preference fields from `TEXT` to `ENUM` types to differentiate between a field a user hasn't set versus one they explicitly have no preference for. This is critical for data integrity and improving the accuracy of the relevancy engine. (RICE: 4000)
2.  **Backend: Re-process malformed job data:** Create an admin endpoint to clean up historical job data that was saved with placeholder titles. (RICE: 4000)
3.  **Feature: User-set Reminders & Next Action Notifications:** Implement CRM-like functionality for users to set reminders for their tracked jobs. (RICE: 4000)