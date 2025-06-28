# Transparent Talent - Changelog

All notable changes to this project will be documented in this file.

## [v0.5.0] - 2025-06-28 - Public Landing Page & Middleware Hardening

This release introduces a public-facing landing page to create a logged-out experience and hardens the authentication middleware after a significant debugging and refactoring effort.

### Added
-   **Public Landing Page:** Implemented a new static landing page at the root route (`/`) to explain the product's value proposition to new and logged-out users.
-   **Developer Protocol:** Added a "Clerk Interaction Protocol" to the project's documentation to establish a stricter workflow for handling the high-risk Clerk frontend library.

### Changed
-   **Authentication Middleware:** Refactored the frontend `middleware.ts` to correctly support both public and protected routes using the Clerk v5 SDK. All routes are now protected by default, with the landing page and sign-in/sign-up pages explicitly made public.

### Fixed
-   **Clerk v5 Implementation:** Resolved a series of persistent build failures by correcting the Clerk middleware implementation. The code now uses the correct "opt-in to protection" model and the proper `auth.protect()` syntax, aligning it with official documentation.

## [v0.4.0] - 2025-06-28 - Production Authentication Fix & Refactor

This release resolves the critical authentication bug and makes the application fully functional. It involved a significant refactor of the backend authentication system to improve stability, transparency, and adherence to open standards.

### Fixed
-   **Critical `401 Unauthorized` Error:** Resolved the persistent authentication failure that blocked all backend API requests. The user dashboard is now fully operational.

### Changed
-   **Replaced Authentication Library:** Removed the `clerk-backend-api` dependency entirely. The backend now performs authentication manually using the standard `PyJWT` and `requests` libraries.
-   **Authentication Flow:** The authentication decorator (`@token_required`) now verifies JWTs by fetching public keys from Clerk's JWKS endpoint and validating standard claims (`iss`, `azp`) for improved security and transparency.

### Added
-   **New Environment Variables:** Added `CLERK_ISSUER_URL` and `CLERK_AUTHORIZED_PARTY` to the backend configuration to support the new manual verification flow.
-   **Robust Auth Debugging:** Added extensive, detailed logging to the `auth.py` module to significantly speed up troubleshooting of any future token validation issues.

### Removed
-   **Removed `clerk-backend-api`:** The unused and problematic Python library was removed from `requirements.txt`.

## [v0.3.1] - 2025-06-28 - Failed Authentication Bugfix Attempt

This release documents a significant but unsuccessful attempt to resolve the critical production authentication bug. While the issue persists, the debugging process revealed key insights into the unexpected behavior of the `clerk-backend-api` library, which will inform the next attempt.

### Changed
-   **Iterative Debugging on `auth.py`:** Multiple versions of the `token_required` decorator were deployed to diagnose a series of cascading errors. This process invalidated several common implementation patterns.

### Fixed
-   **Clerk Dashboard Misconfiguration:** Corrected a user-facing issue where a misconfigured "Restrictions" list was improperly blocking valid user sign-in attempts.

### Unresolved Issues
-   **Critical `401 Unauthorized` Error:** The root cause of the authentication failure remains. The latest logs indicate the `clerk.authenticate_request()` method is throwing a `TypeError: Clerk.authenticate_request() missing 1 required positional argument: 'options'`, even when provided with what appear to be the correct parameters. The exact expected structure for the `options` argument remains unknown.

## [v0.3.0] - 2025-06-27 - End-to-End User Authentication

This version implements a complete, secure authentication system across the entire application stack, from the frontend client to the backend API.

### Added
-   **User Authentication:** Integrated Clerk for robust user sign-up, sign-in, and session management across the full stack.
-   **Frontend Middleware:** Added `middleware.ts` to the Next.js app to protect all routes and enforce authentication.
-   **Backend Token Validation:** Created an `auth.py` decorator in the Flask backend to validate JWTs on all protected API endpoints.
-   **Clerk SDKs:** Added `@clerk/nextjs` to the frontend and `clerk-backend-api` to the backend.
-   **Database Migration:** Added a `clerk_user_id` column to the `users` table to link application data with the authentication provider.

