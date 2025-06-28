# Session End & Documentation Update

## My Task
Please perform the following end-of-session tasks:

1.  **Summarize Accomplishments:** Based on our chat history for this session, provide a concise, 2-3 bullet point summary of the main technical and strategic tasks we completed.

2.  **Update Project Documentation:** Based on the summary from step 1 and the attached source files, perform the following updates:
    *   **Analyze Backlog Ideas:** Review the "Unrefined Ideas & Brainstorming" section of `BACKLOG.md`. For each item, analyze its purpose, assign it to a logical tier in the roadmap (with estimated RICE values), and remove it from the brainstorming section.
    *   **Update Changelog:** Create a new version entry in `CHANGELOG.md` reflecting the accomplishments. Use the summary from step 1 to create detailed "Added," "Changed," and "Fixed" sections.
    *   **Update Backlog Status & Structure:** In `BACKLOG.md`:
        *   Change the `Status` of the completed tasks from "To Do" to "Done" (if not already done).
        *   **Crucially, move all "Done" items from their respective Tier tables to the new "Completed Features & Bugfixes" section at the bottom of the file.**
        *   Within the "Completed Features & Bugfixes" section, group items by their completion version (from `CHANGELOG.md`), ordered in reverse chronological order (most recent version first).
        *   For each completed item, include its "Feature/Bugfix" name, "Original Tier", and "RICE Score". For small polish items not previously in the backlog (e.g., header link), mark "Original Tier" as "UI/UX Polish" and "RICE Score" as "N/A".
    *   **Update System Brief:** In `SYSTEM_BRIEF.md`, update the "Current Project Status" and "Immediate Backlog" sections.
    *   **Review Architecture:** Briefly review `ARCHITECTURE.md` and other documents for any necessary updates based on the changes made.

3.  **Final Output:**
    *   **For `CHANGELOG.md`:** Generate *only the new version block* for the latest changes. Do not reproduce the entire file.
    *   **For all other modified files (`BACKLOG.md`, `SYSTEM_BRIEF.md`, etc.):** Output the complete, updated text.
    *   Ensure all documents are consistent with one another.
    *   Output git commands to push the updated documentation.