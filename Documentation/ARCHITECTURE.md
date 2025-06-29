# Transparent Talent - System Architecture

Transparent Talent is architected as a modern, decoupled, three-tier full-stack application, augmented by external services for authentication and generative AI. This is a professional and highly scalable design.

![Transparent Talent Architecture Diagram](https://i.imgur.com/L1h2eU3.png)

## Tier 1: The Frontend (Client)

*   **Technology:** Next.js (built on React).
*   **Purpose:** This is the user-facing part of the application. It is responsible for rendering the User Interface (UI), managing visual state, and handling user interactions.
*   **How it Works:** It operates as a Single Page Application (SPA). When it needs data or needs to perform an action, it makes asynchronous, token-authenticated HTTP requests (API calls) to the Backend API.
*   **Deployment:** Deployed as a Next.js application on **Vercel**. Its deployment is automatically triggered by a git push to the main branch of the monorepo.

## Tier 2: The Backend (Server/API)

*   **Technology:** Python with the Flask framework.
*   **Purpose:** This is the "brain" of the application. It is responsible for all business logic, data processing, and security. It serves as the single, authoritative gateway to the database and other services.
*   **How it Works:** It exposes a RESTful API with specific endpoints (e.g., `/api/users/profile`). It receives requests from the Frontend, validates the included JWT, interacts with the Database, calls external services, and sends back structured data (JSON) as a response.
*   **Deployment:** Deployed as a web service on **Render**. It is connected to a production database and its deployment is automatically triggered by a git push to the main branch of the monorepo.

## Tier 3: The Database (Persistence Layer)

*   **Technology:** PostgreSQL.
*   **Purpose:** This is the application's permanent memory. It is responsible for storing all structured data in a reliable, organized, and efficient manner.
*   **How it Works:** It contains a relational schema with tables like `users`, `jobs`, `companies`, `tracked_jobs`, and `user_profiles`. The Backend is the only component that communicates directly with the database.
*   **Deployment:** Hosted as a managed PostgreSQL instance on **Render**.

## External Service: Authentication

*   **Technology:** Clerk.
*   **Purpose:** Provides a complete, secure, and decoupled user management system.
*   **How it Works:** The frontend integrates Clerk's Next.js SDK to provide sign-in/sign-up UI and session management. After login, the frontend acquires a JWT. The backend performs manual, stateless JWT verification on every protected API request. It fetches Clerk's public keys from a standard JWKS endpoint, validates the token's signature and claims (such as issuer and authorized party), and ensures all actions are performed by an authenticated user. This approach avoids proprietary SDKs on the backend in favor of open standards.

## External Service: Generative AI

*   **Technology:** Google Gemini API.
*   **Purpose:** This service acts as a specialized "co-processor" for complex, creative, or analytical tasks.
*   **How it Works:** The Backend API securely calls the Gemini API using a secret API key. The frontend never communicates directly with the AI service. The backend sends a carefully crafted prompt (which now includes richer user profile context like work style and remote preferences) and integrates the response data into the application's normal flow.