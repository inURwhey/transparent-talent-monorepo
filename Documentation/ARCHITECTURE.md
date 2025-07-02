# Transparent Talent - System Architecture

Transparent Talent is architected as a modern, decoupled, three-tier full-stack application, augmented by external services for authentication and generative AI. This is a professional and highly scalable design.

## Core Data Philosophy: User Truth vs. AI Interpretation
A foundational principle of the system is the separation of user-provided data from AI-generated interpretations.
*   **User as Source of Truth:** Data entered directly by a user into their profile is considered their ground truth and is never automatically overwritten.
*   **AI as Enrichment Layer:** AI processes, like resume parsing, serve to enrich the user's profile by filling in empty fields. The long-term vision is to evolve this into an "AI Suggested Edits" model, where the AI's interpretations are presented to the user for explicit approval before being saved, thus preserving both data sources.

## Tier 1: The Frontend (Client)

*   **Technology:** Next.js (React).
*   **Purpose:** This is the user-facing part of the application. It is responsible for rendering the User Interface (UI), managing visual state, and handling user interactions.
*   **How it Works:** It operates as a Single Page Application (SPA). When it needs data or needs to perform an action, it makes asynchronous, token-authenticated HTTP requests (API calls) to the Backend API.
*   **Deployment:** Deployed as a Next.js application on **Vercel**. Its production deployment is automatically triggered by a git push to the `main` branch. Preview deployments are automatically generated for all other feature branches, providing isolated testing environments.

## Tier 2: The Backend (Server/API)

*   **Technology:** Python with the Flask framework.
*   **Purpose:** This is the "brain" of the application. It is responsible for all business logic, data processing, and security. It serves as the single, authoritative gateway to the database and other services.
*   **How it Works:** It exposes a RESTful API with specific endpoints (e.g., `/api/users/profile`). It receives requests from the Frontend, validates the included JWT, interacts with the Database, calls external services, and sends back structured data (JSON) as a response.
*   **Data Lifecycle Management:** The business logic for core entities follows a strictly defined state machine to ensure data integrity and predictable behavior. For a detailed breakdown of these state machines, see the **[Data Lifecycle Management](DATA_LIFECYCLE.md)** document.
*   **Deployment:** Deployed as a web service on **Render**. It is connected to a production database and its deployment is automatically triggered by a git push to the `main` branch. Feature branch testing is supported by creating temporary, parallel backend services on Render that deploy from their respective branches.

## Tier 3: The Database (Persistence Layer)

*   **Technology:** PostgreSQL.
*   **Purpose:** This is the application's permanent memory. It is responsible for storing all structured data in a reliable, organized, and efficient manner.
*   **How it Works:** It contains a relational schema with tables like `users`, `jobs`, `companies`, `tracked_jobs`, and `user_profiles`. The Backend is the only component that communicates directly with the database.
*   **Deployment:** Hosted as a managed PostgreSQL instance on **Render**.

## External Service: Authentication

*   **Technology:** Clerk.
*   **Purpose:** Provides a complete, secure, and decoupled user management system.
*   **How it Works:** The frontend integrates Clerk's Next.js SDK to provide sign-in/sign-up UI and session management. After login, the frontend acquires a JWT. The backend performs manual, stateless JWT verification on every protected API request. It fetches Clerk's public keys from a standard JWKS endpoint, validates the token's signature and claims (such as issuer), and now securely validates the `azp` (authorized party) claim against both a static list of production URLs and a regex pattern for dynamic Vercel preview URLs. This approach avoids proprietary SDKs on the backend in favor of open standards.

## External Service: Generative AI

*   **Technology:** Google Gemini API.
*   **Purpose:** This service acts as a specialized "co-processor" for complex, creative, or analytical tasks.
*   **How it Works:** The Backend API securely calls the Gemini API using a secret API key. The frontend never communicates directly with the AI service. The backend sends a carefully crafted prompt (which now includes richer user profile context like work style and remote preferences) and integrates the response data into the application's normal flow.