### Changed
-   **API Security:** All backend endpoints in `app.py` were refactored to be protected by the `@token_required` decorator and to securely derive the user's identity from the session, removing user identifiers from URL parameters.
-   **Frontend Dashboard:** The main dashboard component was refactored to use modern, secure data-loading hooks (`useAuth`, `useUser`) instead of relying on URL parameters.
-   **Frontend Layout:** Modified `apps/frontend/app/layout.tsx` to include the `<ClerkProvider>` and user session controls (`<UserButton>`).

### Fixed
-   **Vercel Deployments:** Resolved a series of `MIDDLEWARE_INVOCATION_FAILED` and TypeScript build errors by correcting the Clerk middleware implementation and component props.
-   **Render Deployments:** Fixed numerous `ModuleNotFoundError` and `TypeError` crashes by correcting the Clerk python package name (`clerk-backend-api`), updating the import paths in `auth.py`, and aligning the Clerk client usage with the specific library version's requirements.
-   **Python Versioning:** Discovered and confirmed that the original Python version (3.13) was incompatible with the authentication libraries, necessitating a downgrade to a stable LTS version (3.12) for production deployments.

## [v0.2.0] - 2025-06-26 - Monorepo Migration & Production Deployment

This version marks the successful re-architecting of the project into a professional monorepo structure and the full deployment of all services to production hosting environments.

### Added
-   **`vercel.json`:** Created a Vercel configuration file to provide explicit build and routing instructions, ensuring successful deployment of the frontend application.
-   **`ARCHITECTURE.md`:** Added a dedicated document to formally describe the full-stack system architecture.

### Changed
-   **Repository Structure:** Migrated the entire codebase from two separate projects into a single monorepo, managed with pnpm workspaces and Turborepo.
-   **Frontend Deployment:** The Next.js frontend is now deployed to **Vercel** from the `apps/frontend` directory of the monorepo.
-   **Backend Deployment:** The Render deployment configuration was updated to correctly build and deploy the Flask API from the `apps/backend` directory of the monorepo.

### Fixed
-   Resolved multiple Git submodule issues that prevented proper version tracking of the frontend and backend applications.
-   Corrected conflicting `package-lock.json` and `next.config.ts` files that caused local and production build failures.
-   Systematically debugged and resolved a series of Vercel 404 deployment errors by correcting build outputs and implementing explicit routing rules.

## [v0.1.0] - 2025-06-26 - Initial MVP and Data Foundation

This initial version represents the successful transition from a manual, spreadsheet-based system to a functional full-stack web application with a robust data foundation.

### Added
-   **Initial Backend API (v1):** Deployed a Python Flask application to Render, serving user data and job information via a RESTful API.
-   **Job Tracker Functionality:** Implemented full CRUD (`GET`, `POST`, `PUT`, `DELETE`) endpoints for tracked jobs, allowing users to manage their application pipeline.
-   **Initial Frontend Dashboard (v1):** Developed a local Next.js application that successfully connects to the backend API to display user profiles, watchlists, job matches, and the interactive job tracker.
-   **Comprehensive Data Migration:**
    *   Successfully designed and executed a migration script to import all historical user and company data from **Bubble JSON exports** into the new PostgreSQL database.
    *   Successfully designed and executed a second, more complex migration script to parse, clean, and import all historical application data from multiple **CSV files** (`TT Opportunities`, `Greg Freed - Job Search`).
    *   Unified all disparate data sources into a single, relational database, creating a comprehensive foundation for all future features.

### Changed
-   **Upgraded Database:** Migrated from a conceptual file-based system to a production-grade **PostgreSQL** database hosted on Render.
-   **Enhanced Business Logic:** Refined API endpoints to filter out irrelevant job data and intelligently handle application status changes.

### Fixed
-   Resolved multiple Python dependency issues (`flask_cors`) to ensure stable deployment on Render.
-   Corrected and iteratively fixed database schema mismatches discovered during the complex data migration process.