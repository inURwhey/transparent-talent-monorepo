# Transparent Talent: Product Backlog & Roadmap v1.32

## Column Definitions
*   **AI Model:** The complexity required from the AI. (Flash, Pro [Breakdown/Execute], Creative, N/A)
*   **Session Cost:** The estimated AI Studio token budget required. (S, M, L)
*   **Epic:** The parent Epic this task belongs to.

---

## Epics
| ID | Epic | Description | Status |
|:---|:---|:---|:---|
| E01| **"Jobs For You" Module** | Implement an end-to-end job recommendation engine, from enhancing backend data to displaying ranked results on the user dashboard. | In Progress |
| E02| **New User Experience** | Refine and stabilize the entire new user journey, from sign-up through onboarding and profile completion. | In Progress |
| E03| **Monetization & Subscriptions** | Define and implement user subscription tiers to gate access to premium AI features. | Not Started |
| E04| **User Relationship Management** | Build a lightweight, integrated CRM for managing professional contacts and leveraging the user's network. | Not Started |
| E05| **System Lifecycles** | Formally define and document the state machines and lifecycles for core system entities (Users, Companies, Jobs) to guide future development. | Not Started |

---

## Tier 1: Foundational Infrastructure (Highest Priority)
| Feature | Epic | Reach | Impact | Confidence | Effort (months) | RICE Score | AI Model | Session Cost | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Architecture: Distinguish 'Unset' vs 'No Preference' in DB** | E02 | 1000 | 2 | 100% | 0.5 | **4000** | Pro Breakdown | M | **To Do** |
| **Backend: Re-process malformed job data** | - | 1000 | 2 | 100% | 0.5 | **4000** | Flash | S | **To Do** |
| **Bugfix: Profile Save Fails Randomly (Likely Render Instance Spin-down)** | - | 1000 | 1 | 70% | 0.5 | **1400** | Flash | S | **To Do** |

## Tier 2: Core User Experience & Differentiation
| Feature | Epic | Reach | Impact | Confidence | Effort (months) | RICE Score | AI Model | Session Cost | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Feature: Intelligent Duplicate Resume Handling (Reactivation/Discard)** | E02 | 1000 | 2 | 90% | 0.5 | **9000** | Flash | M | **To Do** |
| **UI/UX: Prompt Users with Incomplete Profiles to Update** | E02 | 1000 | 2 | 90% | 0.25 | **8000** | Flash | S | **To Do** |
| **Feature: Add Professional Designations/Certifications to Profile** | E02 | 1000 | 2 | 100% | 0.25 | **8000** | Flash | S | **To Do** |
| **Architecture: Regex-based JWT Audience Validation** | - | 1000 | 2 | 100% | 0.25 | **8000** | Flash | S | **To Do** |
| **Backend: Re-process incomplete company profiles** | E01 | 1000 | 2 | 100% | 0.25 | **8000** | Flash | S | **To Do** |
| **AI: Improve company research prompt & validation** | E01 | 1000 | 3 | 90% | 0.5 | **5400** | Creative | M | **To Do** |
| **Feature: Resume File Upload & Parsing** | E02 | 1000 | 3 | 90% | 0.5 | **5400** | Pro | M | **To Do** |
| **UI/UX: Job Reactivation Flow for Inactive Tracked Jobs** | - | 1000 | 2 | 100% | 0.25 | **5000** | Flash | S | **To Do** |
| **UI/UX: Company-centric profile view in tracker** | E01 | 1000 | 2 | 100% | 0.5 | **4000** | Flash | M | **To Do** |
| **Feature: Bulk Reprocess Relevancy** | - | 1000 | 2 | 100% | 0.5 | **4000** | Flash | M | **To Do** |
| **Feature: AI-powered Resume Change Detection** | E02 | 1000 | 2 | 90% | 0.5 | **3600** | Flash | M | **To Do** |
| **UI/UX: Implement Autosave for Profile and Resume Pages** | E02 | 1000 | 2 | 90% | 0.5 | **3600** | Flash | M | **To Do** |
| **UI/UX: Enhance Profile Completion UX** | E02 | 1000 | 2 | 90% | 0.5 | **3600** | Flash | M | **To Do** |
| **UI/UX: Multi-step Archiving/Hiding Workflow for Tracked Jobs** | - | 1000 | 2 | 90% | 0.5 | **3600** | Flash | M | **To Do** |
| **UI: Transparent Relevance Scorecard** | E01 | 1000 | 3 | 100% | 1.0 | **3000** | Flash | M | **To Do** |
| **Architecture: Implement 'AI Suggested Edits' and UI** | E02 | 1000 | 3 | 90% | 1.0 | **2700** | Pro Breakdown | L | **To Do** |
| **Architecture: Implement "Knowledge Gap" Enrichment Engine** | E01 | 1000 | 3 | 90% | 1.0 | **2700** | Pro Breakdown | L | **To Do** |

