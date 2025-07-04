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
*   **Application is Stable:** The ORM migration is complete, and all cascading bugs on the backend and frontend have been resolved. The application is deployed and functional.
*   **AI Features Blocked:** The application's core AI features (resume parsing, job analysis) are non-functional due to a persistent API error when communicating with Google Gemini. This is the top-priority issue.

## 4. Immediate Backlog & Known Critical Issues
### Known Critical Issues
*   **Gemini API Integration:** All AI-powered features are blocked due to a `400 Bad Request` or `404 Not Found` error when calling the Gemini API. The root cause is an incompatibility between the API endpoint version, the available models for the API key, and the request payload.

### Next Steps
1.  **Tech Debt: Resolve Gemini API Errors:** This is the highest priority task.
2.  **Feature: Resume File Upload & Parsing:** High-priority feature to allow users to easily rebuild their profiles.
3.  **Feature: User Account Deletion:** Implement a secure, cascading user account deletion feature.
4.  **UI/UX:** Provide an explicit error message to the user when resume parsing fails.
5.  **UI/UX:** Remove the automatic redirect after saving the user profile.