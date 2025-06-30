# Transparent Talent: Product Backlog & Roadmap v1.17

## Unrefined Ideas & Brainstorming
*This section is an inbox for raw ideas. During a "Session Summary" they will be refined, scored, and moved into the prioritized backlog below.*

---

## Column Definitions

### AI Model
The "AI Model" column indicates the estimated complexity and nuance required from the AI assistant to generate and debug the code for a given feature.

*   **Flash:** The task is straightforward, involves well-defined patterns, and requires minimal nuanced understanding.
*   **Pro:** The task is complex, requires deeper contextual understanding, advanced debugging, or significant architectural decisions.
*   **N/A:** The task is primarily conceptual or manual.

### Session Cost
The "Session Cost" column estimates the AI Studio session token budget required to complete the task, which is the primary constraint on development velocity.

*   **S (Small):** < 40k tokens. A task that can be completed quickly with minimal context.
*   **M (Medium):** 40k - 80k tokens. A standard feature or refactoring task.
*   **L (Large):** 80k - 120k+ tokens. A complex architectural task or feature epic.

---

## Tier 1: Foundational Infrastructure (Highest Priority)
| Feature | Reach | Impact | Confidence | Effort (months) | RICE Score | AI Model | Session Cost | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Feature: User-set Reminders & Next Action Notifications** | 1000 | 2 | 100% | 0.5 | **4000** | Flash | M | **To Do** |


## Tier 2: Core User Experience & Differentiation
| Feature | Reach | Impact | Confidence | Effort (months) | RICE Score | AI Model | Session Cost | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Marketing: LinkedIn Company Profile** | 1000 | 1 | 100% | 0.1 | **10000** | N/A | N/A | **To Do** |
| **UI/UX: Refine "Inactive Applications" Filter and Status Display** | 1000 | 2 | 100% | 0.25 | **8000** | Flash | S | **To Do** |
| **Feature: Define & Verify New User Account Flow** | 1000 | 3 | 100% | 0.5 | **6000** | Pro | L | **To Do** |
| **Feature: Geocoding for typed locations** | 1000 | 1 | 100% | 0.25 | **4000** | Flash | M | **To Do** |
| **Feature: Reverse Geocoding for selected locations** | 1000 | 1 | 100% | 0.25 | **4000** | Flash | M | **To Do** |
| **UI/UX: Multi-step Archiving/Hiding Workflow for Tracked Jobs** | 1000 | 2 | 90% | 0.5 | **3600** | Flash | M | **To Do** |
| **UI/UX: 'Jobs for You' Module Restoration** | 1000 | 3 | 90% | 0.75 | **3600** | Flash | S | **To Do** |
| **UI: Transparent Relevance Scorecard** | 1000 | 3 | 100% | 1.0 | **3000** | Flash | M | **To Do** |
| **Feature: Bulk Job Submission (CSV/URLs)** | 500 | 3 | 90% | 1.0 | **1350** | Pro | M | **To Do** |
| **Feature: User Feedback Loop** | 1000 | 3 | 100% | 2.5 | **1200** | Pro | L | **To Do** |

