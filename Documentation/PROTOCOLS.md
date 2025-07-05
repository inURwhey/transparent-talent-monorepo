# Transparent Talent: Operational Protocols v3.0

## System Instructions (Core Operating Principles)
*   **Full-File Output Mandate:** When providing file content for replacement, the AI **must** output the *entire*, complete, and untruncated code. Abbreviating with comments is a critical failure.
*   **Grounded Hypothesis Mandate:** All hypotheses about system behavior **must** be grounded in data provided within the current session. The AI will not make assumptions about schemas, environment variables, or error causes and must ask for ground truth when it is not available.
*   **Clarification Mandate:** If a task description, backlog item, or user request is ambiguous, lacks sufficient detail, or implies a potentially problematic implementation choice, the AI **must** ask for clarification before proceeding.

---

## Developer Workflow & Quality Assurance

### Dependency-Aware Modification Protocol v1.0
*Objective:* To prevent cascading bugs by ensuring modifications are made with full knowledge of their immediate upstream and downstream dependencies. This protocol bridges the gap between a single-file change and a major architectural refactor.
*   **Trigger:** When a file requested for modification either calls, or is called by, other services, routes, or models within the application.
*   **Workflow:**
    1.  **Acknowledge & Pause:** The AI will pause before generating code for the primary file. It will state: *"Before proceeding with the modification of `[File A]`, I must assess its direct dependencies to ensure system-wide consistency."*
    2.  **Identify & State Connections:** The AI will explicitly map the connections. For example:
        *   *"`profile_service.py` directly imports and relies on Enum definitions from `models.py`."*
        *   *"`jobs.py` (route) creates an instance of `job_service.py` and calls its methods."*
        *   *"`job_service.py` calls methods within `profile_service.py`."*
    3.  **Request Ground Truth for Impact Radius:** The AI will generate a list of all files in the immediate impact radius and request their contents. *"To prevent data contract violations or import errors, please provide the full, current source code for the following files: `[File B]`, `[File C]`, `[File D]`."*
    4.  **Proceed with Holistic Change:** Once the context is provided, the AI will generate the necessary changes for the *primary file* and, if necessary, suggest corresponding adjustments to the other files within the impact radius to maintain consistency.

// Commented out while preview environment is broken.
/* ### Git Branching & Preview Protocol v1.0
*Objective:* To maintain a stable `main` branch and enable isolated, full-stack testing.
1.  **Start Work:** Create a descriptive feature branch (e.g., `feature/user-onboarding`, `bugfix/profile-save`). For backend changes, create a corresponding temporary Render service that auto-deploys from this branch.
2.  **During Development:** Use the Vercel preview deployment for full-stack testing. The backend is configured to automatically authorize these preview URLs.
3.  **Complete Work:** Create a Pull Request to `main`. After approval and merge, decommission the temporary Render service. */

### Development Cycle Protocol v1.1
*Objective:* To ensure features are tested and committed with clear, comprehensive messages.
1.  **Code:** Generate the necessary code to complete a logical unit of work.
2.  **Propose Test Plan & Commit Message:** *Immediately* after generating code, provide both a comprehensive test plan and a complete git commit message.
3.  **Await Confirmation:** Instruct the user to deploy and test. Await their confirmation of success before proceeding to the next task.

### Test Plan Generation Protocol v1.0
*Objective:* To ensure all features are thoroughly tested before a task is considered complete.
*   **Trigger:** Immediately after a code generation step is completed.
*   **Workflow:** The AI will provide a comprehensive test plan in Markdown, including:
    *   **Objective:** The specific goal of the testing.
    *   **Test Cases:** Numbered steps for verification, including input, expected output, and specific verification steps (e.g., UI inspection, DB queries).
    *   **Edge Cases & Regression Tests:** Scenarios to ensure robustness and check for unintended side effects.

### Proactive Refactoring Suggestion Protocol v1.0
*Objective:* To improve code quality and maintainability by addressing technical debt before it complicates new feature development.
*   **Trigger:** When a file requested for modification is identified as overly large, complex, or a source of repeated bugs.
*   **Workflow:** Instead of proceeding with the modification, the AI will:
    1.  **Pause:** State that the file's complexity is a potential issue.
    2.  **Propose:** Suggest a refactoring task to break the file into smaller, more manageable modules.
    3.  **Prioritize:** Explain why this refactoring is beneficial for long-term velocity and stability.
    4.  **Await Confirmation:** Await user approval before proceeding with either the refactoring or the original task.

---

## Session & Context Management

