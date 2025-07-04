# Transparent Talent: System Brief v2.17

## 1. Core Vision & Business Model
*   **Problem:** The job market is inefficient, opaque, and biased.
*   **Short-Term Solution:** An AI-powered service for individual job seekers that uses a feedback-driven, consultative approach to provide clarity and systematically evaluate opportunities.
*   **Long-Term Vision ("Nielsen for Talent"):** Become a foundational, two-way transparency layer for the talent market by providing standardized, verified data for both candidates and businesses.
*   **Core Value Prop:** Replace subjective, keyword-driven hiring with explicit, multi-dimensional relevance calculations (`Position Relevance` + `Environment Fit`).

## 2. Technology Stack & Architecture
*   **Frontend:** Next.js (React) hosted on **Vercel**.
*   **Backend:** Python with **Flask**, hosted as a web service on **Render**. The backend now uses **Flask-SQLAlchemy** as its ORM and **Flask-Migrate** for database migrations.
*   **Database:** **PostgreSQL**, hosted on **Render**.
*   **AI Service:** Google **Gemini API**, called exclusively from the backend.
*   **Authentication:** **Clerk**, integrated with the frontend. Backend uses manual JWT verification.
*   **Architecture Style:** Decoupled three-tier application, managed in a **monorepo**. The backend now follows a service-oriented architecture with an application factory pattern.

## 3. Current Project Status
*   **Application is Stable and Functional:** The critical, system-wide bugs introduced during the Flask-SQLAlchemy ORM migration have been fully resolved. This involved a comprehensive refactoring of backend models, services, CORS configuration, and all frontend components to ensure the data contract is synchronized across the full stack. The application is now fully operational.
*   **Backend Data Layer Refactoring (Complete):** The migration of the backend from raw `psycopg2` calls to the Flask-SQLAlchemy ORM is functionally complete and stable. All core features are operational on the new architecture.
*   **User Data Preserved:** The migration was completed without data loss; user profile data was damaged during the process but has been restored and validated as functional.

## 4. Immediate Backlog & Known Critical Issues
### Known Critical Issues
*   **Gemini API Integration:** AI-powered features (resume parsing, job analysis) are currently failing due to a `404 Not Found` error when calling the Gemini API. This is the highest priority issue to resolve.

### Next Steps
1.  **Tech Debt: Resolve Gemini API 404 Errors:** Investigate and fix the Gemini API configuration.
2.  **Feature: Resume File Upload & Parsing:** This is now a high-priority feature to allow users to easily rebuild their profiles after the data damage during the migration.
3.  **Feature: User Account Deletion:** Implement a secure, cascading user account deletion feature.
4.  **Backend: Re-process malformed job data:** Create an admin endpoint to clean up historical job data.
5.  **BI: Platform-wide Hiring Funnel Analytics:** Leverage new milestone timestamps for business intelligence.