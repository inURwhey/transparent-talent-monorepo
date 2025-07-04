# Transparent Talent: System Brief v2.17

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
*   **Backend Stability Enhanced:** The recurring "Profile Save Fails Randomly" bug is no longer reproducible and is considered resolved, indicating improved backend stability, potentially due to Render environment behavior or previous architectural changes.
*   **Job Tracker UI/UX Stable:** The Job Tracker table has undergone significant stability and user experience improvements, including immediate UI updates for CRM fields, fixed date selection for future dates, and clean console output. (Note: The persistent table layout/overflow issue is acknowledged and moved to backlog).
*   **Strategic Roadmap Defined:** A comprehensive strategic roadmap has been integrated, detailing go-to-market, monetization, and phased product development towards the "Nielsen for Talent" vision.
*   **Structured User Preferences:** Critical user profile preference fields have been migrated to `ENUM` types in the database, enabling a precise distinction between unset fields and explicitly stated "No Preference." This is a foundational improvement for the core relevancy engine.
*   **CRM Reminders & Notes (Live):** The foundational CRM-like functionality has been implemented, allowing users to add "Next Action Date" and "Next Action Notes" to their tracked jobs. This enhances personal pipeline management.
*   **V1 Company Profiles (Live):** An end-to-end feature for company data is now live. The backend automatically researches new companies upon job submission. The frontend has been refactored into a modular architecture and now displays this AI-generated company data in an expandable "Company Snapshot" card within the job tracker, making the "Environment Fit" score transparent to the user.
*   **Onboarding Lifecycle Hardened:** The entire new user experience, from sign-up and job submission to profile completion, is stable and robust.
*   **Application is stable and functional on its production domain.**

## 4. Immediate Backlog & Next Steps
1.  **Backend: Re-process malformed job data:** Create an admin endpoint to clean up historical job data that was saved with placeholder titles. (RICE: 4000)
2.  **BI: Platform-wide Hiring Funnel Analytics:** Leverage new milestone timestamps for business intelligence. (RICE: 4000)
3.  **Feature: Intelligent Duplicate Resume Handling (Reactivation/Discard):** Implement logic to manage duplicate resume submissions. (RICE: 9000)
4.  **UI/UX: Prompt Users with Incomplete Profiles to Update:** Guide users to complete their profiles for better recommendations. (RICE: 8000)
5.  **Feature: Bulk Job URL Submission:** Allow users to submit multiple job URLs at once for tracking and analysis. (RICE: 8000)
6.  **Feature: Add Professional Designations/Certifications to Profile:** Expand user profile data. (RICE: 8000)
7.  **Architecture: Regex-based JWT Audience Validation:** Harden authentication security. (RICE: 8000)
8.  **Backend: Re-process incomplete company profiles:** Clean up and enrich historical company data. (RICE: 8000)
9.  **Feature: Proactive AI Job Sourcing & Screening:** Implement AI-driven proactive job search based on user profile. (RICE: 3600)
10. **Feature: Contacts CRM (V1: Manual Entry & Tracking):** Implement basic contact tracking with next-best-action. (RICE: 3600)
11. **Feature: AI-Assisted Application Artifact Generation (MVP: Cover Letter & Resume Strategy):** Provide AI assistance for application materials. (RICE: 1800)