## Tier 3: New Features & Future Growth
| Feature | Epic | Reach | Impact | Confidence | Effort (months) | RICE Score | AI Model | Session Cost | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Feature (Premium): Exportable Prompts for Third-Party AI** | E03 | 200 | 2 | 100% | 0.1 | **4000** | Flash | S | **To Do** |
| **Feature: Contacts CRM (LinkedIn Import)** | E04 | 1000 | 3 | 90% | 0.75 | **3600** | Pro Execute| L | **To Do** |
| **Feature: Add Contract Work Preferences** | E02 | 1000 | 1 | 90% | 0.25 | **3600** | Flash | S | **To Do** |
| **Feature: Company Logos & Rich Content** | E01 | 1000 | 2 | 90% | 0.5 | **3600** | Flash | M | **To Do** |
| **Feature (Coaching): AI-Powered Interview Prep** | E03 | 1000 | 3 | 90% | 1.0 | **2700** | Pro | L | **To Do** |
| **Feature: User-Facing Application Artifact Generation (Resumes, Cover Letters)** | E03 | 1000 | 3 | 90% | 1.5 | **1800** | Creative | L | **To Do** |
| **Feature: User Feedback Loop** | E01 | 1000 | 3 | 100% | 2.5 | **1200** | Pro | L | **To Do** |
| **Feature: "Jobs For You" Pagination & Tabular View** | E01 | 1000 | 2 | 90% | 0.25 | **800** | Flash | S | **To Do** |
| **UI/UX: Clear Date Field in Next Action Date** | - | 1000 | 1 | 90% | 0.1 | **900** | Flash | S | **To Do** |
| **UI/UX: Restrict Next Action Date to Future Only** | - | 1000 | 1 | 90% | 0.1 | **900** | Flash | S | **To Do** |
| **UI/UX: Refine Job Tracker Table Layout** | - | 1000 | 2 | 90% | 0.25 | **1800** | Flash | S | **To Do** |

---

## Documentation & Architecture
| Task | Description | Priority | Epic |
|:---|:---|:---|:---|
| **Documentation: Define User Lifecycle** | Create `USER_LIFECYCLE.md` with a Mermaid diagram to map the user journey from visitor to fully onboarded and active user. | High | E05 |
| **Documentation: Create Style Guide** | Create `STYLE_GUIDE.md` to codify recurring design patterns, component usage, and UI/UX decisions to ensure consistency. | Medium | - |
| **Documentation: Define Company & Job Lifecycles** | Create documents and diagrams for how company and job entities are created, updated, and managed within the system. | Medium | E05 |

---

## Technical Debt & Research
| Task | Description | Priority |
|:---|:---|:---|
| **Tech Debt: Modularize backend routes** | Break down the monolithic `apps/backend/routes/jobs.py` into smaller, more manageable service calls and helper functions to improve readability and testability. | Medium |
| **Tech Debt: Differentiate `employment_records` and `roles`** | Analyze the purpose and usage of the `employment_records` and `roles` tables. Refactor or merge them to create a clear, single source of truth for a user's work history. | Medium |
| **Tech Debt: Improve Lightweight Scraper** | Enhance the simple title scraper to use more advanced techniques (e.g., CSS selectors, low-cost AI call) to improve the accuracy of company/title extraction for incomplete profiles. | Medium |
| **Research: Long-lived, user-specific AI context windows** | Investigate the feasibility and cost-effectiveness of using advanced AI APIs (like OpenAI's Assistants API) to maintain stateful, long-running conversations and context for individual users. | Low |
| **Tech Debt: Modernize JWT Validation Library** | Evaluate and potentially replace the current `PyJWT` library for token validation with a more modern alternative, such as Clerk's official backend SDK (`clerk-python`). | Low |
| **Bugfix: UI Update Delay for Job Tracker Fields** | The "Next Action Date" and "Next Action Notes" fields do not visually update immediately after changes are saved, despite successful backend persistence and frontend data refetch. This requires further investigation into React's reconciliation and `react-table`'s rendering pipeline. | High | - |

---

## Business & Marketing Initiatives
| Task | Description |
|:---|:---|
| **Marketing: LinkedIn Company Profile** | Create and maintain an official company profile on LinkedIn. |
| **BizDev: User Recruitment (Colleges, 'Never Search Alone')** | Establish partnerships or outreach programs with university career centers and job search communities to recruit early-adopter users. |
| **Marketing: Empathetic Outreach to Laid-off Employees** | Create and execute a marketing campaign that offers genuine help and resources to individuals recently affected by company layoffs. |
| **Promotion: Basic tier free for 2025 for all Never Search Alone council members** | Offer a promotional deal to a key partner community to drive early adoption and gather targeted feedback. |

---

## Completed Features & Bugfixes
| Feature/Bugfix | Original Tier | RICE Score |
| :--- | :--- | :--- |
| **Feature: User-set Reminders & Next Action Notifications** | Tier 1 | 4000 |
| **Feature: Enhanced Company Profiles & Research** | Tier 2 | 1200 |
| **Feature: Automated Company Data Enrichment** | Tier 2 | 5400 |