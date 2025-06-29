# Transparent Talent: Product Backlog & Roadmap v1.11

## Unrefined Ideas & Brainstorming
*This section is an inbox for raw ideas. During a "Session Summary" they will be refined, scored, and moved into the prioritized backlog below.*

---

## AI Model Column Definition
The "AI Model" column indicates the estimated complexity and nuance required from the AI assistant (me) to generate and debug the code for a given feature. This helps in task prioritization and resource allocation for development assistance.

*   **Flash:** The task is straightforward, involves well-defined patterns, and requires minimal nuanced understanding or complex multi-step reasoning from the AI assistant to generate the code and deployment instructions. Typically involves standard CRUD operations, simple UI components, or clear logical flows.
*   **Pro:** The task is complex, requires deeper contextual understanding, nuanced code generation, advanced debugging strategies, or involves significant architectural decisions from the AI assistant's perspective. This might include optimizing complex algorithms, designing sophisticated data structures, or tackling tricky cross-service integrations.
*   **N/A:** The task is primarily conceptual, strategic, or involves manual work that does not require the AI assistant's direct code generation assistance.

---

## Tier 1: Foundational Infrastructure (Highest Priority)
| Feature | Reach | Impact | Confidence | Effort (months) | RICE Score | AI Model | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Refactor: Separate `tracked_jobs.status` into `status` and `status_reason` columns (with ENUMs)** | 1 | 3 | 100% | 0.75 | **4.0** | Flash | **To Do** |
| **Backend: Scheduled Job URL Validity Checks & Status Updates** | 1 | 2 | 100% | 0.5 | **4.0** | Flash | **To Do** |
| **Backend: Define & Implement Comprehensive Data Lifecycle Management** | 1 | 3 | 90% | 1.0 | **2.7** | Pro | **To Do** |


## Tier 2: Core User Experience & Differentiation
| Feature | Reach | Impact | Confidence | Effort (months) | RICE Score | AI Model | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Feature: Define & Verify New User Account Flow** | 1000 | 3 | 100% | 0.5 | **6000** | Pro | **To Do** |
| **Feature: User Profile Onboarding & Data Input** | 1000 | 3 | 100% | 0.75 | **4000** | Flash | **To Do** |
| **UI/UX: User-Controlled Job Archiving & Expiration Notifications** | 1000 | 2 | 90% | 0.5 | **3600** | Flash | **To Do** |
| **UI/UX: 'Jobs for You' Module Restoration** | 1000 | 3 | 90% | 0.75 | **3600** | Flash | **To Do** |
| **UI: Transparent Relevance Scorecard** | 1000 | 3 | 100% | 1.0 | **3000** | Flash | **To Do** |
| **Feature: Automated Application Status Expiration & Notifications** | 1000 | 2 | 90% | 0.75 | **2400** | Flash | **To Do** |
| **Backend: Automated App Expiration** | 1000 | 1 | 100% | 0.25 | **4000** | Flash | **To Do** |
| **Feature: Bulk Job Submission (CSV/URLs)** | 500 | 3 | 90% | 1.0 | **1350** | Pro | **To Do** |
| **Feature: User Feedback Loop** | 1000 | 3 | 100% | 2.5 | **1200** | Pro | **To Do** |


## Tier 3: AI & System Intelligence (Mid-Term)
| Feature | Reach | Impact | Confidence | Effort (months) | RICE Score | AI Model | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Feature: Instant Analysis for Known Jobs**| 1000 | 2 | 100% | 0.5 | **4000** | Pro | **To Do** |
| **Automation: Tiered Job Analysis (Lightweight Pre-Screening + Detailed AI)** | 1000 | 3 | 90% | 1.5 | **1800** | Pro | **To Do** |
| **Automation: Full API Job Analysis**| 1000 | 3 | 90% | 2.0 | **1350** | Pro | **To Do** |
| **Feature: Proactive Anomaly Detection**| 1000 | 3 | 90% | 2.5 | **1080** | Pro | **To Do** |
| **Feature: Automated Job Sourcing (Email/Platform Integration)** | 1000 | 2 | 90% | 0.75 | **900** | Pro | **To Do** |
| **Documentation: Codify Industry Standards in Protocols** | 1 | 3 | 90% | 0.25 | **10.8** | N/A | **To Do** |
| **Feature: "User News" Sourcing** | 1000 | 2 | 90% | 2.0 | **900** | Pro | **To Do** |
| **AI: Multi-Model Verification**| 1000 | 2 | 90% | 2.0 | **900** | Pro | **To Do** |
| **Feature: Verifiable Outcomes**| 1000 | 3 | 80% | 3.0 | **800** | Pro | **To Do** |
| **Backend: Automated News Sourcing** | 1000 | 1 | 90% | 2.0 | **450** | Pro | **To Do** |
| **Backend: System-Wide Staleness Logic** | 1000 | 1 | 100% | 0.5 | **2000** | Pro | **To Do** |
| **Feature: "Transparent Rejection"**| 1000 | 3 | 80% | 2.0 | **1200** | Pro | **To Do** |
| **Feature: Browser Extension** | 500 | 2 | 80% | 3.0 | **267** | Pro | **To Do** |
| **AI: Full Data Leverage Mandate** | 1 | 3 | 90% | 1.0 | **2.7** | N/A | **To Do** |
| **AI: Automated Prompt QA System** | 1 | 3 | 80% | 3.0 | **0.8** | Pro | **To Do** |
| **Backend: DB-Driven AI Protocols** | 1 | 2 | 100% | 0.5 | **4.0** | Pro | **To Do** |

