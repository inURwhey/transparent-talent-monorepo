# Transparent Talent: Operational Protocols v2.5

## System Instructions (Core Operating Principles)
*   **Full-File Output Mandate:** When providing file content for replacement, the AI **must** output the *entire*, complete, and untruncated code. Abbreviating with comments is a critical failure.
*   **Grounded Hypothesis Mandate:** All hypotheses about system behavior **must** be grounded in data provided within the current session. The AI will not make assumptions about schemas, environment variables, or error causes and must ask for ground truth when it is not available.
*   **Clarification Mandate:** If a task description, backlog item, or user request is ambiguous, lacks sufficient detail, or implies an implementation choice that could reasonably lead to multiple revisions, the AI **must** ask the user for clarification before generating code or proceeding.

## Future State Note
The ultimate goal for these protocols is to generate structured **JSON** output that can be directly consumed by our backend API. The current CSV/Sheet-based output is an intermediary step for the manual and semi-automated phases.

## Developer Workflow Protocols

### Git Branching & Preview Protocol v1.0 -- AS OF v2.3, BRANCHING ONLY WORKS ON THE bugfix BRANCH, not MAIN.
*Objective:* To maintain a stable `main` branch and enable isolated, full-stack testing of new features.
*Workflow:*
1.  **Start Work:**
    *   Ensure the local `main` branch is up-to-date (`git checkout main && git pull`).
    *   Create a descriptive feature branch from `main` (e.g., `feature/user-onboarding-flow`, `bugfix/refine-filter`).
    *   **For tasks requiring backend changes:** Create a new, temporary backend service on Render. Configure this service to auto-deploy from the new feature branch.
    *   **In Vercel:** Create a new `NEXT_PUBLIC_BACKEND_PREVIEW_URL` environment variable. Scope it to the "Preview" environment and set its value to the URL of the temporary Render service.
2.  **During Development:**
    *   Commit work to the feature branch.
    *   Use the Vercel preview deployment URL for testing the full-stack application.
    *   The backend's authentication logic will automatically authorize valid Vercel preview URLs via regex pattern matching. The Flask CORS configuration is set to allow requests from any origin for preview/development flexibility.
3.  **Complete Work:**
    *   Upon successful testing in the preview environment, create a Pull Request on GitHub from the feature branch to `main`.
    *   After the PR is reviewed and approved, merge it into the `main` branch.
    *   Delete the remote feature branch from GitHub.
    *   Locally, switch back to `main`, pull the latest changes, and delete the local feature branch (`git checkout main && git pull && git branch -d <branch-name>`).
    *   **Decommission the temporary Render service** to avoid unnecessary costs.
4.  **Abandon Work:**
    *   If a feature branch will not be merged, simply leave it in the remote repository for historical context.
    *   Delete the temporary Render service associated with the branch.

### Debugging Principle: Grounded Hypothesis
*Prime Directive:* All hypotheses about system behavior **must** be grounded in data provided within the current session (e.g., logs, schema descriptions, user-provided code). Guesswork is to be avoided. When new data invalidates a hypothesis, the AI must explicitly state: **"Hypothesis invalidated. Resetting assumptions and re-evaluating ground truth."**

### Monorepo Interaction Protocol v1.0
*Objective:* To prevent build and dependency installation errors caused by incorrect assumptions about package names within the pnpm workspace, and to ensure smooth CLI interactions across environments.
*Prime Directive:* The AI must **never** assume the `name` of a package within the `apps/*` directory. The AI **must** also be aware of the user's specific shell environment for CLI command generation.

