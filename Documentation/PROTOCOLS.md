# Transparent Talent: Operational Protocols v1.8

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

### Clerk Interaction Protocol v1.0
*Objective:* To prevent debugging cycles and ensure correctness when modifying authentication code related to the `@clerk/nextjs` library.

*Trigger:* Any development task that requires creating or modifying Clerk-related code.

*Workflow:*
1.  **Ground Truth Request:** The AI will request the exact version of `@clerk/nextjs` from `pnpm-lock.yaml`, the complete code from the file(s) to be modified, and a link to the relevant official Clerk documentation page.
2.  **Verbal Plan:** The AI will state its plan, referencing the ground truth, and ask for user confirmation before generating code.
3.  **Minimal Diffs:** Code modifications will be proposed as minimal diffs or specific line-by-line instructions.

### Database Interaction Protocol v1.1
*Objective:* To prevent backend errors caused by incorrect assumptions about the database schema.
*Prime Directive:* The AI must **never** assume the structure of a database table.

*Workflow:*
1.  **Mandatory Schema Request:** Before generating any code that references a database table, the AI **must** first prompt the user to provide the `\d <table_name>` description for all relevant tables.
2.  **Grounded Code Generation:** The generated code will strictly adhere to the column names and types from the user-provided schema.

## Workflow Guide: How to Run Protocols
This workflow should be executed sequentially within a single chat session to maintain context.
1.  **Initiate Company & Lead Discovery (Protocol 1.4):** Start by providing the user's profile and resume and requesting a 'Master Target Company List' and 'Preliminary Job Leads'.
2.  **Initiate Preliminary Screening (Protocol 2.2):** From the list of leads generated in Step 1, select specific jobs to screen. The AI will apply the critical verification protocol to each.
3.  **Initiate Detailed Analysis (Protocol User-Driven v1.1):** For jobs that pass screening, provide the full job description and request a detailed analysis.

---

## Protocol 1.4: User-Profile Based Company & Lead Discovery
*Objective:* To identify relevant target companies and initial raw job postings based on a user's profile.
*AI Instructions:*
1.  Analyze user profile to extract key search criteria (titles, skills, industries, preferences, deal-breakers).
2.  Perform deep web searches for companies matching these criteria, excluding any companies on the user's "avoid" list.
3.  Compile a "Master Target Company List" with company name, website, careers page URL, and a rationale for targeting.
4.  Scan career pages and general job boards for these target companies to compile a list of "Preliminary Job Leads" (Company, Title, URL, Source).

## Protocol 2.2: Batch Job Preliminary Screening
*Objective:* To quickly evaluate a batch of job leads to determine if a full analysis is warranted.
*AI Instructions:* For each job lead:
1.  **Critical Verification:** Confirm the job posting is live and reliable, check for previous applications, verify company size, and check for hard "deal-breakers".
2.  **Decision:** Output a `PROCEED` or `DO NOT PROCEED` decision.
3.  **Output (if PROCEED):** Provide a single-line summary ready for staging.

## Protocol User-Driven Job Analysis v1.1
*Objective:* To conduct a comprehensive relevance analysis of a single job against a user's profile.
*AI Instructions:*
1.  **Re-Verification:** Briefly confirm the job is still live.
2.  **Position Relevance Scoring (0-50):** Evaluate alignment with user's core expertise, role scope, leadership tier, compensation, and career goals.
3.  **Environment Fit Scoring (0-50):** Evaluate alignment with company size, culture, team structure, and location/flexibility.
4.  **Synthesized Analysis:** Provide an estimated "Hiring Manager View," the final Matrix Rating, a 2-4 sentence summary, key qualification gaps, and recommended testimonials.

---
*(Protocols 6.0 and 7.0 remain unchanged)*