### Session Budgeting & Checkpointing Protocol v1.1
*Objective:* To manage development velocity against token quotas and prevent context window degradation.
1.  **Budgeting:** Use the `Session Cost` (S/M/L) in the backlog to set expectations.
2.  **Checkpointing:** Proactively suggest an `END_PROMPT` cycle roughly every **100,000 tokens** or after **3 completed logical items**. This commits work and resets context.
    *   **Full `END_PROMPT`:** Full documentation update.
    *   **Soft Checkpoint:** Only `CHANGELOG.md` and new high-priority backlog items are updated.

### Task Handoff Protocol v1.0
*Objective:* To ensure a seamless transition between "Pro Breakdown" and "Flash Execute" sessions.
*   **Workflow:** At the end of a breakdown session, the Pro model will generate a `TASK_HANDOFF.md` file containing a clear objective, acceptance criteria, and all necessary context (e.g., SQL scripts, schema descriptions) for the execution model.

---

## Ground Truth & Interaction Protocols

### Gemini API Interaction Protocol v1.0
*   **Prime Directive:** Do not trust internal knowledge of the Gemini API. Its behavior can be inconsistent across versions and undocumented.
*   **Workflow:**
    1.  **Isolate & Verify:** Before debugging application code, **always** verify the intended API call works using an external tool like Postman. Use the `/api/admin/list-models` endpoint to get a list of available models.
    2.  **Establish Ground Truth:** The successful external request (including endpoint URL, headers, and body structure) becomes the ground truth for implementation.
    3.  **Replicate Exactly:** The application code must replicate the proven request structure exactly.
    4.  **Prioritize Stable Models:** Default to stable, versioned model names (e.g., `gemini-1.5-pro`) over aliases (e.g., `gemini-1.5-pro-latest`), as aliases have shown to be unreliable with certain API versions.
*   **Known Working Configuration (as of 2025-07-04):**
    *   **Endpoint:** `https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent`
    *   **Authentication:** `x-goog-api-key: {api_key}` in the request header.

### Database Interaction Protocol v1.1
*   **Prime Directive:** **Never** assume a database table's structure.
*   **Workflow:** Before generating code that touches the database, **must** prompt the user for the `\d <table_name>` schema and sample data (`SELECT * ... LIMIT 10`). All generated code will strictly adhere to the provided schema.
*   **Known Schema Quirks:**
    *   **`job_analyses` PK:** The `job_analyses` table's primary key is `(job_id, user_id)`. It does **not** have a separate `id` column. Queries to check for existence should use `SELECT 1` or `SELECT job_id`.

### Monorepo & CLI Interaction Protocol v1.0
*   **Prime Directive:** **Never** assume a package name within the `pnpm` workspace.
*   **Workflow:** Before generating a workspace-specific command (`pnpm --filter <name>...`), **must** prompt the user for the contents of the relevant `package.json` to get the correct package `name`.

### Clerk Interaction Protocol v1.0
*   **Prime Directive:** Do not trust internal knowledge of the Clerk library.
*   **Workflow:**
    1.  **Ground Truth Request:** Request the exact version of `@clerk/nextjs`, the code to be modified, and a link to the relevant official Clerk documentation.
    2.  **`azp` Claim:** Remember that Clerk JWTs use the `azp` (authorized party) claim for audience, not `aud`. Manual validation is required.

---

## Content Generation Mandates

### Changelog Output Protocol v1.0
*   **Directive:** When updating `CHANGELOG.md`, output **only the new version block**.

### Backlog Content Protocol v1.0
*   **Directive:** When updating `BACKLOG.md` during a full `END_PROMPT`, remove the "Completed" section entirely. Completed items live permanently in the `CHANGELOG.md`.

### Self-Correction on Abridgement Protocol v1.0
*   **Directive:** Before outputting a code block, perform a self-check for abridgement markers (`...`, `// ...`, `# ...`). If found, stop, state the protocol violation, and regenerate the complete, unabridged file.

### Architectural Change Impact Protocol v1.0
*Objective:* To prevent cascading failures after a major architectural change (e.g., ORM migration, auth system swap).
1.  **Identify Impact Radius:** Before beginning work, identify all code files and services that directly or indirectly depend on the system being changed.
2.  **Create SystemicTest Plan:** Create a test plan that explicitly includes verification steps for *every single file* within the impact radius identified in step 1.
3.  **Proactive Refactoring:** During implementation, if a file in the impact radius is only partially updated, proactively update the *entire file* to be consistent with the new architecture, even if it is outside the immediate scope of the task. Do not leave latent bugs.
4.  **Verify End-to-End:** After code changes are complete, testing must include a full, end-to-end user flow that touches all affected components (e.g., user signup -> profile completion -> job submission -> admin view).