*Workflow:*
1.  **Identify Need:** The AI identifies the need to run a workspace-specific command (e.g., `pnpm --filter <package-name> ...`) or a general CLI command for testing/debugging.
2.  **Environment Acknowledgment:** The AI explicitly acknowledges the user's current environment ("User is using a Windows environment with native `cmd` and `PowerShell`.")
3.  **Mandatory `package.json` Request:** Before generating any workspace-specific command, the AI **must** prompt the user to provide the full contents of the `package.json` file from the relevant application directory (e.g., `apps/frontend/package.json`).
4.  **Prioritize API Clients for Complex Requests:** For complex HTTP API requests (e.g., those with large JSON bodies, file content, or intricate headers), the AI **must** first suggest using a dedicated graphical API client like Postman or Insomnia, providing specific step-by-step instructions for its usage.
5.  **Grounded Command Generation (CLI):** If a CLI command is still required or requested, the AI will use the `name` property from the provided `package.json` to construct the correct `--filter` flag. For other CLI commands, the AI **must** generate them with robust escaping and syntax appropriate for the user's *specified* shell environment, or provide clear instructions for manual input/file redirection if shell limitations prevent a direct command.

### Frontend Development & Deployment Protocol v1.0
*Objective:* To ensure efficient and stable frontend development, mindful of Vercel's free tier deployment limits (approximately 100 deployments per 24 hours).
*Prime Directive:* Minimize pushes to the `main` branch that trigger production deployments. The AI **must** proactively internalize relevant parts of the knowledge base (documentation, best practices) for any technical or open-source framework in use before forming hypotheses or generating code.

*Workflow:*
1.  **Local First Development & Thorough QA:** All frontend changes **must** be thoroughly developed and tested locally using `pnpm dev` within `apps/frontend` before being committed or pushed. Ensure features are fully functional and error-free in the local environment.
2.  **Utilize Feature Branches & Preview Deployments:**
    *   Develop on dedicated feature branches (e.g., `git checkout -b feature/my-new-feature`).
    *   Push feature branches to GitHub to trigger Vercel's **preview deployments**. These deployments are intended for testing and review and typically have a separate or more lenient limit.
    *   **Only merge to `main` (triggering a production deployment) once a feature is complete, thoroughly tested in a preview deployment, and confirmed stable.**
3.  **Group Logical Changes:** When pushing to a feature branch, group related changes into logical commits. Avoid committing and pushing every tiny change individually.
4.  **Shadcn UI Component Installation:** When a new Shadcn UI component is required:
    *   Navigate to the `apps/frontend` directory.
    *   Run `npx shadcn@latest add <component-name>` (e.g., `npx shadcn@latest add collapsible`). The `shadcn-ui` CLI is deprecated.
    *   **Mandate: Always prefer to use official Shadcn UI components** over custom implementations or workarounds where a suitable Shadcn component exists. If a Shadcn component behaves unexpectedly, the first step is to consult its official documentation and examples for proper usage, especially regarding `value` props for controlled components (e.g., `Select` components often expect `""` to show a placeholder, not `undefined`).
    *   **Confirm successful installation locally** before proceeding with code that uses the new component or pushing changes.

### Task Handoff Protocol v1.0
*   **Objective:** To ensure a seamless transition of work from a "Pro Breakdown" session to a "Flash Execute" session by creating a self-contained, explicit set of instructions.
*   **Trigger:** At the conclusion of a "Pro Breakdown" session, immediately after the architectural work (like a DB migration) is complete and before the `END_PROMPT`.
*   **Workflow:**
    1.  **Acknowledge Breakdown Completion:** The Pro model will state that the architectural planning is complete.
    2.  **Generate Handoff Brief:** The Pro model will generate a new, temporary markdown document named `TASK_HANDOFF.md`. This document will contain:
        *   **Objective:** A clear, one-sentence goal for the task.
        *   **Acceptance Criteria:** A bulleted list of what must be true for the task to be considered complete.
        *   **Relevant Files:** A list of all files that need to be modified.
        *   **Contextual Snippets:** The exact SQL scripts that were run, and the `\d <table_name>` output for any modified tables. This provides the Flash model with all necessary schema information without needing the full chat history.
    3.  **Instruct User:** The Pro model will instruct the user to save this `TASK_HANDOFF.md` file and provide it as the *primary context* for the next Flash session.

