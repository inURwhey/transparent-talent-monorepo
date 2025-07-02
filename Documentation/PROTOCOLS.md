# Transparent Talent: Operational Protocols v3.0

## System Instructions (Core Operating Principles)
*   **Full-File Output Mandate:** When providing file content for replacement, the AI **must** output the *entire*, complete, and untruncated code. Abbreviating with comments is a critical failure.
*   **Grounded Hypothesis Mandate:** All hypotheses about system behavior **must** be grounded in data provided within the current session. The AI will not make assumptions about schemas, environment variables, or error causes and must ask for ground truth when it is not available.
*   **Clarification Mandate:** If a task description, backlog item, or user request is ambiguous, lacks sufficient detail, or implies a potentially problematic implementation choice, the AI **must** ask for clarification before proceeding.

---

## Developer Workflow & Quality Assurance

### Git Branching & Preview Protocol v1.0
*Objective:* To maintain a stable `main` branch and enable isolated, full-stack testing.
1.  **Start Work:** Create a descriptive feature branch (e.g., `feature/user-onboarding`, `bugfix/profile-save`). For backend changes, create a corresponding temporary Render service that auto-deploys from this branch.
2.  **During Development:** Use the Vercel preview deployment for full-stack testing. The backend is configured to automatically authorize these preview URLs.
3.  **Complete Work:** Create a Pull Request to `main`. After approval and merge, decommission the temporary Render service.

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

### Database Interaction Protocol v1.1
*   **Prime Directive:** **Never** assume a database table's structure.
*   **Workflow:** Before generating code that touches the database, **must** prompt the user for the `\d <table_name>` schema and sample data (`SELECT * ... LIMIT 10`). All generated code will strictly adhere to the provided schema.

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

### Self-Correction on Truncation Protocol v1.0
*   **Directive:** Before outputting a code block, perform a self-check for truncation markers (`...`). If found, stop, state the protocol violation, and regenerate the complete, untruncated file.