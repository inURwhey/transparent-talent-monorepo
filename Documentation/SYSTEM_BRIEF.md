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
*   **"Jobs For You" Module (v1) Live:** A new module on the user dashboard now displays a ranked list of personalized job recommendations, fetched from a new backend matching service. Core functionality is live, with UI/UX polish pending.
*   **Intelligent Onboarding Flow:** The system now intelligently gates AI features based on profile completion. Users with incomplete profiles can track jobs but are shown CTAs to complete their profile to unlock AI analysis and recommendations, creating a more compelling user journey.
*   **Backend Stability Hardened:** Critical bugs related to data integrity, state synchronization, and edge cases (like re-tracking jobs) have been resolved, making the backend services significantly more robust.
*   **Application is stable and functional on its production domain.**

## 4. Immediate Backlog & Next Steps
1.  **Backend: Re-process malformed job data:** Create an admin endpoint to clean up historical job data that was saved with placeholder titles. (RICE: 4000)
2.  **Feature: User-set Reminders & Next Action Notifications:** Implement CRM-like functionality for users to set reminders for their tracked jobs. (RICE: 4000)
3.  **UI/UX: Change "Desired Job Title" to "Desired Job Title(s)":** A simple text change on the profile page. (RICE: 20000)