## Tier 4: Future Vision & Long-Term bets
| Feature | Reach | Impact | Confidence | Effort (months) | RICE Score | AI Model | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Infra: Background Jobs w/ Redis** | 1000 | 2 | 100% | 1.5 | **1333** | Pro | **To Do** |
| **Platform: Business Certification** | 5000 | 3 | 50% | 6.0 | **1250** | N/A | **To Do** |
| **AI: User & Job Clustering for Proactive Matching** | 1000 | 3 | 70% | 4.0 | **525** | Pro | **To Do** |
| **Business: Tier AI Features by Model Cost/Capability** | 200 | 1 | 80% | 0.5 | **320** | N/A | **To Do** |
| **Platform: System-Wide Analysis from User Submissions**| 1000 | 3 | 80% | 4.0 | **600** | Pro | **To Do** |
| **Platform: System-Wide Relevance Calc**| 1000 | 3 | 90% | 6.0 | **450** | Pro | **To Do** |
| **Revenue: "Bring Your Own Key" (BYOK) Model** | 200 | 1 | 70% | 0.5 | **280** | Pro | **To Do** |
| **Platform: Data Access for Biz** | 1000 | 3 | 50% | 6.0 | **250** | Pro | **To Do** |
| **BI: ML User/Company Clustering** | 10 | 3 | 80% | 4.0 | **6.0** | Pro | **To Do** |

---

## Completed Features & Bugfixes
*This section lists all completed features and bugfixes, categorized by the release version they were delivered in, in reverse chronological order.*

### [v0.13.0] - 2025-06-29 - Data Integrity & Analysis Hardening
| Feature/Bugfix | Original Tier | RICE Score |
| :--- | :--- | :--- |
| **Maintenance: Data Integrity Pass** | T1 | 8.0 |
| **Database: User-Specific Job Analysis & Versioning Schema** | T1 | N/A |
| **Backend: Corrected Job Analysis UPSERT & Retrieval** | T1 | N/A |
| **Data Cleanup: Mark Unreachable Tracked Jobs as 'Expired - Unreachable'** | T1 | N/A |

### [v0.12.0] - 2025-06-29
| Feature/Bugfix | Original Tier | RICE Score |
| :--- | :--- | :--- |
| **Bugfix: New Account Dashboard Error** | T2 | 12000 |
| **UI/UX: Context-Aware "Get Started" Button** | T2 | 4000 |
| **UI/UX: Header "Transparent Talent" Link to Homepage** | UI/UX Polish | N/A |

### [v0.11.0] - 2025-06-28
| Feature/Bugfix | Original Tier | RICE Score |
| :--- | :--- | :--- |
| **UI/UX: Job Tracker Pagination** | T2 | 4000 |

### [v0.10.0] - 2025-06-28
| Feature/Bugfix | Original Tier | RICE Score |
| :--- | :--- | :--- |
| **UI/UX: Auto-set 'Date Applied' on Status Change** | T2 | 8000 |

### [v0.9.0] - 2025-06-28
| Feature/Bugfix | Original Tier | RICE Score |
| :--- | :--- | :--- |
| **Deployment: Production Domain** | T2 | 4000 |

### [v0.8.0] - 2025-06-28
| Feature/Bugfix | Original Tier | RICE Score |
| :--- | :--- | :--- |
| **Architecture: Data Contract Standardization** | T1 | 24.0 |

### [v0.7.0] - 2025-06-28
| Feature/Bugfix | Original Tier | RICE Score |
| :--- | :--- | :--- |
| **UI: Tabular Job Tracker** | T2 | 4000 |

### [v0.6.0] - 2025-06-28
| Feature/Bugfix | Original Tier | RICE Score |
| :--- | :--- | :--- |
| **Feature: User Job Submission** | T2 | 6000 |

### [v0.5.0] - 2025-06-28
| Feature/Bugfix | Original Tier | RICE Score |
| :--- | :--- | :--- |
| **Feature: Logged Out Experience** | T2 | 8000 |

### [v0.4.0] - 2025-06-28
| Feature/Bugfix | Original Tier | RICE Score |
| :--- | :--- | :--- |
| **Bugfix: Resolve Production Authentication** | T1 | 12000 |

### [v0.3.0] - 2025-06-27
| Feature/Bugfix | Original Tier | RICE Score |
| :--- | :--- | :--- |
| **Security: Implement User Authentication** | T1 | 6000 |

### [v0.2.0] - 2025-06-26
| Feature/Bugfix | Original Tier | RICE Score |
| :--- | :--- | :--- |
| **Architecture: Monorepo Setup** | T1 | 12.0 |
| **Deployment: Deploy Frontend** | T1 | 12000 |

### [v0.1.0] - 2025-06-26
| Feature/Bugfix | Original Tier | RICE Score |
| :--- | :--- | :--- |
| **Initial Backend API (v1)** | T1 | N/A |
| **Job Tracker Functionality** | T1 | N/A |
| **Initial Frontend Dashboard (v1)** | T1 | N/A |
| **Comprehensive Data Migration** | T1 | N/A |
| **Upgraded Database** | T1 | N/A |
| **Enhanced Business Logic** | T1 | N/A |