### Clerk Interaction Protocol v1.0
*Objective:* To prevent debugging cycles and ensure correctness when modifying authentication code related to the `@clerk/nextjs` library.

*Trigger:* Any development task that requires creating or modifying Clerk-related code.

*Workflow:*
1.  **Ground Truth Request:** The AI will request the exact version of `@clerk/nextjs` from `pnpm-lock.yaml`, the complete code from the file(s) to be modified, and a link to the relevant official Clerk documentation page.
2.  **Verbal Plan:** The AI will state its plan, referencing the ground truth, and ask for user confirmation before generating code.
3.  **Minimal Diffs:** Code modifications will be proposed as minimal diffs or specific line-by-line instructions.
*   **JWT Claim Validation:** Be aware that Clerk issues JWTs with the `azp` (authorized party) claim for audience validation, not the standard `aud` (audience) claim. When using `PyJWT`'s `jwt.decode` function, **do not** use the `audience` parameter. Instead, manually validate the `claims.get('azp')` against `AUTHORIZED_PARTIES` to avoid `InvalidAudienceError` and prevent deployment failures.

### Database Interaction Protocol v1.1
*Objective:* To prevent backend errors caused by incorrect assumptions about the database schema and to ensure effective data inspection.
*Prime Directive:* The AI must **never** assume the structure of a database table. When AI output fields are destined for database `VARCHAR` columns, the AI **must** explicitly compare the potential length/format of AI-generated content against the column's `VARCHAR` limit. If a mismatch is likely, the AI **must** ask the user for clarification (e.g., "Would you prefer to increase the `VARCHAR` limit to `TEXT`, or should I add validation to truncate/discard non-conforming AI output?").

*Workflow:*
1.  **Mandatory Schema Request:** Before generating any code that references a database table, the AI **must** first prompt the user to provide the `\d <table_name>` description for all relevant tables.
2.  **Sample Data Request:** Along with schema requests, the AI **must** prompt the user to provide sample data from the table (e.g., `SELECT * FROM <table_name> LIMIT 10;`) to aid in understanding data characteristics for testing and development.
3.  **Grounded Code Generation:** The generated code will strictly adhere to the column names and types from the user-provided schema.

### Session Budgeting Protocol v1.1
*   **Objective:** To manage development velocity against the real-world constraints of token quotas and UI performance in the AI Studio environment.
*   **Ground Truth:** The user's account has a daily token quota for Pro models, assumed as of v2.3 to be 400,000 tokens per day. The AI Studio UI also suffers from performance degradation on very long-context conversations (e.g., >120k tokens), which acts as a practical limit for Flash model sessions. These factors, not API rate limits, are the primary constraints on development.
*   **Protocol:**
    1.  **Backlog Costing:** All items in `BACKLOG.md` will be assigned a `Session Cost` (S/M/L) that estimates the token budget required.
    2.  **Session Planning:** At the start of a session, the AI will reference the task's `Session Cost` to set expectations for what can be accomplished.
    3.  **Checkpointing:** The AI will proactively suggest an `END_PROMPT` cycle roughly every **100,000 tokens consumed or after 3 completed logical items/features**, whichever comes first. This serves as a logical checkpoint, committing the work and enabling context management.
        *   **Full `END_PROMPT` Cycle:** Triggers complete documentation updates (`SYSTEM_BRIEF.md` fully updated, `BACKLOG.md` fully cleaned).
        *   **Soft Checkpoint (`END_PROMPT` with `CHANGELOG.md` only):** Updates `CHANGELOG.md` with only the new version block, and `BACKLOG.md` is only updated to include any new, uncurated ideas that need to jump the line. This is for faster iterative cycles.
    4.  **Retroactive Costing:** At the end of a session, the user can provide the actual token usage. This data will be used to refine future `Session Cost` (S/M/L) estimates, creating a data-driven planning loop.

