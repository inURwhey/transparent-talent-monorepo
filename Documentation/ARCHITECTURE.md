# Transparent Talent - System Architecture

Transparent Talent is architected as a modern, decoupled, three-tier full-stack application, augmented by a fourth external service for generative AI. This is a professional and highly scalable design.

![Transparent Talent Architecture Diagram](https://i.imgur.com/L1h2eU3.png)

## Tier 1: The Frontend (Client)

*   **Technology:** Next.js (built on React).
*   **Purpose:** This is the user-facing part of the application. It is responsible for rendering the User Interface (UI) in the browser, managing the visual state, and handling all user interactions.
*   **How it Works:** It operates as a Single Page Application (SPA). It does not contain any sensitive logic or secret keys. When it needs data or needs to perform an action, it makes asynchronous HTTP requests (API calls) to the Backend API.
*   **Deployment:** Deployed as a Next.js application on **Vercel**. Its deployment is automatically triggered by a git push to the main branch of the monorepo.

## Tier 2: The Backend (Server/API)

*   **Technology:** Python with the Flask framework.
*   **Purpose:** This is the "brain" of the application. It is responsible for all business logic, data processing, and security. It serves as the single, authoritative gateway to the database and other services.
*   **How it Works:** It exposes a RESTful API with specific endpoints (e.g., `/users/.../profile`, `/users/.../tracked-jobs`). It receives requests from the Frontend, validates them, interacts with the Database, calls external services like the Gemini API, and sends back structured data (JSON) as a response.
*   **Deployment:** Deployed as a web service on **Render**. It is connected to a production database and its deployment is automatically triggered by a git push to the main branch of the monorepo.

## Tier 3: The Database (Persistence Layer)

*   **Technology:** PostgreSQL.
*   **Purpose:** This is the application's permanent memory. It is responsible for storing all structured data in a reliable, organized, and efficient manner.
*   **How it Works:** It contains a relational schema with tables like `users`, `jobs`, `companies`, and `tracked_jobs`. The Backend is the only component that communicates directly with the database, executing SQL queries to create, read, update, and delete data. It is accessed securely via a `DATABASE_URL` environment variable.
*   **Deployment:** Hosted as a managed PostgreSQL instance on **Render**.

## External Service: Generative AI

*   **Technology:** Google Gemini API.
*   **Purpose:** This service acts as a specialized "co-processor" for complex, creative, or analytical tasks that are beyond the scope of traditional programming.
*   **How it Works:** The Backend API securely calls the Gemini API using a secret API key. The frontend never communicates directly with the AI service. The backend sends a carefully crafted prompt, receives the text/JSON response, parses it, and then integrates that data into the application's normal flow.