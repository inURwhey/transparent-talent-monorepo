# Transparent Talent: Operational Protocols v2.1

## Future State Note
The ultimate goal for these protocols is to generate structured **JSON** output that can be directly consumed by our backend API. The current CSV/Sheet-based output is an intermediary step for the manual and semi-automated phases.

## Developer Workflow Protocols

### Debugging Principle: Grounded Hypothesis
*Prime Directive:* All hypotheses about system behavior **must** be grounded in data provided within the current session (e.g., logs, schema descriptions, user-provided code). Guesswork is to be avoided. When new data invalidates a hypothesis, the AI must explicitly state: **"Hypothesis invalidated. Resetting assumptions and re-evaluating ground truth."**

### Monorepo Interaction Protocol v1.0
*Objective:* To prevent build and dependency installation errors caused by incorrect assumptions about package names within the pnpm workspace.
*Prime Directive:* The AI must **never** assume the `name` of a package within the `apps/*` directory.

*Workflow:*
1.  **Identify Need:** The AI identifies the need to run a workspace-specific command (e.g., `pnpm --filter <package-name> ...`).
2.  **Mandatory `package.json` Request:** Before generating the command, the AI **must** prompt the user to provide the full contents of the `package.json` file from the relevant application directory (e.g., `apps/frontend/package.json`).
3.  **Grounded Command Generation:** The AI will use the `name` property from the provided `package.json` to construct the correct `--filter` flag and then present the full command to the user.

### Frontend Development & Deployment Protocol v1.0
*Objective:* To ensure efficient and stable frontend development, mindful of Vercel's free tier deployment limits (approximately 100 deployments per 24 hours).
*Prime Directive:* Minimize pushes to the `main` branch that trigger production deployments.

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
    *   **Confirm successful installation locally** before proceeding with code that uses the new component or pushing changes.
5.  **Clarification for Ambiguity:** If a task involves an implementation choice that is not explicitly specified (e.g., UI default state, specific styling, handling of edge cases), and a "best guess" could reasonably lead to multiple revisions or deployments, the AI **must** ask the user for clarification before generating code.

### Clerk Interaction Protocol v1.0
*Objective:* To prevent debugging cycles and ensure correctness when modifying authentication code related to the `@clerk/nextjs` library.

*Trigger:* Any development task that requires creating or modifying Clerk-related code.

*Workflow:*
1.  **Ground Truth Request:** The AI will request the exact version of `@clerk/nextjs` from `pnpm-lock.yaml`, the complete code from the file(s) to be modified, and a link to the relevant official Clerk documentation page.
2.  **Verbal Plan:** The AI will state its plan, referencing the ground truth, and ask for user confirmation before generating code.
3.  **Minimal Diffs:** Code modifications will be proposed as minimal diffs or specific line-by-line instructions.
*   **JWT Claim Validation:** Be aware that Clerk issues JWTs with the `azp` (authorized party) claim for audience validation, not the standard `aud` (audience) claim. When using `PyJWT`'s `jwt.decode` function, **do not** use the `audience` parameter. Instead, manually validate the `claims.get('azp')` against `AUTHORIZED_PARTIES` to avoid `InvalidAudienceError` and prevent deployment failures.

### Database Interaction Protocol v1.1
*Objective:* To prevent backend errors caused by incorrect assumptions about the database schema.
*Prime Directive:* The AI must **never** assume the structure of a database table.

*Workflow:*
1.  **Mandatory Schema Request:** Before generating any code that references a database table, the AI **must** first prompt the user to provide the `\d <table_name>` description for all relevant tables.
2.  **Grounded Code Generation:** The generated code will strictly adhere to the column names and types from the user-provided schema.