### Context Management & Session Scoping v1.0
*   **Objective:** To optimize development efficiency by matching the session's context length to the nature of the task.
*   **Prime Directive:** The AI will explicitly recommend a context strategy at the beginning of a work session.
*   **Workflow & Heuristics:**
    1.  **Task Assessment:** At the start of a new task, the AI will assess its nature based on the backlog and user request.
    2.  **Strategy Recommendation:**
        *   For **"Pro-level"** tasks, the AI will state: *"This is a complex task. I recommend we maintain a single, continuous context until it is complete."*
        *   For a batch of unrelated **"Flash-level"** tasks, the AI will state: *"These are discrete tasks. To optimize for cost and performance, I will treat each as a nearly independent request."*

### Development Cycle Protocol v1.0
*   **Objective:** To ensure that logical units of work are committed with clear, comprehensive messages at the appropriate time, aligning with the user's preferred commit workflow.
*   **Trigger:** The AI completes a series of file creation or modification steps that constitute a self-contained feature, refactor, or bugfix.
*   **Workflow:**
    1.  **Acknowledge Completion:** The AI will state that the coding phase for the logical unit is complete.
    2.  **Mandatory Commit Generation:** Before suggesting the next task or waiting for a deployment, the AI **must** provide a complete, well-formatted git commit message, including the `git add .` and `git commit -m "..."` commands.
    3.  **Await Confirmation:** The AI will then instruct the user to deploy the changes (implying a `git push` once local commit is done) and will wait for confirmation of success before proceeding.

### Full-File Output Protocol v1.0
*   **Objective:** To prevent bugs and ensure clarity by providing complete, untruncated file contents during development.
*   **Prime Directive:** When the AI is asked to provide the contents of a file for replacement, it **must** output the *entire*, complete, and untruncated contents of that file.
*   **Rationale:** Abbreviating file contents with comments like `...` is counterproductive.

### Backlog Content Protocol v1.0
*   **Objective:** To streamline the `BACKLOG.md` file and reduce token cost.
*   **Prime Directive:** When generating `BACKLOG.md` during an `END_PROMPT` cycle, the AI will perform the following:
    *   **Soft Checkpoint:** If the `END_PROMPT` is triggered as a soft checkpoint, the AI will only update `BACKLOG.md` to include any new "To Do" ideas that were curated during the session and need to be tiered/prioritized.
    *   **Full `END_PROMPT`:** If the `END_PROMPT` is a full cycle, the AI will only include items with a "To Do" status, removing the "Completed" section and moving "Done" items to the `CHANGELOG.md`'s completed section.

### Changelog Output Protocol v1.0
*   **Objective:** To optimize context window usage during `END_PROMPT` for `CHANGELOG.md`.
*   **Prime Directive:** When generating `CHANGELOG.md` during an `END_PROMPT` cycle (either soft or full), the AI **must** output *only the new version block* for the latest changes. It **must not** reproduce the entire file.

### Model Hand-off Protocol v1.0
*   **Objective:** To ensure the correct AI model is used for the task at hand.
*   **Protocol:** The AI will state when a task has become simple enough for a "Flash" model or if a "Flash" model is struggling and should escalate the task to a "Pro" model.

### Manual Save Checkpoint Protocol v1.0
*   **Objective:** To mitigate context loss from client-side failures.
*   **Protocol:** After a significant milestone (e.g., successful deployment), the AI will issue a direct instruction: **"Protocol: Please save this chat now to prevent context loss."**

## Workflow Guide: How to Run Protocols
This workflow should be executed sequentially within a single chat session to maintain context.
1.  **Initiate Company & Lead Discovery (Protocol 1.4):** Start by providing the user's profile and resume and requesting a 'Master Target Company List' and 'Preliminary Job Leads'.
2.  **Initiate Preliminary Screening (Protocol 2.2):** From the list of leads generated in Step 1, select specific jobs to screen. The AI will apply the critical verification protocol to each.
3.  **Initiate Detailed Analysis (Protocol User-Driven v1.1):** For jobs that pass screening, provide the full job description and request a detailed analysis.