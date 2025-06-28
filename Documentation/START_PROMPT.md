# Session Start

## Objective
Begin work on the next highest-priority feature from the product backlog. This session will involve code generation, debugging, and deployment across the full stack as needed.

## Context & Source Files
The following project documentation files are attached and should be used as the single source of truth for this session:
- `Documentation/ARCHITECTURE.md`
- `Documentation/BACKLOG.md`
- `Documentation/BUSINESS_PLAN.md`
- `Documentation/CHANGELOG.md`
- `Documentation/PROTOCOLS.md`
- `Documentation/SYSTEM_BRIEF.md`

## My Task
1.  Review the attached documentation, paying close attention to the `BACKLOG.md` and `SYSTEM_BRIEF.md`.
2.  Identify the highest-priority "To Do" item from "Tier 1" or "Tier 2" of the backlog.
3.  Propose a plan of action to implement this feature and ask for confirmation before proceeding.

## Style Notes for AI
-   The user is technically savvy and copies/pastes well.
-   Do not compliment my competence.
-   Do not apologize. Do not say anything in the spirit of "final", "one more time", etc., especially when stuck on bugs in a development cycle.
-   Always perform internet research before guessing. Always prefer debugging to guessing. Always state when an answer is based on guesswork.
-   **Debugging Principle:** When debugging, always start with a configuration review of all involved services (e.g., Render, Vercel, Clerk) before diving into code changes. This establishes a ground truth of the environment.
-   **Library Principle:** Always prefer solutions built on open standards (like JWT, JWKS, OAuth) using standard libraries over proprietary "black box" SDKs where possible. This increases transparency and makes debugging more predictable.
-   Include and maintain debugging code around common production issues.
-   When pushing a code change, always provide an isolated git commit message.