## Tier 3: AI & System Intelligence (Mid-Term)
| Feature | Reach | Impact | Confidence | Effort (months) | RICE Score | AI Model | Session Cost | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Backend: Enhance Job Data for AI Matching** | 1000 | 3 | 100% | 0.5 | **12000** | Pro | M | **To Do** |
| **Feature: Instant Analysis for Known Jobs**| 1000 | 2 | 100% | 0.5 | **4000** | Pro | L | **To Do** |
| **Feature: Cascading Expiration from Job Posting to Applications** | 1000 | 3 | 80% | 1.0 | **2400** | Pro | M | **To Do** |
| **Automation: Tiered Job Analysis (Lightweight Pre-Screening + Detailed AI)** | 1000 | 3 | 90% | 1.5 | **1800** | Pro | L | **To Do** |
| **UI/UX: Complex Notification System for Job Expiration** | 1000 | 2 | 90% | 1.0 | **1800** | Pro | L | **To Do** |
| **Feature: AI-Assisted Offer Negotiation** | 1000 | 3 | 90% | 1.5 | **1800** | Pro | L | **To Do** |
| **Feature: LinkedIn Profile/Resume Content Extraction & AI Parsing** | 1000 | 3 | 80% | 1.5 | **1600** | Pro | L | **To Do** |
| **Automation: Full API Job Analysis**| 1000 | 3 | 90% | 2.0 | **1350** | Pro | L | **To Do** |
| **Feature: Proactive Anomaly Detection**| 1000 | 3 | 90% | 2.5 | **1080** | Pro | L | **To Do** |
| **Feature: "Transparent Rejection"**| 1000 | 3 | 80% | 2.0 | **1200** | Pro | M | **To Do** |
| **Feature: Detailed Interview Stage Tracking (w/ Email/Calendar)** | 1000 | 3 | 80% | 2.0 | **1200** | Pro | L | **To Do** |
| **Feature: Automated Job Sourcing (Email/Platform Integration)** | 1000 | 2 | 90% | 0.75 | **900** | Pro | M | **To Do** |
| **Documentation: Codify Industry Standards in Protocols** | 1 | 3 | 90% | 0.25 | **10.8** | N/A | S | **To Do** |
| **Feature: "User News" Sourcing** | 1000 | 2 | 90% | 2.0 | **900** | Pro | M | **To Do** |
| **AI: Multi-Model Verification**| 1000 | 2 | 90% | 2.0 | **900** | Pro | M | **To Do** |
| **Feature: Verifiable Outcomes**| 1000 | 3 | 80% | 3.0 | **800** | Pro | L | **To Do** |
| **Backend: Automated News Sourcing** | 1000 | 1 | 90% | 2.0 | **450** | Pro | L | **To Do** |
| **Backend: System-Wide Staleness Logic** | 1000 | 1 | 100% | 0.5 | **2000** | Pro | M | **To Do** |
| **Feature: Browser Extension** | 500 | 2 | 80% | 3.0 | **267** | Pro | L | **To Do** |
| **AI: Full Data Leverage Mandate** | 1 | 3 | 90% | 1.0 | **2.7** | N/A | S | **To Do** |
| **AI: Automated Prompt QA System** | 1 | 3 | 80% | 3.0 | **0.8** | Pro | L | **To Do** |
| **Backend: DB-Driven AI Protocols** | 1 | 2 | 100% | 0.5 | **4.0** | Pro | M | **To Do** |

## Tier 4: Future Vision & Long-Term bets
| Feature | Reach | Impact | Confidence | Effort (months) | RICE Score | AI Model | Session Cost | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Infra: Background Jobs w/ Redis** | 1000 | 2 | 100% | 1.5 | **1333** | Pro | L | **To Do** |
| **Platform: Business Certification** | 5000 | 3 | 50% | 6.0 | **1250** | N/A | N/A | **To Do** |
| **Platform: System-Wide Analysis from User Submissions**| 1000 | 3 | 80% | 4.0 | **600** | Pro | L | **To Do** |
| **AI: User & Job Clustering for Proactive Matching** | 1000 | 3 | 70% | 4.0 | **525** | Pro | L | **To Do** |
| **Platform: System-Wide Relevance Calc**| 1000 | 3 | 90% | 6.0 | **450** | Pro | L | **To Do** |
| **Business: Tier AI Features by Model Cost/Capability** | 200 | 1 | 80% | 0.5 | **320** | N/A | S | **To Do** |
| **Revenue: "Bring Your Own Key" (BYOK) Model** | 200 | 1 | 70% | 0.5 | **280** | Pro | M | **To Do** |
| **Platform: Data Access for Biz** | 1000 | 3 | 50% | 6.0 | **250** | N/A | N/A | **To Do** |
| **Platform: Standard Business Email Addresses** | 10 | 1 | 100% | 0.25 | **40** | N/A | S | **To Do** |
| **BI: Platform-wide Hiring Funnel Analytics** | 10 | 3 | 100% | 3.0 | **10** | Pro | M | **To Do** |
| **BI: ML User/Company Clustering** | 10 | 3 | 80% | 4.0 | **6.0** | Pro | L | **To Do** |
| **Platform: Job Posting Multi-Context Awareness (Cities, Sources)** | 1 | 3 | 70% | 2.0 | **1.05** | Pro | M | **To Do** |