# Transparent Talent: Operational Protocols v1.5

## Future State Note
The ultimate goal for these protocols is to generate structured **JSON** output that can be directly consumed by our backend API. The current CSV/Sheet-based output is an intermediary step for the manual and semi-automated phases.

## Developer Workflow Protocols

### Clerk Interaction Protocol v1.0
*Objective:* To prevent debugging cycles and ensure correctness when modifying authentication code related to the `@clerk/nextjs` library, which has proven to be a high-risk dependency due to frequent breaking changes and unreliable AI knowledge.

*Trigger:* Any development task that requires creating or modifying Clerk-related code in the frontend application.

*Workflow:*
1.  **Explicit Declaration:** The user will declare the start of a "Clerk Session."
2.  **Ground Truth Request:** The AI will request the following from the user before proceeding:
    *   The exact version of `@clerk/nextjs` from `pnpm-lock.yaml`.
    *   The complete, current, and working code from the file(s) to be modified.
    *   A link to the most relevant official Clerk documentation page for the task.
3.  **Verbal Plan:** The AI will state its plan in plain English, referencing the ground truth, and ask for user confirmation before generating any code.
4.  **Diff-Based Changes:** Code modifications will be proposed as minimal diffs or specific line-by-line instructions rather than full file replacements to reduce the risk of re-introducing errors.
5.  **User Authority:** The user acts as the final authority, validating the AI's proposals against the official documentation. The AI's role is to assist, not to provide definitive, untested solutions.

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
1.  **Critical Verification:**
    *   Confirm the job posting is live and the source is reliable.
    *   Check for previous applications by the user to this company.
    *   Verify company size against user preferences.
    *   Check for any hard "deal-breakers" from the user's profile.
2.  **Decision:** Based on verification, output a `PROCEED` or `DO NOT PROCEED` decision.
3.  **Output (if PROCEED):** Provide a single-line summary ready for staging, including a preliminary relevance assessment.

## Protocol User-Driven Job Analysis v1.1
*Objective:* To conduct a comprehensive relevance analysis of a single job against a user's profile.
*AI Instructions:*
1.  **Re-Verification:** Briefly confirm the job is still live.
2.  **Position Relevance Scoring (0-50):** Evaluate alignment with user's core expertise, role scope, leadership tier, compensation, and career goals.
3.  **Environment Fit Scoring (0-50):** Evaluate alignment with company size, culture (based on web search of reviews), team structure, and location/flexibility.
4.  **Synthesized Analysis:**
    *   Provide an estimated "Hiring Manager View" (Strong, Possible, Stretch, Unlikely).
    *   Calculate the final Matrix Rating (A, B, C, etc.).
    *   Write a 2-4 sentence summary of the opportunity.
    *   List 2-3 key qualification gaps the user might have.
    *   Recommend 1-3 impactful testimonials from the user's resume.

## Account Onboarding & User Profile Protocol v1.2
*Objective:* To capture all necessary user data for analysis.
*Core Components:* A structured intake mechanism (e.g., a web form) that captures career goals, work preferences, skills, deal-breakers, industry preferences, and personality insights. This data populates a central user profile in the database and serves as the foundation for all other protocols.

---

## Protocol 6.0: User Feedback Analysis Protocol
*Objective:* To analyze user-provided feedback on job matches and suggest actionable improvements to their profile or the system's understanding.
*Trigger:* A user submits negative feedback (e.g., "thumbs-down") on a job match.
*AI Instructions:*
1.  **Ingest Context:** Retrieve the full analysis of the disliked job, the user's complete profile at the time of analysis, and the user's feedback text (if provided).
2.  **Identify the Mismatch:** Compare the job's attributes with the user's profile and feedback. Determine the most likely reason for the mismatch.
3.  **Formulate a Hypothesis:** State a clear hypothesis for the mismatch. (e.g., "Hypothesis: The user dislikes the 'FinTech' sub-sector, even though 'Technology' is a preferred industry.")
4.  **Suggest an Actionable Change:** Propose a specific, easy-to-accept change to the user's profile. (e.g., "I noticed you disliked this job. The company is in the 'FinTech' industry. Would you like me to add this to your 'Industries to Avoid' list to improve future recommendations? [Yes/No]").

---

## Protocol 7.0: Proactive Profile Anomaly Detection
*Objective:* To identify and surface inconsistencies between a user's stated preferences and their actions, prompting reflection and creating opportunities for strategic realignment.
*Trigger:* A periodic system scan or a key user action (e.g., adding a misaligned company to a watchlist).
*AI Instructions:*
1.  **Ingest User Data:** Retrieve the user's full profile, current watchlist, and tracked jobs.
2.  **Run Anomaly Heuristics:** Compare data sets to find meaningful inconsistencies (e.g., Goal vs. Action, Strengths vs. Targets, Deal-Breaker Violations).
3.  **Generate a Consultative Notification:** If an anomaly is detected, craft a helpful notification for the user.
    *   **Template:** "I noticed something interesting about your strategy. Your profile emphasizes [Stated Preference], but your recent activity, like [User Action], seems to point in a different direction. Would you like to: A) Update your profile preferences? B) Explore this with an AI assistant? C) Schedule a session with a career coach?"