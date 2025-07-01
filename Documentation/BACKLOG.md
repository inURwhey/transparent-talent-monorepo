# Transparent Talent: Product Backlog & Roadmap v1.24

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

---

## Tier 1: Foundational Infrastructure (Highest Priority)
| Feature | Epic | Reach | Impact | Confidence | Effort (months) | RICE Score | AI Model | Session Cost | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Backend: Update AI prompt to parse new structured job fields** | E01 | 1000 | 3 | 100% | 0.25 | **12000** | Flash | S | **To Do** |
| **Backend: Implement V1 JobMatchingService** | E01 | 1000 | 3 | 100% | 0.5 | **6000** | Pro Execute| M | **To Do** |
| **UI: Implement "Jobs For You" Dashboard Module** | E01 | 1000 | 3 | 100% | 0.5 | **6000** | Flash | M | **To Do** |
| **Feature: User-set Reminders & Next Action Notifications** | - | 1000 | 2 | 100% | 0.5 | **4000** | Flash | M | **To Do** |
| **Bugfix: Profile Save Fails Randomly (Likely Render Instance Spin-down)** | - | 1000 | 1 | 70% | 0.5 | **1400** | Flash | S | **To Do** |

## Tier 2: Core User Experience & Differentiation
| Feature | Epic | Reach | Impact | Confidence | Effort (months) | RICE Score | AI Model | Session Cost | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **UI/UX: Change "Desired Job Title" to "Desired Job Title(s)"** | E02 | 1000 | 1 | 100% | 0.05 | **20000** | N/A | S | **To Do** |
| **Marketing: LinkedIn Company Profile** | - | 1000 | 1 | 100% | 0.1 | **10000** | N/A | N/A | **To Do** |
| **UI/UX: Add filler text to "preferred work location" dropdown & conditional logic for remote preference.**| E02 | 1000 | 1 | 100% | 0.1 | **10000** | Flash | S | **To Do** |
| **Feature: Intelligent Duplicate Resume Handling (Reactivation/Discard)** | E02 | 1000 | 2 | 90% | 0.5 | **9000** | Flash | M | **To Do** |
| **UI/UX: Job Reactivation Flow for Inactive Tracked Jobs** | - | 1000 | 2 | 100% | 0.25 | **5000** | Flash | S | **To Do** |
| **Feature: Resume File Upload & Parsing** | E02 | 1000 | 3 | 90% | 0.5 | **5400** | Pro | M | **To Do** |
| **UI/UX: Modularize Profile Page Components** | E02 | 1000 | 2 | 100% | 0.5 | **4000** | Flash | M | **To Do** |
| **Feature: Bulk Reprocess Relevancy** | - | 1000 | 2 | 100% | 0.5 | **4000** | Flash | M | **To Do** |
| **UI/UX: Implement Autosave for Profile and Resume Pages** | E02 | 1000 | 2 | 90% | 0.5 | **3600** | Flash | M | **To Do** |
| **UI/UX: Enhance Profile Completion UX** | E02 | 1000 | 2 | 90% | 0.5 | **3600** | Flash | M | **To Do** |
| **UI/UX: Multi-step Archiving/Hiding Workflow for Tracked Jobs** | - | 1000 | 2 | 90% | 0.5 | **3600** | Flash | M | **To Do** |
| **UI: Transparent Relevance Scorecard** | E01 | 1000 | 3 | 100% | 1.0 | **3000** | Flash | M | **To Do** |
| **Feature: AI-Generated Application Assets (Resume/Cover Letter)** | - | 1000 | 3 | 90% | 1.0 | **2700** | Pro | L | **To Do** |
| **Feature: Bulk Job Submission (CSV/URLs)** | - | 500 | 3 | 90% | 1.0 | **1350** | Pro | M | **To Do** |
| **Feature: User Feedback Loop** | E01 | 1000 | 3 | 100% | 2.5 | **1200** | Pro | L | **To Do** |
| **Feature: Connect Resume Processing with Roles Data Type** | E02 | 1000 | 3 | 80% | 1.0 | **2400** | Pro | M | **To Do** |
| **UI/UX: Implement Dynamic Page Titles for SEO** | - | 1000 | 1 | 100% | 0.25 | **4000** | N/A | S | **To Do** |

*Note: Tier 3 and 4 items remain unchanged but would be linked to Epics as they are prioritized.*

---

## Completed Features & Bugfixes
### v0.37.0
| Feature/Bugfix | Original Tier | RICE Score | Epic |
| :--- | :--- | :--- | :--- |
| **UI: Update profile page with new salary fields** | Tier 1 | 12000 | E02 |

### Previous Versions
*Items from v0.36.0 and earlier are documented in the `CHANGELOG.md`.*