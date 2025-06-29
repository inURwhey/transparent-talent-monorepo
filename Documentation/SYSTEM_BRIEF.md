# Transparent Talent: System Brief v2.0

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
*   **Backend Architecture Refactored:** The backend has been completely refactored from a monolithic `app.py` into a scalable, service-oriented architecture. This new structure separates concerns into dedicated layers for configuration, services, routes, and database management, significantly improving maintainability and testability.
*   **Frontend Stability Restored:** A critical infinite loop bug on the user dashboard has been resolved. This fixed core performance issues and resolved related UI bugs, such as the status dropdown not persisting its state.
*   **Architecture:** Formally defined and documented a comprehensive data lifecycle for tracked jobs in `DATA_LIFECYCLE.md`, creating a robust state machine that includes milestone timestamps, CRM-like functionality for next actions, and a foundation for future features like offer negotiation support and hiring funnel analytics.
*   **Application is stable and functional on its production domain.** The application now features a public-facing landing page for new user acquisition and a fully functional, authenticated user dashboard.

(The rest of the status items remain unchanged)

## 4. Immediate Backlog & Next Steps
1.  **Refactor: Modularize Frontend `dashboard/page.tsx`:** Deconstruct the main dashboard component into smaller, reusable sub-components and custom hooks to improve maintainability, state management, and testability. (RICE: 300)
2.  **Refactor: Separate `tracked_jobs.status` into `status` and `status_reason` columns (with ENUMs):** The first implementation step of the new Data Lifecycle definition. This involves a database migration and refactoring backend logic. (RICE: 4.0)
3.  **UI/UX: Refine "Inactive Applications" Filter and Status Display:** Refine the "Inactive Applications" filter to accurately reflect status categories like "Expired," "Rejected," "Withdrawn," and "Accepted." (RICE: 8000)
4.  **Feature: Define & Verify New User Account Flow:** Define and implement a comprehensive and verified onboarding flow for new user accounts beyond basic profile creation. (RICE: 6000)