### Session Budgeting Protocol v1.0
*   **Objective:** To manage development velocity against the real-world constraint of daily token quotas in the AI Studio environment.
*   **Ground Truth:** The user's account has a daily token quota for Pro models. The AI Studio UI also suffers from performance degradation on very long-context conversations (e.g., >120k tokens). These factors, not API rate limits, are the primary constraints on development.
*   **Protocol:**
    1.  **Backlog Costing:** All items in `BACKLOG.md` will be assigned a `Session Cost` (S/M/L) that estimates the token budget required.
    2.  **Session Planning:** At the start of a session, the AI will reference the task's `Session Cost` to set expectations for what can be accomplished within the daily quota.
    3.  **Checkpointing:** For `L` (Large) cost tasks, the AI will proactively suggest using an `END_PROMPT` cycle to serve as a logical checkpoint, committing the work and resetting the session's token count to avoid UI lag.

### Context Management & Session Scoping v1.0
*   **Objective:** To optimize development efficiency by matching the session's context length to the nature of the task.
*   **Prime Directive:** The AI will explicitly recommend a context strategy at the beginning of a work session.
*   **Workflow & Heuristics:**
    1.  **Task Assessment:** At the start of a new task, the AI will assess its nature based on the backlog and user request.
    2.  **Strategy Recommendation:**
        *   For **"Pro-level"** tasks, the AI will state: *"This is a complex task. I recommend we maintain a single, continuous context until it is complete."*
        *   For a batch of unrelated **"Flash-level"** tasks, the AI will state: *"These are discrete tasks. To optimize for cost and performance, I will treat each as a nearly independent request."*

### Development Cycle Protocol v1.0
*   **Objective:** To ensure that logical units of work are committed with clear, comprehensive messages at the appropriate time.
*   **Trigger:** The AI completes a series of file creation or modification steps that constitute a self-contained feature, refactor, or bugfix.
*   **Workflow:**
    1.  **Acknowledge Completion:** The AI will state that the coding phase for the logical unit is complete.
    2.  **Mandatory Commit Generation:** Before suggesting the next task or waiting for a deployment, the AI **must** provide a complete, well-formatted git commit message.
    3.  **Await Confirmation:** The AI will then instruct the user to commit and deploy the changes and will wait for confirmation of success before proceeding.

### Full-File Output Protocol v1.0
*   **Objective:** To prevent bugs and ensure clarity by providing complete, untruncated file contents during development.
*   **Prime Directive:** When the AI is asked to provide the contents of a file for replacement, it **must** output the *entire*, complete, and untruncated contents of that file.
*   **Rationale:** Abbreviating file contents with comments like `...` is counterproductive.

### Backlog Content Protocol v1.0
*   **Objective:** To streamline the `BACKLOG.md` file and reduce token cost.
*   **Prime Directive:** When generating `BACKLOG.md` during an `END_PROMPT`, the AI will only include items with a "To Do" status, removing the "Completed" section.
*   **Rationale:** The `CHANGELOG.md` is the official historical record. The completed list in the backlog is redundant and adds unnecessary token overhead.

## Workflow Guide: How to Run Protocols
This workflow should be executed sequentially within a single chat session to maintain context.
1.  **Initiate Company & Lead Discovery (Protocol 1.4):** Start by providing the user's profile and resume and requesting a 'Master Target Company List' and 'Preliminary Job Leads'.
2.  **Initiate Preliminary Screening (Protocol 2.2):** From the list of leads generated in Step 1, select specific jobs to screen. The AI will apply the critical verification protocol to each.
3.  **Initiate Detailed Analysis (Protocol User-Driven v1.1):** For jobs that pass screening, provide the full job description and request a detailed analysis.

## Code Generation Protocols
*   **Full File Replacement vs. Targeted Changes:**
    *   **Full File Replacement:** For changes involving adding or removing multiple functions/routes; significant restructuring or refactoring of existing code; modifying a TypeScript interface or Python data structure that affects multiple parts of the file; or addressing complex bugs where a full context is crucial.
    *   **Targeted Changes:** For isolated changes that are a single line modification; adding or removing a single import statement; changing a literal value (e.g., a constant); or adding a single, small, self-contained `if` or `else` block.